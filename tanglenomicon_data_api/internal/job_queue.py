from ..interfaces.job import generation_job, generation_job_results
from ..interfaces.job_state import Job_State_Enum
from ..internal.security import User
from . import config

from fastapi import HTTPException
from typing import Dict, Type, List
from datetime import datetime, timedelta
from threading import Semaphore
import time

_job_queue: Dict[str, generation_job] = dict()

semaphore: Semaphore = Semaphore()


async def mark_job_complete(results: generation_job_results, current_user: User):
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
    now = datetime.now()
    diff = now - then
    if diff >= config.config["clocks"]["stale"]:
        return True
    return False


def clean_stale_jobs():
    global _job_queue
    semaphore.acquire()
    items: List[generation_job] = [
        i
        for i in _job_queue
        if (_check_time_delta(_job_queue[i].timestamp))
        and (_job_queue[i].cur_state != Job_State_Enum.complete)
    ]
    for item in items:
        item.cur_state = Job_State_Enum.new
    semaphore.release()


def clean_complete_jobs():
    global _job_queue
    semaphore.acquire()
    items: List[generation_job] = [
        i for i in _job_queue if _job_queue[i].cur_state == Job_State_Enum.complete
    ]
    for item in items:
        item.store()
        del _job_queue[item.id]
    semaphore.release()


async def enqueue_job(job: generation_job):
    global _job_queue
    semaphore.acquire()
    if job.id not in _job_queue:
        _job_queue[job.id] = job
        semaphore.release()
        return
    semaphore.release()
    raise HTTPException(status_code=500, detail="job enqueue error.")
