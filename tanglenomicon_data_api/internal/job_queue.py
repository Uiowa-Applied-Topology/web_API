"""Job Queue handles the tangle generation job "queue"."""

from ..interfaces.job import GenerationJob, GenerationJobResults, JobStateEnum
from ..internal.security import User
from . import config_store

from typing import Annotated
from fastapi import Depends, APIRouter

from typing import Dict, Type, List
from datetime import datetime, timezone
from threading import Semaphore
import asyncio
import logging

logger = logging.getLogger("uvicorn")


router = APIRouter(
    prefix="/job_queue",
    tags=["Jobs"],
    responses={404: {"description": "Not found"}},
)

_job_queue: Dict[str, GenerationJob] = dict()

jq_semaphore: Semaphore = Semaphore()
task_semaphore: Semaphore = Semaphore()


async def aiterjq():
    """sdfsdfsdf."""
    for i in _job_queue:
        yield i


async def _get_count(job_type: Type[GenerationJob] = GenerationJob) -> int:
    """Get the number of jobs from the queue.

    Parameters
    ----------
    job_type : Type[generation_job], optional
        The type of job to find, by default GenerationJob.

    Returns
    -------
    int
        The count.
    """
    return len(
        [i async for i in aiter(aiterjq()) if isinstance(_job_queue[i], job_type)]
    )


async def _get_count_new(job_type: Type[GenerationJob] = GenerationJob) -> int:
    """Get the number of jobs from the queue in the 'new' state.

    Parameters
    ----------
    job_type : Type[generation_job], optional
        The type of job to find, by default GenerationJob.

    Returns
    -------
    int
        The count.
    """
    return len(
        [
            i
            async for i in aiter(aiterjq())
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == JobStateEnum.new
        ]
    )


async def _get_count_complete(job_type: Type[GenerationJob] = GenerationJob) -> int:
    """Get the number of jobs from the queue in the 'complete' state.

    Parameters
    ----------
    job_type : Type[generation_job], optional
        The type of job to find, by default GenerationJob.

    Returns
    -------
    int
        The count.
    """
    return len(
        [
            i
            async for i in aiter(aiterjq())
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == JobStateEnum.complete
        ]
    )


async def _get_count_pending(job_type: Type[GenerationJob] = GenerationJob) -> int:
    """Get the number of jobs from the queue in the 'pending' state.

    Parameters
    ----------
    job_type : Type[generation_job], optional
        The type of job to find, by default GenerationJob.

    Returns
    -------
    int
        The count.
    """
    return len(
        [
            i
            async for i in aiter(aiterjq())
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == JobStateEnum.pending
        ]
    )


def _is_above_time_delta(then: datetime) -> bool:
    """Check if the time between now and then is below or above threshold.

    Parameters
    ----------
    then : datetime
        The timestamp from "then".

    Returns
    -------
    bool
        ``True`` if above threshold ``False`` otherwise.
    """
    now = datetime.now(timezone.utc)
    diff = now - then
    if diff.total_seconds() >= config_store.cfg_dict["job-queue"]["clocks"]["stale"]:
        return True
    return False


async def _clean_stale_jobs():
    """Clean job queue of stale jobs."""
    global _job_queue
    task_semaphore.acquire()
    jq_semaphore.acquire()
    items: List[GenerationJob] = [
        _job_queue[i]
        async for i in aiter(aiterjq())
        if (_is_above_time_delta(_job_queue[i].timestamp))
        and (_job_queue[i].cur_state != JobStateEnum.complete)
    ]
    jq_semaphore.release()
    for item in items:
        item.cur_state = JobStateEnum.new
    task_semaphore.release()


async def _clean_complete_jobs():
    """Store complete jobs into DB."""
    global _job_queue
    task_semaphore.acquire()
    jq_semaphore.acquire()
    items: List[GenerationJob] = [
        _job_queue[i]
        async for i in aiter(aiterjq())
        if _job_queue[i].cur_state == JobStateEnum.complete
    ]
    jq_semaphore.release()
    for item in items:
        try:
            await item.store()
            del _job_queue[item.job_id]
            logger.debug(f"Stored {item.job_id}")
        except Exception as e:
            logger.error(f"Exception while processing job {item.job_id}: {e}")
            pass
    task_semaphore.release()


async def mark_job_complete(results: GenerationJobResults, current_user: User) -> bool:
    """Mark job in queue as complete.

    Parameters
    ----------
    results : GenerationJobResults
        The reported results from the user.
    current_user : User
        The user submitting the results.

    Returns
    -------
    bool
        ``True`` if successfully marked complete ``False`` otherwise.
    """
    global _job_queue
    marked = False
    if (
        results.job_id in _job_queue
        and _job_queue[results.job_id].cur_state == JobStateEnum.pending
        and _job_queue[results.job_id].client_id == current_user.username
    ):
        job: GenerationJob = _job_queue[results.job_id]
        job.update_results(results)
        job.cur_state = JobStateEnum.complete
        marked = True
    # @@@IMPROVEMENT: should add logging here.
    return marked


async def get_next_job(
    job_type: Type[GenerationJob], current_user: User
) -> GenerationJob | None:
    """Get the next job to complete from the job queue.

    Parameters
    ----------
    job_type : Type[generation_job]
        The type of job to find in the queue.
    current_user : User
        The user requesting the job.

    Returns
    -------
    GenerationJob | None
        The job to feed the user or None if none exist.
    """
    global _job_queue
    job = None
    jq_semaphore.acquire()
    items = [
        i
        async for i in aiter(aiterjq())
        if isinstance(_job_queue[i], job_type)
        and _job_queue[i].cur_state == JobStateEnum.new
    ]
    if len(items) > 0:
        _job_queue[items[0]].cur_state = JobStateEnum.pending
        _job_queue[items[0]].client_id = current_user.username
        job = _job_queue[items[0]]
    jq_semaphore.release()
    return job


async def enqueue_job(job: GenerationJob) -> bool:
    """Add a job to the queue.

    Parameters
    ----------
    job : generation_job
        The job to add to the queue.

    Returns
    -------
    bool
        ``True`` if job is enqueued ``False`` otherwise.
    """
    global _job_queue
    enqueued = False
    jq_semaphore.acquire()
    if job.job_id not in _job_queue:
        _job_queue[job.job_id] = job
        enqueued = True
    jq_semaphore.release()
    return enqueued


async def get_job_statistics(job_type: Type[GenerationJob] = GenerationJob) -> dict:
    """Get all job statistics.

    Parameters
    ----------
    job_type : Type[GenerationJob], optional
        The type of job to find, by default GenerationJob.

    Returns
    -------
    dict
        The queue statistics for the type.
    """
    return {
        "queue_length": await _get_count(job_type),
        "new": await _get_count_new(job_type),
        "pending": await _get_count_pending(job_type),
        "complete": await _get_count_complete(job_type),
    }


async def task_clean_stale_jobs():
    """Task that periodically cleans stale jobs from the queue."""
    while True:
        await asyncio.sleep(config_store.cfg_dict["job-queue"]["clocks"]["stale"])
        await _clean_stale_jobs()


async def task_clean_complete_jobs():
    """Task that periodically stores complete jobs in the queue."""
    while True:
        await asyncio.sleep(config_store.cfg_dict["job-queue"]["clocks"]["complete"])
        await _clean_complete_jobs()


@router.get("/stats")
async def retrieve_job_statistics(
    stats: Annotated[dict, Depends(get_job_statistics)]
) -> dict:
    """Request for queue statistics.

    Parameters
    ----------
    stats : Annotated[dict, Depends
        The statistics.

    Returns
    -------
    dict
        The statistics.
    """
    return stats
