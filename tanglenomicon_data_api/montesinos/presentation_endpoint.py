"""Defines the public API endpoints to work/report on montesinos tangles."""

from fastapi import Depends, APIRouter
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
    page_idx: int = 0,
    page_size: int = 100,
):
    tangle_col = orm.get_montesinos_collection()
    pipeline = [
        {"$match": {"isMontesinos": True}},
        {
            "$facet": {
                "metadata": [{"$count": "totalCount"}],
                "data": [
                    {"$skip": int(page_idx * page_size)},
                    {"$limit": int(page_size)},
                ],
            }
        },
    ]
    async for response in tangle_col.aggregate(pipeline):
        return [
            from_dict(data_class=orm.MontesinosTangleDB, data=rat_tang)
            for rat_tang in response["data"]
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
