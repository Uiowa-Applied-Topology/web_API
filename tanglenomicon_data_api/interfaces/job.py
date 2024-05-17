"""The Job interface.

The class describes the common interface all job types implement.

"""

from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class Job_State_Enum(str, Enum):
    """_summary_

    Parameters
    ----------
    str : _type_
        _description_
    Enum : _type_
        _description_
    """

    new = "new"
    pending = "pending"
    complete = "complete"


class generation_job_results(BaseModel):
    """_summary_

    Parameters
    ----------
    BaseModel : _type_
        _description_
    """

    id: str


class generation_job(BaseModel):
    """_summary_

    Parameters
    ----------
    BaseModel : _type_
        _description_

    Raises
    ------
    NotImplementedError
        _description_
    NotImplementedError
        _description_
    """

    id: str
    timestamp: datetime
    cur_state: Job_State_Enum = Job_State_Enum.new
    client_id: str = None
    _results: generation_job_results

    def store(self):
        """_summary_

        Raises
        ------
        NotImplementedError
            _description_
        """
        raise NotImplementedError

    def update_results(self, res: generation_job_results):
        """_summary_

        Parameters
        ----------
        res : generation_job_results
            _description_

        Raises
        ------
        NotImplementedError
            _description_
        """
        raise NotImplementedError


class confirm_job_receipt(generation_job_results):
    """_summary_

    Parameters
    ----------
    generation_job_results : _type_
        _description_
    """

    accepted: bool = False
