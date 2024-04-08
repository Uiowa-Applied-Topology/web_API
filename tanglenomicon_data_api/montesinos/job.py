"""The Job interface.

The class describes the common interface all job types implement.

"""

from datetime import datetime
from ..interfaces.job import generation_job
from ..interfaces.job_state import state_enum


class job(generation_job):
        id: str
        timestamp: datetime
        cur_state: state_enum
        client_id: str
        rat_lists: list(list(str))

