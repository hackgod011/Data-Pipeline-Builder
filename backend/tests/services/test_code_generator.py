# backend/tests/services/test_code_generator.py
import ast
from app.schemas.pipeline import PipelinePlan, PipelineStep
from app.services.code_generator import generate_code


def make_plan(steps: list[dict]) -> PipelinePlan:
    return PipelinePlan(
        pipeline_id="test",
        name="Test",
        nl_prompt="test",
        version=1,
        steps=[PipelineStep(**s) for s in steps],
    )


def test_generates_valid_python(tmp_path):
    plan = make_plan([
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/test.csv"},
            "output_alias": "df", "description": "Load CSV", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "load", "operation": "write_csv",
            "params": {"input": "df", "destination": "outputs/out.csv"},
            "output_alias": "output", "description": "Save", "depends_on": ["s1"],
        },
    ])
    code = generate_code(plan)
    ast.parse(code)  # raises SyntaxError if invalid


def test_read_csv_in_output():
    plan = make_plan([{
        "step_id": "s1", "type": "extract", "operation": "read_csv",
        "params": {"source": "uploads/sales.csv"},
        "output_alias": "sales_df", "description": "Load", "depends_on": [],
    }])
    code = generate_code(plan)
    assert "pd.read_csv" in code
    assert "sales_df" in code


def test_filter_step_in_output():
    plan = make_plan([
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/data.csv"},
            "output_alias": "df", "description": "Load", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "transform", "operation": "filter",
            "params": {"input": "df", "condition": "region == 'North'"},
            "output_alias": "filtered_df", "description": "Filter North", "depends_on": ["s1"],
        },
    ])
    code = generate_code(plan)
    assert "query(" in code or "region == 'North'" in code


def test_aggregate_step_uses_groupby():
    plan = make_plan([
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/data.csv"},
            "output_alias": "df", "description": "Load", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "transform", "operation": "aggregate",
            "params": {"input": "df", "group_by": ["region"], "agg": {"revenue": "sum"}},
            "output_alias": "agg_df", "description": "Aggregate", "depends_on": ["s1"],
        },
    ])
    code = generate_code(plan)
    assert "groupby" in code
    assert "revenue" in code


def test_join_step_uses_merge():
    plan = make_plan([
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/a.csv"},
            "output_alias": "left_df", "description": "Load A", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "extract", "operation": "read_csv",
            "params": {"source": "uploads/b.csv"},
            "output_alias": "right_df", "description": "Load B", "depends_on": [],
        },
        {
            "step_id": "s3", "type": "transform", "operation": "join",
            "params": {"left": "left_df", "right": "right_df", "on": "id", "how": "inner"},
            "output_alias": "joined_df", "description": "Join", "depends_on": ["s1", "s2"],
        },
    ])
    code = generate_code(plan)
    assert "merge" in code
    assert "how='inner'" in code


def test_step_markers_present():
    plan = make_plan([{
        "step_id": "s1", "type": "extract", "operation": "read_csv",
        "params": {"source": "uploads/data.csv"},
        "output_alias": "df", "description": "Load", "depends_on": [],
    }])
    code = generate_code(plan)
    assert "PIPEFORGE:STEP_START:s1" in code
    assert "PIPEFORGE:STEP_END:s1:success" in code


def test_generated_code_is_executable(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,value\nAlice,10\nBob,20\n")
    out_file = tmp_path / "out.csv"

    plan = make_plan([
        {
            "step_id": "s1", "type": "extract", "operation": "read_csv",
            "params": {"source": str(csv_file)},
            "output_alias": "df", "description": "Load", "depends_on": [],
        },
        {
            "step_id": "s2", "type": "load", "operation": "write_csv",
            "params": {"input": "df", "destination": str(out_file)},
            "output_alias": "out", "description": "Save", "depends_on": ["s1"],
        },
    ])
    code = generate_code(plan)
    exec(compile(code, "<pipeline>", "exec"), {})
    assert out_file.exists()
