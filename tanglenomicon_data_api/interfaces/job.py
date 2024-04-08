"""The Job interface.

The class describes the common interface all job types implement.

"""

from datetime import datetime
from .job_state import Job_State_Enum
from pydantic import BaseModel


class generation_job_results(BaseModel):
    id: str


class generation_job(BaseModel):
    id: str
    timestamp: datetime
    cur_state: Job_State_Enum
    client_id: str = None
    _results: generation_job_results

    def store(self):
        ...
        raise NotImplementedError

    def update_results(self, res: generation_job_results):
        ...
        raise NotImplementedError
