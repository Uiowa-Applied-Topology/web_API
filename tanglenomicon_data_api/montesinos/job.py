"""The Job interface.

The class describes the common interface all job types implement.

"""

from datetime import datetime, timezone
from ..interfaces.job import generation_job, generation_job_results
from ..interfaces.job_state import Job_State_Enum
from ..internal import job_queue, config
from . import orm
from ..rational import orm as rat_orm
from threading import Semaphore
from typing import List
from dacite import from_dict
from dataclasses import asdict
import time
import math
import copy
import uuid

OPEN_STEN_FILTER = {
    "$and": [
        {"state": {"$ne": orm.DBjobState_Enum.complete}},
        {"state": {"$ne": orm.DBjobState_Enum.no_headroom}},
    ]
}
STARTED_STEN_FILTER = {
    "$and": [
        {"state": {"$ne": orm.DBjobState_Enum.complete}},
        {"state": {"$ne": orm.DBjobState_Enum.new}},
    ]
}


semaphore: Semaphore = Semaphore()


def _move_head(sten: orm.mont_stencil_db) -> orm.HeadState_Enum:
    overflow = True
    for i, sten_entry in enumerate(sten.stencil_array):
        if overflow:
            sten.head[i] += 1
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
            < sten.head[i]
        ):
            sten.head[i] = 0
            overflow = True
        else:
            break
    if overflow:
        for i, sten_entry in enumerate(sten.stencil_array):
            sten.head[i] = sten_entry
        return orm.HeadState_Enum.no_headroom
    return orm.HeadState_Enum.headroom


class Montesinos_Job_Results(generation_job_results):
    mont_list: List[str]
    crossing_num: int = None


class Montesinos_Job(generation_job):
    rat_lists: List[List[str]]
    _results: Montesinos_Job_Results = None

    async def store(self):
        global semaphore
        store = orm._get_storage_collection()
        stencil_col = orm._get_stencil_collection()
        tangles_2_store = [
            {"_id": tang, "crossing_num": self._results.crossing_num}
            for tang in self._results.mont_list
        ]
        semaphore.acquire()
        await store.insert_many(tangles_2_store)
        sten = from_dict(
            data_class=orm.mont_stencil_db,
            data=(await stencil_col.find_one({"open_jobs.job_id": self.id})),
        )
        i = [j.job_id for j in sten.open_jobs].index(self.id)
        del sten.open_jobs[i]
        if sten.state == orm.DBjobState_Enum.no_headroom and len(sten.open_jobs)==0:
            sten.state = orm.DBjobState_Enum.complete
        await stencil_col.replace_one({"_id": sten._id}, asdict(sten))
        semaphore.release()

    def update_results(self, res: Montesinos_Job_Results):
        self._results = res


async def _build_job(
    crossing_numbers: List[int], pages: List[int], id: str = None
) -> str:
    store_rat = orm._get_rational_collection()
    if not id:
        id = str(uuid.uuid4())
    job = Montesinos_Job(
        cur_state=Job_State_Enum.new,
        timestamp=datetime.now(timezone.utc),
        id=id,
        rat_lists=list(),
    )
    for cn, page in zip(crossing_numbers, pages):
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
        async for response in store_rat.aggregate(pipeline):
            for rat_tang in response["data"]:
                rat_tang = from_dict(data_class=rat_orm.rational_tang_db, data=rat_tang)
                lis.append(rat_tang._id)
                ...
            ...

        job.rat_lists.append(lis)
    await job_queue.enqueue_job(job)
    return job.id


async def get_jobs(count: int):
    global semaphore
    stencil_col = orm._get_stencil_collection()
    semaphore.acquire()
    sten = from_dict(
        data_class=orm.mont_stencil_db,
        data=(await stencil_col.find_one(OPEN_STEN_FILTER)),
    )
    sten.state = orm.DBjobState_Enum.started
    while count > 0 and sten:
        job_id = await _build_job(sten.stencil_array, sten.head)
        sten.open_jobs.append({"job_id": job_id, "cursor": copy.deepcopy(sten.head)})
        count -= 1
        if _move_head(sten) == orm.HeadState_Enum.no_headroom:
            sten.state = orm.DBjobState_Enum.no_headroom
            stencil_col.replace_one({"_id": sten._id}, asdict(sten))
            sten = from_dict(
                data_class=orm.mont_stencil_db,
                data=(await stencil_col.find_one(OPEN_STEN_FILTER)),
            )
            sten.state = orm.DBjobState_Enum.started
    stencil_col.replace_one({"_id": sten._id}, asdict(sten))
    semaphore.release()


async def startup_jobs():
    global semaphore
    store_sten = orm._get_stencil_collection()
    semaphore.acquire()

    async for sten in store_sten.find(STARTED_STEN_FILTER):
        sten = from_dict(data_class=orm.mont_stencil_db, data=sten)

        for open_item in sten.open_jobs:
            await _build_job(sten.stencil_array, open_item.cursor, id=open_item.job_id)
            ...
    semaphore.release()
    nmjc = job_queue.get_job_statistics(Montesinos_Job)["new"]
    if nmjc < config.config["job-queue"]["min-new-count"]:
        await get_jobs(config.config["job-queue"]["min-new-count"] - nmjc)
