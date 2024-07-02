"""Defines the public API endpoints to work/report on montesinos tangles."""

from fastapi import Depends, APIRouter, HTTPException
from . import orm, job
from ..internal import job_queue
from typing import Annotated, List
from dacite import from_dict

router = APIRouter(
    prefix="/montesinos",
    tags=["Montesinos"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


################################################################################
# Helper Functions
################################################################################


async def _retrieve_montesinos_tangles(
    start_id: str = None,
    page_idx: int = 0,
    page_size: int = 100,
):
    if page_size <= 0:
        raise HTTPException(status_code=404, detail="Page size must be positive")
    tangle_col = orm.get_montesinos_collection()
    if start_id is None:
        tangle_page = (
            await tangle_col.find({"isMontesinos": True})
            .sort([("crossing_num", 1)])
            .limit(page_size)
            .to_list(page_size)
        )
        for i in range(page_idx):
            tangle_page = (
                await tangle_col.find(
                    {"_id": {"$gt": tangle_page[-1]["_id"]}, "isMontesinos": True}
                )
                .sort([("crossing_num", 1)])
                .limit(page_size)
                .to_list(page_size)
            )
    else:
        tangle_page = (
            await tangle_col.find({"_id": {"$gt": start_id}, "isMontesinos": True})
            .sort([("crossing_num", 1)])
            .limit(page_size)
            .to_list(page_size)
        )
    return [
        from_dict(data_class=orm.MontesinosTangleDB, data=tang) for tang in tangle_page
    ]


@router.get("/tangles", response_model=List[orm.MontesinosTangleDB])
async def retrieve_montesinos_tangles(
    tangle_list: Annotated[
        List[orm.MontesinosTangleDB], Depends(_retrieve_montesinos_tangles)
    ]
):
    """Return the next montesinos job.

    Parameters
    ----------
    tangle_list : Annotated[mj.montesinos_Job, Depends
        The next montesinos Job.

    Returns
    -------
    montesinos_Job
        The next montesinos Job.
    """
    return tangle_list


@router.get("/queue/stats")
async def retrieve_generic_job_queue_stats() -> dict:
    """Return job queue statistics for generic jobs.

    Returns
    -------
    dict
        Job queue statistics for generic jobs. Broken into:
        - Total
        - New
        - Pending
        - Complete
    """
    return await job_queue.get_job_statistics(job.MontesinosJob)
