"""Defines the ORM for rational tangles."""

from dataclasses import dataclass
from typing import List


@dataclass
class RationalTangDB:
    """The ORM for rational tangles stored in mongodb."""

    _id: str
    twist_vector: str
    crossing_num: int
    tv_array: List[int]
    in_unit_interval: bool
