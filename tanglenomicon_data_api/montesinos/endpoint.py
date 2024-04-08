from fastapi import Depends, APIRouter, HTTPException, status
from ..internal.security import auth_current_user, get_current_user, User
from ..internal import db_connector as dbc
from ..interfaces.job_state import Job_State_Enum
from ..interfaces.confirm import confirm_job_receipt
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union
from pydantic import BaseModel
import motor.motor_asyncio
from . import job as mj
from ..internal import job_queue
import time
import uuid

router = APIRouter(
    prefix="/montesinos",
    tags=["Tangles", "Algebraic", "Montesinos", "Generation"],
    dependencies=[Depends(auth_current_user)],
    responses={404: {"description": "Not found"}},
)


async def report_job_results(
    job_results: mj.Montesinos_Job_Results,
    current_user: Annotated[User, Depends(get_current_user)],
) -> confirm_job_receipt:
    await job_queue.mark_job_complete(job_results,current_user)
    results = confirm_job_receipt(id=job_results.id, accepted=True)
    return results


async def get_next_montesinos_job(
    current_user: Annotated[User, Depends(get_current_user)]
):
    job = await job_queue.get_next_job(mj.Montesinos_Job, current_user)
    return job


@router.post("/job/report")
async def report_montesinos_job(
    response: Annotated[confirm_job_receipt, Depends(report_job_results)],
) -> confirm_job_receipt:
    return response


@router.get("/job/retrieve", response_model=mj.Montesinos_Job)
async def retrieve_montesinos_job(
    next_job: Annotated[mj.Montesinos_Job, Depends(get_next_montesinos_job)]
):
    return next_job
