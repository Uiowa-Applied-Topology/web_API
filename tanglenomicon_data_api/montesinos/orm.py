"""ORM for the Montesinos submodule."""

from typing import List
from enum import Enum
from dataclasses import dataclass
from bson import ObjectId
from ..internal import db_connector as dbc
from motor.motor_asyncio import AsyncIOMotorCollection


STENCIL_COL_NAME = "mont_stencils"
STORAGE_COL_NAME = "montesinos"
RATIONAL_COL_NAME = "rational"


def _get_stencil_collection() -> AsyncIOMotorCollection:
    """Return the mongodb collection containing the Montesinos stencils.

    Returns
    -------
    AsyncIOMotorCollection
        The Montesinos stencils collection.
    """
    return dbc.db[STENCIL_COL_NAME]


def _get_storage_collection() -> AsyncIOMotorCollection:
    """Return the mongodb collection containing the Montesinos tangles.

    Returns
    -------
    AsyncIOMotorCollection
        The Montesinos tangles collection.
    """
    return dbc.db[STORAGE_COL_NAME]


def _get_rational_collection() -> AsyncIOMotorCollection:
    """Return the mongodb collection containing the rational tangles.

    Returns
    -------
    AsyncIOMotorCollection
        The rational tangles collection.
    """
    return dbc.db[RATIONAL_COL_NAME]


class StencilHeadStateEnum(str, Enum):
    """Enum describing the states of the Head pointer for stencils."""

    headroom = "headroom"
    no_headroom = "no_headroom"


class StencilStateEnum(int, Enum):
    """Enum describing the states of a stencil."""

    new = 0
    started = 1
    no_headroom = 2
    complete = 3


@dataclass
class StencilJobDB:
    """A subjob for a stencil to be read/written to/from a collection."""

    job_id: str
    cursor: List[int]


@dataclass
class StencilDB:
    """A stencil to be read/written to/from a collection."""

    _id: ObjectId
    stencil_array: List[int]
    str_rep: str
    crossing_num: int
    head: List[int]
    state: int
    open_jobs: List[StencilJobDB]
