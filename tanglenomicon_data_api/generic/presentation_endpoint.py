"""Defines the public API endpoints to work/report on generic tangles."""

from fastapi import Depends, APIRouter, HTTPException
from . import orm
from ..internal import job_queue
from typing import Annotated, List
from dacite import from_dict

router = APIRouter(
    tags=["Generic"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


################################################################################
# Helper Functions
################################################################################


async def _retrieve_generic_tangles(
    page_idx: int = 0,
    page_size: int = 100,
):
    tangle_col = orm.get_generic_collection()
    pipeline = [
        {"$match": {}},
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
            from_dict(data_class=orm.GenericTangDB, data=rat_tang)
            for rat_tang in response["data"]
        ]


async def _retrieve_generic_tangle(id: str):
    tangle_col = orm.get_generic_collection()
    tang = await tangle_col.find_one({"_id": str(id)})
    if not tang:
        raise HTTPException(status_code=404, detail="Tangle not found.")
    return tang


@router.get("/tangles", response_model=List[orm.GenericTangDB])
async def retrieve_generic_tangles(
    tangle_list: Annotated[List[orm.GenericTangDB], Depends(_retrieve_generic_tangles)]
):
    """Return the next generic job.

    Parameters
    ----------
    tangle_list : Annotated[mj.generic_Job, Depends
        The next generic Job.

    Returns
    -------
    generic_Job
        The next generic Job.
    """
    return tangle_list


@router.get("/tangle")
async def retrieve_generic_tangle(
    tangle: Annotated[List[orm.GenericTangDB], Depends(_retrieve_generic_tangle)]
):
    """Return the next generic job.

    Parameters
    ----------
    tangle : Dict
        The next generic Job.

    Returns
    -------
    generic_Job
        The next generic Job.
    """
    return tangle


@router.get("/queue_stats")
async def retrieve_job_statistics(
    stats: Annotated[dict, Depends(job_queue.get_job_statistics)]
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
