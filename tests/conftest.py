import pytest
import json
from mongomock_motor import AsyncMongoMockClient
from pathlib import Path
from datetime import datetime, timedelta, timezone

from tanglenomicon_data_api.internal import db_connector as dbc
from tanglenomicon_data_api.internal import config_store as cfg
from tanglenomicon_data_api.internal import job_queue
from jose import jwt


test_path = Path.cwd() / Path("tests")


def _load_fixture(path: Path) -> dict:
    dat = None
    with open(path) as f:
        dat = json.load(f)
    return dat
    ...


@pytest.fixture
async def setup_job_queue():
    # stub the db connection.
    job_queue._job_queue = {}
    yield  # Provide the data to the test
    job_queue._job_queue = {}
    # Teardown: Clean up resources (if any) after the test


@pytest.fixture
async def setup_database():
    # stub the db connection.
    dbc.db = AsyncMongoMockClient()["test_tanglenomicon"]
    yield  # Provide the data to the test
    dbc.db = None
    # Teardown: Clean up resources (if any) after the test


@pytest.fixture
async def empty_montesinos_storage_col(setup_database):
    col = dbc.db[
        cfg.cfg_dict["tangle-classes"]["montesinos"]["montesinos_storage_col_name"]
    ]
    await col.delete_many({})
    yield
    await col.delete_many({})


@pytest.fixture
async def empty_montesinos_stencil_col(setup_database):
    col = dbc.db[
        cfg.cfg_dict["tangle-classes"]["montesinos"]["montesinos_stencil_col_name"]
    ]
    await col.delete_many({})
    yield
    await col.delete_many({})


@pytest.fixture
async def empty_rational_col(setup_database):
    col = dbc.db[cfg.cfg_dict["tangle-classes"]["rational"]["rational_col_name"]]
    await col.delete_many({})
    yield
    await col.delete_many({})


@pytest.fixture
async def valid_rational_col(setup_database):
    col = dbc.db[cfg.cfg_dict["tangle-classes"]["rational"]["rational_col_name"]]
    dat = _load_fixture(test_path / Path("fixtures") / "valid_rational_col.json")

    await col.delete_many({})
    await col.insert_many(dat)
    yield
    await col.delete_many({})


@pytest.fixture
async def valid_montesinos_stencil_col(setup_database):
    col = dbc.db[
        cfg.cfg_dict["tangle-classes"]["montesinos"]["montesinos_stencil_col_name"]
    ]
    dat = _load_fixture(test_path / Path("fixtures") / "valid_stencil_col.json")

    await col.delete_many({})
    await col.insert_many(dat)
    yield
    await col.delete_many({})


@pytest.fixture
async def valid_montesinos_stencil_col_all_new(setup_database):
    col = dbc.db[
        cfg.cfg_dict["tangle-classes"]["montesinos"]["montesinos_stencil_col_name"]
    ]
    dat = _load_fixture(test_path / Path("fixtures") / "valid_stencil_col_all_new.json")

    await col.delete_many({})
    await col.insert_many(dat)
    yield
    await col.delete_many({})



@pytest.fixture
async def valid_auth_col(setup_database):
    col = dbc.db[cfg.cfg_dict["auth"]["auth-col-name"]]
    dat = _load_fixture(test_path / Path("fixtures") / "valid_auth_col.json")

    await col.delete_many({})
    await col.insert_many(dat)
    yield
    await col.delete_many({})


@pytest.fixture
async def get_test_jwt(valid_auth_col):
    dat = _load_fixture(test_path / Path("fixtures") / "fake_creds.json")
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    dat["exp"] = expire
    token = jwt.encode(
        dat,
        cfg.cfg_dict["auth"]["secret_key"],
        algorithm=cfg.cfg_dict["auth"]["algorithm"],
    )
    yield token
    token = None
