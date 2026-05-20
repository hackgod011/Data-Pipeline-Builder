from unittest.mock import AsyncMock, patch
from app.schemas.pipeline import PipelinePlan, PipelineStep

CSV = b"region,revenue\nNorth,100\n"

MOCK_PLAN = PipelinePlan(
    pipeline_id="p1",
    name="Test",
    nl_prompt="test",
    version=1,
    steps=[
        PipelineStep(
            step_id="s1",
            type="extract",
            operation="read_csv",
            params={"source": "x.csv"},
            output_alias="df",
            description="Load",
            depends_on=[],
        ),
    ],
)


async def _make_pipeline(client):
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as m:
        m.return_value = MOCK_PLAN
        resp = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "test", "source_ids": [], "pipeline_name": "Test"},
        )
    assert resp.status_code == 200
    return resp.json()["pipeline_id"]


async def test_execute_pipeline_returns_execution_id(client):
    pid = await _make_pipeline(client)
    resp = await client.post(f"/api/v1/pipelines/{pid}/execute")
    assert resp.status_code == 200
    data = resp.json()
    assert "execution_id" in data
    assert data["status"] == "pending"


async def test_get_execution_status(client):
    pid = await _make_pipeline(client)
    exe = await client.post(f"/api/v1/pipelines/{pid}/execute")
    eid = exe.json()["execution_id"]
    import asyncio
    await asyncio.sleep(0.2)
    resp = await client.get(f"/api/v1/executions/{eid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == eid
    assert resp.json()["status"] in {"pending", "running", "success", "failed"}


async def test_execute_nonexistent_pipeline_returns_404(client):
    resp = await client.post("/api/v1/pipelines/does-not-exist/execute")
    assert resp.status_code == 404


async def test_get_execution_404(client):
    resp = await client.get("/api/v1/executions/nonexistent-id")
    assert resp.status_code == 404


async def test_list_pipeline_executions(client):
    pid = await _make_pipeline(client)
    await client.post(f"/api/v1/pipelines/{pid}/execute")
    resp = await client.get(f"/api/v1/pipelines/{pid}/executions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] is not None
    assert "status" in data[0]


async def test_list_pipeline_executions_empty(client):
    pid = await _make_pipeline(client)
    resp = await client.get(f"/api/v1/pipelines/{pid}/executions")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_profile_returns_404_when_no_profile(client):
    pid = await _make_pipeline(client)
    exe = await client.post(f"/api/v1/pipelines/{pid}/execute")
    eid = exe.json()["execution_id"]
    resp = await client.get(f"/api/v1/executions/{eid}/profile")
    # Profile only exists after a successful run that produced an output file
    assert resp.status_code == 404
