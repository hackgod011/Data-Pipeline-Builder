# backend/tests/api/test_pipelines.py
import io
from unittest.mock import AsyncMock, patch

CSV_BYTES = b"region,revenue\nNorth,100\nSouth,200\n"

MOCK_PLAN = {
    "pipeline_id": "mock-pipe",
    "name": "Revenue by Region",
    "nl_prompt": "sum revenue by region",
    "version": 1,
    "steps": [
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/test/data.csv"},
            "output_alias": "df", "description": "Load data", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "transform", "operation": "aggregate",
            "params": {"input": "df", "group_by": ["region"], "agg": {"revenue": "sum"}},
            "output_alias": "agg_df", "description": "Aggregate", "depends_on": ["s1"],
        },
    ],
}


async def _upload_source(client):
    resp = await client.post(
        "/api/v1/sources/upload",
        files={"files": ("data.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    return resp.json()["source_ids"][0]


async def test_generate_pipeline_returns_plan(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)

    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        resp = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_id" in data
    assert data["plan"] is not None
    assert data["generated_code"] is not None
    assert "pd.read_csv" in data["generated_code"]


async def test_generate_returns_clarifying_questions(client):
    source_id = await _upload_source(client)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = ["Which column to group by?"]
        resp = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "do something", "source_ids": [source_id]},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["clarifying_questions"] == ["Which column to group by?"]
    assert data["plan"] is None


async def test_list_pipelines(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    resp = await client.get("/api/v1/pipelines")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_get_pipeline_code(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        gen = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    pipe_id = gen.json()["pipeline_id"]
    resp = await client.get(f"/api/v1/pipelines/{pipe_id}/code")
    assert resp.status_code == 200
    assert "pd.read_csv" in resp.json()["code"]


async def test_get_single_pipeline(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        gen = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    pipe_id = gen.json()["pipeline_id"]
    resp = await client.get(f"/api/v1/pipelines/{pipe_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pipe_id
    assert resp.json()["nl_prompt"] == "sum revenue by region"


async def test_get_pipeline_404(client):
    resp = await client.get("/api/v1/pipelines/nonexistent-id")
    assert resp.status_code == 404


async def test_update_pipeline_bumps_version(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        gen = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    pipe_id = gen.json()["pipeline_id"]
    updated_plan = {**MOCK_PLAN, "pipeline_id": pipe_id}
    resp = await client.put(
        f"/api/v1/pipelines/{pipe_id}",
        json={"plan": updated_plan, "code_mode": "pandas"},
    )
    assert resp.status_code == 200
    assert resp.json()["version"] == 2


async def test_update_pipeline_404(client):
    resp = await client.put(
        "/api/v1/pipelines/nonexistent-id",
        json={"plan": MOCK_PLAN, "code_mode": "pandas"},
    )
    assert resp.status_code == 404


async def test_export_pipeline_script(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        gen = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    pipe_id = gen.json()["pipeline_id"]
    resp = await client.get(f"/api/v1/pipelines/{pipe_id}/export")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    assert ".py" in resp.headers["content-disposition"]
    assert "pd.read_csv" in resp.text


async def test_get_pipeline_versions(client):
    source_id = await _upload_source(client)
    from app.schemas.pipeline import PipelinePlan
    mock_plan = PipelinePlan(**MOCK_PLAN)
    with patch("app.api.routes.pipelines.parse_nl_to_plan", new_callable=AsyncMock) as mock:
        mock.return_value = mock_plan
        gen = await client.post(
            "/api/v1/pipelines/generate",
            json={"nl_prompt": "sum revenue by region", "source_ids": [source_id]},
        )
    pipe_id = gen.json()["pipeline_id"]
    # Trigger a version save by updating
    updated_plan = {**MOCK_PLAN, "pipeline_id": pipe_id}
    await client.put(
        f"/api/v1/pipelines/{pipe_id}",
        json={"plan": updated_plan, "code_mode": "pandas"},
    )
    resp = await client.get(f"/api/v1/pipelines/{pipe_id}/versions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1  # one saved version from the update
