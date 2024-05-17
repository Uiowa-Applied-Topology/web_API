"""_summary_

Raises
------
HTTPException
    _description_
HTTPException
    _description_
HTTPException
    _description_
"""

from ..interfaces.job import generation_job, generation_job_results, Job_State_Enum
from ..internal.security import User
from . import config

from fastapi import HTTPException
from fastapi import APIRouter

from typing import Dict, Type, List
from datetime import datetime, timezone
from threading import Semaphore
import asyncio


router = APIRouter(
    prefix="/job_queue",
    tags=["Jobs"],
    responses={404: {"description": "Not found"}},
)


_job_queue: Dict[str, generation_job] = dict()

semaphore: Semaphore = Semaphore()


async def mark_job_complete(results: generation_job_results, current_user: User):
    """_summary_

    Parameters
    ----------
    results : generation_job_results
        _description_
    current_user : User
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    global _job_queue
    semaphore.acquire()
    if (
        results.id in _job_queue
        and _job_queue[results.id].cur_state == Job_State_Enum.pending
        and _job_queue[results.id].client_id == current_user.username
    ):
        job: generation_job = _job_queue[results.id]
        job.update_results(results)
        job.cur_state = Job_State_Enum.complete
        semaphore.release()
        return
    semaphore.release()
    raise HTTPException(
        status_code=404, detail="Job not in queue or Job not in pending."
    )


async def get_next_job(
    job_type: Type[generation_job], current_user: User
) -> generation_job:
    """_summary_

    Parameters
    ----------
    job_type : Type[generation_job]
        _description_
    current_user : User
        _description_

    Returns
    -------
    generation_job
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    global _job_queue
    semaphore.acquire()
    items = [
        i
        for i in _job_queue
        if isinstance(_job_queue[i], job_type)
        and _job_queue[i].cur_state == Job_State_Enum.new
    ]
    if len(items) > 0:
        _job_queue[items[0]].cur_state = Job_State_Enum.pending
        _job_queue[items[0]].client_id = current_user.username
        semaphore.release()
        return _job_queue[items[0]]
    semaphore.release()
    raise HTTPException(status_code=404, detail="Job not found.")


def _check_time_delta(then: datetime) -> bool:
    """_summary_

    Parameters
    ----------
    then : datetime
        _description_

    Returns
    -------
    bool
        _description_
    """
    now = datetime.now(timezone.utc)
    diff = now - then
    if diff.total_seconds() >= config.config["job-queue"]["clocks"]["stale"]:
        return True
    return False


async def _clean_stale_jobs():
    """_summary_"""
    global _job_queue
    semaphore.acquire()
    items: List[generation_job] = [
        _job_queue[i]
        for i in _job_queue
        if (_check_time_delta(_job_queue[i].timestamp))
        and (_job_queue[i].cur_state != Job_State_Enum.complete)
    ]
    for item in items:
        item.cur_state = Job_State_Enum.new
    semaphore.release()


async def _clean_complete_jobs():
    global _job_queue
    semaphore.acquire()
    items: List[generation_job] = [
        _job_queue[i]
        for i in _job_queue
        if _job_queue[i].cur_state == Job_State_Enum.complete
    ]
    for item in items:
        await item.store()
        del _job_queue[item.id]
    semaphore.release()


async def enqueue_job(job: generation_job):
    """_summary_

    Parameters
    ----------
    job : generation_job
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    global _job_queue
    semaphore.acquire()
    if job.id not in _job_queue:
        _job_queue[job.id] = job
        semaphore.release()
        return
    semaphore.release()
    raise HTTPException(status_code=500, detail="job enqueue error.")


def get_count_new(job_type: Type[generation_job]):
    """_summary_

    Parameters
    ----------
    job_type : Type[generation_job]
        _description_

    Returns
    -------
    _type_
        _description_
    """
    return len(
        [
            i
            for i in _job_queue
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == Job_State_Enum.new
        ]
    )


def get_count_complete(job_type: Type[generation_job]):
    """_summary_

    Parameters
    ----------
    job_type : Type[generation_job]
        _description_

    Returns
    -------
    _type_
        _description_
    """
    return len(
        [
            i
            for i in _job_queue
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == Job_State_Enum.complete
        ]
    )


def get_count_pending(job_type: Type[generation_job]):
    """_summary_

    Parameters
    ----------
    job_type : Type[generation_job]
        _description_

    Returns
    -------
    _type_
        _description_
    """
    return len(
        [
            i
            for i in _job_queue
            if isinstance(_job_queue[i], job_type)
            and _job_queue[i].cur_state == Job_State_Enum.pending
        ]
    )


def get_job_statistics(job_type: Type[generation_job]):
    """_summary_

    Parameters
    ----------
    job_type : Type[generation_job]
        _description_

    Returns
    -------
    _type_
        _description_
    """
    return {
        "queue_length": len(_job_queue),
        "new": get_count_new(job_type),
        "pending": get_count_pending(job_type),
        "complete": get_count_complete(job_type),
    }


@router.get("/stats")
async def retrieve_job_statistics():
    """_summary_

    Returns
    -------
    _type_
        _description_
    """
    return get_job_statistics(generation_job)


async def task_clean_stale_jobs():
    """_summary_"""
    while True:
        await asyncio.sleep(config.config["job-queue"]["clocks"]["stale"])
        await _clean_stale_jobs()


async def task_clean_complete_jobs():
    """_summary_"""
    while True:
        await asyncio.sleep(config.config["job-queue"]["clocks"]["complete"])
        await _clean_complete_jobs()
