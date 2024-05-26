
from dataclasses import dataclass
from typing import List


@dataclass
class rational_tang_db:
    _id: str
    twist_vector: str
    crossing_num: int
    tv_array: List[int]
    in_unit_interval: bool