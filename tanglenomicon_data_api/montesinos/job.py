"""An implementation of the job interface for Montesinos jobs."""

from datetime import datetime, timezone
from ..interfaces.job import GenerationJob, GenerationJobResults, JobStateEnum
from ..internal import job_queue, config
from . import orm
from ..rational import orm as rat_orm
from threading import Semaphore
from typing import List
from dacite import from_dict
from dataclasses import asdict
import math
import copy
import uuid

OPEN_STEN_FILTER = {
    "$and": [
        {"state": {"$ne": orm.StencilStateEnum.complete}},
        {"state": {"$ne": orm.StencilStateEnum.no_headroom}},
    ]
}
STARTED_STEN_FILTER = {
    "$and": [
        {"state": {"$ne": orm.StencilStateEnum.complete}},
        {"state": {"$ne": orm.StencilStateEnum.new}},
    ]
}


semaphore: Semaphore = Semaphore()


def _move_head(stencildb: orm.StencilDB) -> orm.StencilHeadStateEnum:
    """Move the head of the Stencil forward by a page.

    Parameters
    ----------
    sten : orm.mont_stencil_db
        A stencil from the DB.

    Returns
    -------
    orm.HeadState_Enum
        Returns the current state of the stencil head. Headroom if not the last
        page was just completed or No headroom otherwise.
    """
    overflow = True
    for i, sten_entry in enumerate(stencildb.stencil_array):
        if overflow:
            stencildb.head[i] += 1
            overflow = False
        if (
            max(
                0,
                (
                    sten_entry
                    - 2
                    - config.config["tangle-classes"]["montesinos"]["page-exp"]
                ),
            )
            < stencildb.head[i]
        ):
            stencildb.head[i] = 0
            overflow = True
        else:
            break
    if overflow:
        for i, sten_entry in enumerate(stencildb.stencil_array):
            stencildb.head[i] = sten_entry
        return orm.StencilHeadStateEnum.no_headroom
    return orm.StencilHeadStateEnum.headroom


async def _build_job(stencil: List[int], pages: List[int], job_id: str = None) -> str:
    """Build and enqueue a new Montesinos job.

    Parameters
    ----------
    stencil : List[int]
        The stencil to fill in.
    pages : List[int]
        The rational pages to retrieve.
    job_id : str, optional
        The id to use for the job, by default None

    Returns
    -------
    str
        The id for the built and enqueued job.
    """
    rational_col = orm._get_rational_collection()
    if not job_id:
        job_id = str(uuid.uuid4())
    job = MontesinosJob(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        rat_lists=list(),
    )
    for cn, page in zip(stencil, pages):
        lis = []
        pipeline = [
            {"$match": {"$and": [{"crossing_num": cn}, {"in_unit_interval": True}]}},
            {
                "$facet": {
                    "metadata": [{"$count": "totalCount"}],
                    "data": [
                        {
                            "$skip": page
                            * math.pow(
                                2,
                                config.config["tangle-classes"]["montesinos"][
                                    "page-exp"
                                ],
                            )
                        },
                        {
                            "$limit": math.pow(
                                2,
                                config.config["tangle-classes"]["montesinos"][
                                    "page-exp"
                                ],
                            )
                        },
                    ],
                }
            },
        ]
        async for response in rational_col.aggregate(pipeline):
            for rat_tang in response["data"]:
                rat_tang = from_dict(data_class=rat_orm.RationalTangDB, data=rat_tang)
                lis.append(rat_tang._id)
                ...
            ...

        job.rat_lists.append(lis)
    await job_queue.enqueue_job(job)
    # @@@IMPROVEMENT: this need error handling.
    return job.job_id


class MontesinosJobResults(GenerationJobResults):
    """The implementation of job results for Montesinos jobs."""

    mont_list: List[str]
    crossing_num: int = None


class MontesinosJob(GenerationJob):
    """The implementation of job for Montesinos tangles."""

    rat_lists: List[List[str]]
    _results: MontesinosJobResults = None

    async def store(self):
        """Store the current job into the Montesinos tangle collection."""
        global semaphore
        montesinos_col = orm._get_storage_collection()
        stencil_col = orm._get_stencil_collection()
        tangles_2_store = [
            {"_id": tang, "crossing_num": self._results.crossing_num}
            for tang in self._results.mont_list
        ]
        semaphore.acquire()
        await montesinos_col.insert_many(tangles_2_store)
        stencildb = from_dict(
            data_class=orm.StencilDB,
            data=(await stencil_col.find_one({"open_jobs.job_id": self.job_id})),
        )
        i = [j.job_id for j in stencildb.open_jobs].index(self.job_id)
        del stencildb.open_jobs[i]
        if (
            stencildb.state == orm.StencilStateEnum.no_headroom
            and len(stencildb.open_jobs) == 0
        ):
            stencildb.state = orm.StencilStateEnum.complete
        await stencil_col.replace_one({"_id": stencildb._id}, asdict(stencildb))
        semaphore.release()

    def update_results(self, res: MontesinosJobResults):
        """Update the job with the reported results."""
        self._results = res


async def get_jobs(count: int = 1):
    """Get and build a specified number of jobs.

    Parameters
    ----------
    count : int, optional
        The number of jobs to get and build, by default 1
    """
    global semaphore
    stencil_col = orm._get_stencil_collection()
    semaphore.acquire()
    stencildb = from_dict(
        data_class=orm.StencilDB,
        data=(await stencil_col.find_one(OPEN_STEN_FILTER)),
    )
    stencildb.state = orm.StencilStateEnum.started
    while count > 0 and stencildb:
        job_id = await _build_job(stencildb.stencil_array, stencildb.head)
        stencildb.open_jobs.append(
            {"job_id": job_id, "cursor": copy.deepcopy(stencildb.head)}
        )
        count -= 1
        if _move_head(stencildb) == orm.StencilHeadStateEnum.no_headroom:
            stencildb.state = orm.StencilStateEnum.no_headroom
            stencil_col.replace_one({"_id": stencildb._id}, asdict(stencildb))
            stencildb = from_dict(
                data_class=orm.StencilDB,
                data=(await stencil_col.find_one(OPEN_STEN_FILTER)),
            )
            stencildb.state = orm.StencilStateEnum.started
    stencil_col.replace_one({"_id": stencildb._id}, asdict(stencildb))
    semaphore.release()


async def startup_task():
    """Task to run at startup to initialize Montesinos jobs."""
    global semaphore
    stencil_col = orm._get_stencil_collection()
    semaphore.acquire()

    async for stencildb in stencil_col.find(STARTED_STEN_FILTER):
        stencildb = from_dict(data_class=orm.StencilDB, data=stencildb)

        for open_item in stencildb.open_jobs:
            await _build_job(
                stencildb.stencil_array, open_item.cursor, job_id=open_item.job_id
            )
            ...
    semaphore.release()
    new_mont_j_cnt = job_queue.get_job_statistics(MontesinosJob)["new"]
    if new_mont_j_cnt < config.config["job-queue"]["min-new-count"]:
        await get_jobs(config.config["job-queue"]["min-new-count"] - new_mont_j_cnt)
