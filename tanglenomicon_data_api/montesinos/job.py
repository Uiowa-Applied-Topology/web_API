"""The Job interface.

The class describes the common interface all job types implement.

"""

from datetime import datetime
from ..interfaces.job import generation_job, generation_job_results
from ..interfaces.job_state import Job_State_Enum
from typing import List


class Montesinos_Job_Results(generation_job_results):
    mont_list: List[str]


class Montesinos_Job(generation_job):
    rat_lists: List[List[str]]
    _results: Montesinos_Job_Results = None

    def store(self):

        ...

    def update_results(self, res: Montesinos_Job_Results):
        self._results = res
