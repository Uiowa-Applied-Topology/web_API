"""The __main__ file/entry point for tanglenomicon_data_api."""

from .montesinos import endpoint as mont_e
from .montesinos import job as mont_j
from .internal import config_store, db_connector, security, job_queue
from fastapi import FastAPI
from uvicorn import Config as UCfg, Server as USrv
import typer
import asyncio
from asyncio import AbstractEventLoop
from typing_extensions import Annotated
from getpass import getpass, getuser
from fastapi.middleware.cors import CORSMiddleware
import logging

loop: AbstractEventLoop = asyncio.new_event_loop()
api: FastAPI = FastAPI()
routers = [security, mont_e, job_queue]
job_defs = [
    mont_j.startup_task,
    job_queue.task_clean_complete_jobs,
    job_queue.task_clean_stale_jobs,
]

logging.getLogger("uvicorn").setLevel(logging.ERROR)

app = typer.Typer()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:1313",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8080",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _startup():
    """Executes a collection of tasks at startup of the API."""
    global loop

    db_cfg = config_store.cfg_dict["db-connection-info"]
    db_connector.init_client(
        db_cfg["domain"],
        db_cfg["port"],
        db_cfg["user"],
        db_cfg["password"],
        db_cfg["database"],
    )


def _main():
    """Executes the main task of the API."""
    global api
    global loop
    global routers
    global job_defs

    for endpoint in routers:
        api.include_router(endpoint.router)
    for job_def in job_defs:
        loop.create_task(job_def())

    loop.run_until_complete(USrv(UCfg(app=api, loop=loop)).serve())


@app.command()
def adduser(
    cfg: Annotated[str, typer.Option(prompt="Path to configuration file.")],
    name: Annotated[str, typer.Option(prompt="Username to add")] = None,
):
    """Add a user to the database."""
    config_store.load(cfg)
    _startup()
    if not name:
        name = getuser("Username: ")
    while (pswd := getpass("Password:")) != getpass("Retype Password:"):
        print("Passwords do not match. Please try again.")
    loop.run_until_complete(security.add_user(name, pswd))
    ...


@app.command()
def run(
    cfg: Annotated[str, typer.Option(prompt="Path to configuration file.")],
):
    """Run the server."""
    config_store.load(cfg)

    _startup()

    _main()


if __name__ == "__main__":
    app()
