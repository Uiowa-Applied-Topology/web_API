"""The Job interface.

The class describes the common interface all job types implement.

"""

from .job import generation_job, generation_job_results


class confirm_job_receipt(generation_job_results):
    accepted: bool = False
