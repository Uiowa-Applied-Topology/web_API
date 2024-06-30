import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from tanglenomicon_data_api.rational import presentation_endpoint
from tanglenomicon_data_api.internal import config_store as cfg

api: FastAPI = FastAPI()
routers = [presentation_endpoint]
for ep in routers:
    api.include_router(ep.router)

pytestmark = pytest.mark.anyio


test_path = Path.cwd() / Path("tests/rational")


@pytest.fixture
def anyio_backend():
    return "asyncio"


################################################################################
################################################################################
# Test cases for the retrieve_rational_tangles endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_retrieve_rational_tangles_positive(
    get_test_cfg,
    valid_rational_col,
):
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/rational/tangles", params={"page_idx": 0, "page_size": 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100


@pytest.mark.anyio
async def test_retrieve_rational_tangles_empty_col(
    get_test_cfg,
    empty_rational_col,
):
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/rational/tangles", params={"page_idx": 0, "page_size": 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.anyio
async def test_retrieve_rational_tangles_empty_list(
    get_test_cfg,
    valid_rational_col,
):
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/rational/tangles", params={"page_idx": 0, "page_size": 0}
        )
        assert response.status_code == 404
