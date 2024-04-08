"""The Job interface.

The class describes the common interface all job types implement.

"""
from enum import Enum

class Job_State_Enum(str, Enum):
    new = "new"
    pending = "pending"
    complete = "complete"