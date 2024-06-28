"""Defines the public API endpoints to work/report on rational tangles."""

from fastapi import Depends, APIRouter
from . import orm
from typing import Annotated, List
from dacite import from_dict

router = APIRouter(
    prefix="/rational",
    tags=["Rational"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


################################################################################
# Helper Functions
################################################################################


async def _retrieve_rational_tangles(
    page_idx: int = 0,
    page_size: int = 100,
):
    tangle_col = orm.get_rational_collection()
    pipeline = [
        {"$match": {"isRational": True}},
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
            from_dict(data_class=orm.RationalTangDB, data=rat_tang)
            for rat_tang in response["data"]
        ]


@router.get("/tangles", response_model=List[orm.RationalTangDB])
async def retrieve_rational_tangles(
    tangle_list: Annotated[
        List[orm.RationalTangDB], Depends(_retrieve_rational_tangles)
    ]
):
    """Return the next rational job.

    Parameters
    ----------
    tangle_list : Annotated[mj.rational_Job, Depends
        The next rational Job.

    Returns
    -------
    rational_Job
        The next rational Job.
    """
    return tangle_list
