from fastapi import Depends, FastAPI

from .montesinos import endpoint as mont_e
from .montesinos import job as mont_j
from .interfaces.job_state import Job_State_Enum
from .internal import db_connector, security, config, job_queue
import time
import uuid
import uvicorn
from fastapi import FastAPI
import argparse
import asyncio


api: FastAPI = FastAPI()
routers = [security, mont_e]


@api.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cfg")
    args = parser.parse_args()
    config.load(args.cfg)
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

    job = mont_j.Montesinos_Job(
        cur_state=Job_State_Enum.new,
        timestamp=time.time(),
        id=str(uuid.uuid4()),
        rat_lists=list(),
    )

    asyncio.run(job_queue.enqueue_job(job))  # TODO: Remove
    # run server
    uvicorn.run(api)

if __name__ == "__main__":
    main()
