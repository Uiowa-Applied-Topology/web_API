import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from anyio import create_task_group, move_on_after, sleep, run

from tanglenomicon_data_api.interfaces.job import GenerationJob, JobStateEnum
from tanglenomicon_data_api.internal import security
from tanglenomicon_data_api.internal.security import User
from tanglenomicon_data_api.internal import job_queue as jq
from tanglenomicon_data_api.internal import config_store as cfg


class MockClass(GenerationJob):
    item: int = 0

    async def store(self): ...
    def update_results(self, results): ...


api: FastAPI = FastAPI()
routers = [security, jq]
for ep in routers:
    api.include_router(ep.router)

pytestmark = pytest.mark.anyio


test_path = Path.cwd() / Path("tests/internal")

cfg.load(test_path / "test_config.yaml")


@pytest.fixture
def anyio_backend():
    return "asyncio"


################################################################################
################################################################################
# Test cases for the retrieve_job_statistics endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_retrieve_job_statistics_positive(setup_job_queue, get_test_jwt):
    headers = {"Authorization": f"Bearer {get_test_jwt}"}
    transport = ASGITransport(app=api)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/job_queue/stats", headers=headers)
        assert response.status_code == 200
        assert response.json() == {
            "queue_length": 0,
            "new": 0,
            "pending": 0,
            "complete": 0,
        }
        for i in range(5):
            job_id = f"pending {i}"
            job = GenerationJob(
                cur_state=JobStateEnum.pending,
                timestamp=datetime.now(timezone.utc),
                job_id=job_id,
            )
            jq._job_queue[job_id] = job
        for i in range(3):
            job_id = f"new {i}"
            job = GenerationJob(
                cur_state=JobStateEnum.new,
                timestamp=datetime.now(timezone.utc),
                job_id=job_id,
            )
            jq._job_queue[job_id] = job
        for i in range(6):
            job_id = f"complete {i}"
            job = GenerationJob(
                cur_state=JobStateEnum.complete,
                timestamp=datetime.now(timezone.utc),
                job_id=job_id,
            )
            jq._job_queue[job_id] = job

        response = await ac.get("/job_queue/stats", headers=headers)
        assert response.status_code == 200
        assert response.json() == {
            "queue_length": 14,
            "new": 3,
            "pending": 5,
            "complete": 6,
        }


################################################################################
################################################################################
# Test cases for the get_job_statistics endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_get_job_statistics_default(setup_job_queue):
    data = jq.get_job_statistics()
    assert data == {
        "queue_length": 0,
        "new": 0,
        "pending": 0,
        "complete": 0,
    }
    for i in range(5):
        job_id = f"pending {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    data = jq.get_job_statistics()
    assert data == {
        "queue_length": 14,
        "new": 3,
        "pending": 5,
        "complete": 6,
    }


@pytest.mark.anyio
async def test_get_job_statistics_specific(setup_job_queue):
    data = jq.get_job_statistics(MockClass)
    assert data == {
        "queue_length": 0,
        "new": 0,
        "pending": 0,
        "complete": 0,
    }
    for i in range(5):
        job_id = f"pending {i}"
        job = MockClass(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = MockClass(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = MockClass(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    data = jq.get_job_statistics(MockClass)
    assert data == {
        "queue_length": 14,
        "new": 3,
        "pending": 5,
        "complete": 6,
    }


@pytest.mark.anyio
async def test_get_job_statistics_nonexistent(setup_job_queue):
    data = jq.get_job_statistics(MockClass)
    assert data == {
        "queue_length": 0,
        "new": 0,
        "pending": 0,
        "complete": 0,
    }
    for i in range(5):
        job_id = f"pending {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    data = jq.get_job_statistics(MockClass)
    assert data == {
        "queue_length": 0,
        "new": 0,
        "pending": 0,
        "complete": 0,
    }


################################################################################
################################################################################
# Test cases for the task_clean_stale_jobs endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_clean_stale_jobs_positive(setup_job_queue):

    job_id = f"new"
    for i in range(5):
        job_id = f"pending {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    with move_on_after(20) as mo:
        await jq.task_clean_stale_jobs()
    pending = [
        j for j in jq._job_queue if jq._job_queue[j].cur_state == JobStateEnum.pending
    ]
    assert len(pending) == 0
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 14


@pytest.mark.anyio
async def test_clean_stale_jobs_empty(setup_job_queue):

    job_id = f"new"
    for i in range(3):
        job_id = f"new {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = GenerationJob(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 9
    with move_on_after(20) as mo:
        await jq.task_clean_stale_jobs()
    pending = [
        j for j in jq._job_queue if jq._job_queue[j].cur_state == JobStateEnum.pending
    ]
    assert len(pending) == 0
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 9


################################################################################
################################################################################
# Test cases for the task_clean_complete_jobs endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_task_clean_complete_jobs_positive(setup_job_queue):

    job_id = f"new"
    for i in range(5):
        job_id = f"pending {i}"
        job = MockClass(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = MockClass(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(6):
        job_id = f"complete {i}"
        job = MockClass(
            cur_state=JobStateEnum.complete,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job

    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 14
    with move_on_after(20) as mo:
        await jq.task_clean_complete_jobs()
    complete = [
        j for j in jq._job_queue if jq._job_queue[j].cur_state == JobStateEnum.complete
    ]
    assert len(complete) == 0
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 8


@pytest.mark.anyio
async def test_task_clean_complete_jobs_empty(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    for i in range(5):
        job_id = f"pending {i}"
        job = MockClass(
            cur_state=JobStateEnum.pending,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    for i in range(3):
        job_id = f"new {i}"
        job = MockClass(
            cur_state=JobStateEnum.new,
            timestamp=datetime.now(timezone.utc),
            job_id=job_id,
        )
        jq._job_queue[job_id] = job
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 8
    with move_on_after(20) as mo:
        await jq.task_clean_stale_jobs()
    complete = [
        j for j in jq._job_queue if jq._job_queue[j].cur_state == JobStateEnum.complete
    ]
    assert len(complete) == 0
    all_ent = [j for j in jq._job_queue]
    assert len(all_ent) == 8


################################################################################
################################################################################
# Test cases for the enqueue_job endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_enqueue_job_positive(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    job = GenerationJob(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    res = await jq.enqueue_job(job)
    assert res == True
    assert jq._job_queue[job_id]
    assert jq._job_queue[job_id] == job


@pytest.mark.anyio
async def test_enqueue_job_in_queue(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    job = GenerationJob(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    jq._job_queue[job_id] = job
    assert jq._job_queue[job_id]
    res = await jq.enqueue_job(job)
    assert res == False



################################################################################
################################################################################
# Test cases for the mark_job_complete endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_mark_job_complete_job_in_queue(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    user = User(username=client_id)
    job = MockClass(
        cur_state=JobStateEnum.pending,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    jq._job_queue[job_id] = job
    assert jq._job_queue[job_id]
    res = await jq.mark_job_complete(job, user)
    assert res == True
    assert jq._job_queue[job_id]
    assert jq._job_queue[job_id].cur_state == JobStateEnum.complete


@pytest.mark.anyio
async def test_mark_job_complete_job_not_in_queue(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    user = User(username=client_id)
    job = MockClass(
        cur_state=JobStateEnum.pending,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    res = await jq.mark_job_complete(job, user)
    assert res == False


@pytest.mark.anyio
async def test_mark_job_complete_job_not_in_pending(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    user = User(username=client_id)
    job = MockClass(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    jq._job_queue[job_id] = job
    assert jq._job_queue[job_id]
    res = await jq.mark_job_complete(job, user)
    assert res == False


@pytest.mark.anyio
async def test_mark_job_complete_job_mismatch_client(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    user = User(username="not the client")
    job = MockClass(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    jq._job_queue[job_id] = job
    assert jq._job_queue[job_id]
    res = await jq.mark_job_complete(job, user)
    assert res == False


################################################################################
################################################################################
# Test cases for the get_next_job endpoint
################################################################################
################################################################################


@pytest.mark.anyio
async def test_get_next_job_with_jobs_in_queue(setup_job_queue):

    job_id = f"new"
    client_id = "client"
    user = User(username=client_id)
    job = MockClass(
        cur_state=JobStateEnum.new,
        timestamp=datetime.now(timezone.utc),
        job_id=job_id,
        client_id=client_id,
    )
    jq._job_queue[job_id] = job
    assert jq._job_queue[job_id]
    res = await jq.get_next_job(MockClass, user)
    assert res
    assert isinstance(res, GenerationJob)
    assert jq._job_queue[res.job_id].cur_state == JobStateEnum.pending
    assert jq._job_queue[res.job_id].client_id == client_id


@pytest.mark.anyio
async def test_get_next_job_empty_queue(setup_job_queue):

    client_id = "client"
    user = User(username=client_id)
    res = await jq.get_next_job(MockClass, user)
    assert res == None
