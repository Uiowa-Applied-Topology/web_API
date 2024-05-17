"""_summary_
"""

from typing import List
from enum import Enum
from dataclasses import dataclass
from bson import ObjectId
from ..internal import db_connector as dbc

STENCIL_COL_NAME = "mont_stencils"
STORAGE_COL_NAME = "montesinos"
RATIONAL_COL_NAME = "rational"


def _get_stencil_collection():
    """_summary_

    Returns
    -------
    _type_
        _description_
    """
    return dbc.db[STENCIL_COL_NAME]


def _get_storage_collection():
    """_summary_

    Returns
    -------
    _type_
        _description_
    """
    return dbc.db[STORAGE_COL_NAME]


def _get_rational_collection():
    """_summary_

    Returns
    -------
    _type_
        _description_
    """
    return dbc.db[RATIONAL_COL_NAME]


class HeadState_Enum(str, Enum):
    """_summary_

    Parameters
    ----------
    str : _type_
        _description_
    Enum : _type_
        _description_
    """

    headroom = "headroom"
    no_headroom = "no_headroom"


class DBjobState_Enum(int, Enum):
    """_summary_

    Parameters
    ----------
    int : _type_
        _description_
    Enum : _type_
        _description_
    """

    new = 0
    started = 1
    no_headroom = 2
    complete = 3


@dataclass
class mont_stencil_job_db:
    """_summary_"""

    job_id: str
    cursor: List[int]


@dataclass
class mont_stencil_db:
    """_summary_"""

    _id: ObjectId
    stencil_array: List[int]
    str_rep: str
    crossing_num: int
    head: List[int]
    state: int
    open_jobs: List[mont_stencil_job_db]
