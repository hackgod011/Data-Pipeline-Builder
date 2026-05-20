# backend/tests/services/test_nl_parser.py
import json
import pytest
from unittest.mock import AsyncMock, patch
from app.services.nl_parser import parse_nl_to_plan, build_schema_context
from app.schemas.pipeline import PipelinePlan


FAKE_SCHEMA = [
    {
        "name": "sales",
        "columns": [
            {"name": "order_id", "dtype": "int64", "sample_values": ["1", "2"]},
            {"name": "region", "dtype": "object", "sample_values": ["North", "South"]},
            {"name": "revenue", "dtype": "float64", "sample_values": ["100.0", "200.0"]},
        ],
    }
]

VALID_PLAN_JSON = json.dumps({
    "pipeline_id": "test-pipe",
    "name": "Region Count",
    "nl_prompt": "count rows by region",
    "version": 1,
    "steps": [
        {
            "step_id": "step_001",
            "type": "extract",
            "operation": "read_csv",
            "params": {"source": "uploads/sales.csv"},
            "output_alias": "sales_df",
            "description": "Load sales data",
            "depends_on": [],
        },
        {
            "step_id": "step_002",
            "type": "transform",
            "operation": "aggregate",
            "params": {"input": "sales_df", "group_by": ["region"], "agg": {"order_id": "count"}},
            "output_alias": "result_df",
            "description": "Count by region",
            "depends_on": ["step_001"],
        },
    ],
})

CLARIFY_JSON = json.dumps({
    "clarifying_questions": ["Which column should I group by?"]
})


def test_build_schema_context_includes_column_names():
    ctx = build_schema_context(FAKE_SCHEMA)
    assert "order_id" in ctx
    assert "region" in ctx
    assert "revenue" in ctx


def test_build_schema_context_includes_sample_values():
    ctx = build_schema_context(FAKE_SCHEMA)
    assert "North" in ctx


@pytest.mark.asyncio
async def test_parse_returns_pipeline_plan_on_valid_response():
    with patch("app.services.nl_parser._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = VALID_PLAN_JSON
        result = await parse_nl_to_plan(
            nl_prompt="count rows by region",
            schema_context=FAKE_SCHEMA,
            pipeline_id="test-pipe",
            pipeline_name="Region Count",
        )
    assert isinstance(result, PipelinePlan)
    assert len(result.steps) == 2


@pytest.mark.asyncio
async def test_parse_returns_clarifying_questions():
    with patch("app.services.nl_parser._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = CLARIFY_JSON
        result = await parse_nl_to_plan(
            nl_prompt="do something",
            schema_context=FAKE_SCHEMA,
            pipeline_id="test-pipe",
            pipeline_name="Test",
        )
    assert isinstance(result, list)
    assert "Which column" in result[0]


@pytest.mark.asyncio
async def test_parse_retries_on_invalid_json():
    with patch("app.services.nl_parser._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = ["not json at all", VALID_PLAN_JSON]
        result = await parse_nl_to_plan(
            nl_prompt="count by region",
            schema_context=FAKE_SCHEMA,
            pipeline_id="test-pipe",
            pipeline_name="Test",
        )
    assert isinstance(result, PipelinePlan)
    assert mock_llm.call_count == 2
