from fastapi import Depends, FastAPI

from .montesinos import endpoint as mont_e
from .montesinos import job as mont_j
from .interfaces.job_state import Job_State_Enum
from .internal import db_connector, security, config, job_queue
import time
import uuid
from uvicorn import Config as ucfg, Server as usrv
from fastapi import FastAPI
import argparse
import asyncio
from asyncio import AbstractEventLoop


loop: AbstractEventLoop = asyncio.new_event_loop()
api: FastAPI = FastAPI()
routers = [security, mont_e, job_queue]
job_defs = [
    mont_j.startup_jobs(),
    job_queue.task_clean_complete_jobs(),
    job_queue.task_clean_stale_jobs(),
]


@api.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


def startup():
    global loop

    db_cfg = config.config["db-connection-info"]
    db_connector.init_client(
        db_cfg["domain"],
        db_cfg["port"],
        db_cfg["user"],
        db_cfg["password"],
        db_cfg["database"],
    )

    for endpoint in routers:
        api.include_router(endpoint.router)
    for job_def in job_defs:
        loop.create_task(job_def)


def main():
    global api
    global loop

    loop.run_until_complete(usrv(ucfg(app=api, loop=loop)).serve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cfg")
    args = parser.parse_args()
    config.load(args.cfg)

    startup()

    main()
