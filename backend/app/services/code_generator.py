from app.schemas.pipeline import PipelinePlan, PipelineStep

HEADER = '''import pandas as pd
import json
from pathlib import Path

'''

SQL_HEADER = '''import duckdb
from pathlib import Path

con = duckdb.connect()

'''


def _p(path: str) -> str:
    """Normalize backslashes so embedded paths are valid Python string literals."""
    return path.replace("\\", "/")


def _step_read_csv(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f'{step.output_alias} = pd.read_csv("{src}")\n'


def _step_read_excel(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f'{step.output_alias} = pd.read_excel("{src}", engine="openpyxl")\n'


def _step_read_json(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f'{step.output_alias} = pd.read_json("{src}")\n'


def _step_read_parquet(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f'{step.output_alias} = pd.read_parquet("{src}")\n'


def _step_filter(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cond = step.params.get("condition", "True")
    return f'{step.output_alias} = {inp}.query("{cond}")\n'


def _step_join(step: PipelineStep) -> str:
    left = step.params.get("left", "left_df")
    right = step.params.get("right", "right_df")
    on = step.params.get("on", "id")
    how = step.params.get("how", "inner")
    return f"{step.output_alias} = {left}.merge({right}, on='{on}', how='{how}')\n"


def _step_aggregate(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    group_by = step.params.get("group_by", [])
    agg = step.params.get("agg", {})
    group_str = str(group_by)
    agg_str = str(agg).replace("'", '"')
    return (
        f"{step.output_alias} = {inp}.groupby({group_str}).agg({agg_str}).reset_index()\n"
    )


def _step_sort(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    by = step.params.get("by", [])
    asc = step.params.get("ascending", True)
    return f"{step.output_alias} = {inp}.sort_values(by={by}, ascending={asc}).reset_index(drop=True)\n"


def _step_rename(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cols = step.params.get("columns", {})
    return f"{step.output_alias} = {inp}.rename(columns={cols})\n"


def _step_drop_columns(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cols = step.params.get("columns", [])
    return f"{step.output_alias} = {inp}.drop(columns={cols})\n"


def _step_fill_nulls(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    col = step.params.get("column", "")
    val = step.params.get("value", 0)
    val_repr = f'"{val}"' if isinstance(val, str) else str(val)
    return f'{step.output_alias} = {inp}.copy()\n{step.output_alias}["{col}"] = {step.output_alias}["{col}"].fillna({val_repr})\n'


def _step_dedup(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    subset = step.params.get("subset", None)
    subset_str = str(subset) if subset else "None"
    return f"{step.output_alias} = {inp}.drop_duplicates(subset={subset_str}).reset_index(drop=True)\n"


def _step_cast(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    col = step.params.get("column", "")
    dtype = step.params.get("dtype", "str")
    if dtype == "datetime":
        return f'{step.output_alias} = {inp}.copy()\n{step.output_alias}["{col}"] = pd.to_datetime({step.output_alias}["{col}"])\n'
    return f'{step.output_alias} = {inp}.copy()\n{step.output_alias}["{col}"] = {step.output_alias}["{col}"].astype("{dtype}")\n'


def _step_write_csv(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    dest = _p(step.params.get("destination", "outputs/output.csv"))
    return f'Path("{dest}").parent.mkdir(parents=True, exist_ok=True)\n{inp}.to_csv("{dest}", index=False)\n'


def _step_write_parquet(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    dest = _p(step.params.get("destination", "outputs/output.parquet"))
    return f'Path("{dest}").parent.mkdir(parents=True, exist_ok=True)\n{inp}.to_parquet("{dest}", index=False)\n'


OPERATION_MAP = {
    "read_csv": _step_read_csv,
    "read_excel": _step_read_excel,
    "read_json": _step_read_json,
    "read_parquet": _step_read_parquet,
    "filter": _step_filter,
    "join": _step_join,
    "aggregate": _step_aggregate,
    "sort": _step_sort,
    "rename": _step_rename,
    "drop_columns": _step_drop_columns,
    "fill_nulls": _step_fill_nulls,
    "dedup": _step_dedup,
    "cast": _step_cast,
    "write_csv": _step_write_csv,
    "write_parquet": _step_write_parquet,
}


# ──────────────────────────────────────────────────────────────────────────────
# SQL mode: generates DuckDB-based Python code instead of Pandas
# ──────────────────────────────────────────────────────────────────────────────

def _sql_read_csv(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM read_csv_auto('{src}')\")\n"


def _sql_read_parquet(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM read_parquet('{src}')\")\n"


def _sql_read_excel(step: PipelineStep) -> str:
    # DuckDB has no native Excel reader; load via pandas then register
    src = _p(step.params.get("source", ""))
    return (
        f"import pandas as _pd\n"
        f"_tmp_{step.output_alias} = _pd.read_excel(\"{src}\", engine=\"openpyxl\")\n"
        f"con.register(\"{step.output_alias}\", _tmp_{step.output_alias})\n"
        f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {step.output_alias}\")\n"
    )


def _sql_read_json(step: PipelineStep) -> str:
    src = _p(step.params.get("source", ""))
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM read_json_auto('{src}')\")\n"


def _sql_filter(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cond = step.params.get("condition", "TRUE").replace('"', "'")
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp} WHERE {cond}\")\n"


def _sql_join(step: PipelineStep) -> str:
    left = step.params.get("left", "left_table")
    right = step.params.get("right", "right_table")
    on = step.params.get("on", "id")
    how = step.params.get("how", "inner").upper()
    return (
        f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
        f"SELECT * FROM {left} {how} JOIN {right} ON {left}.{on} = {right}.{on}\")\n"
    )


def _sql_aggregate(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    group_by: list[str] = step.params.get("group_by", [])
    agg: dict[str, str] = step.params.get("agg", {})
    if group_by and agg:
        gb_cols = ", ".join(group_by)
        agg_parts = ", ".join(f"{func}({col}) AS {col}_{func}" for col, func in agg.items())
        return (
            f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
            f"SELECT {gb_cols}, {agg_parts} FROM {inp} GROUP BY {gb_cols}\")\n"
        )
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp}\")\n"


def _sql_sort(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    by = step.params.get("by", [])
    asc = step.params.get("ascending", True)
    order = "ASC" if asc else "DESC"
    by_str = ", ".join(by) if isinstance(by, list) else str(by)
    return (
        f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
        f"SELECT * FROM {inp} ORDER BY {by_str} {order}\")\n"
    )


def _sql_rename(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cols: dict[str, str] = step.params.get("columns", {})
    if cols:
        renames = ", ".join(f"{old} AS {new}" for old, new in cols.items())
        excludes = ", ".join(cols.keys())
        return (
            f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
            f"SELECT * EXCLUDE ({excludes}), {renames} FROM {inp}\")\n"
        )
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp}\")\n"


def _sql_drop_columns(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    cols: list[str] = step.params.get("columns", [])
    if cols:
        excludes = ", ".join(cols)
        return (
            f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
            f"SELECT * EXCLUDE ({excludes}) FROM {inp}\")\n"
        )
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp}\")\n"


def _sql_fill_nulls(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    col = step.params.get("column", "")
    val = step.params.get("value", 0)
    val_str = f"'{val}'" if isinstance(val, str) else str(val)
    if col:
        return (
            f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
            f"SELECT * EXCLUDE ({col}), COALESCE({col}, {val_str}) AS {col} FROM {inp}\")\n"
        )
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp}\")\n"


def _sql_dedup(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT DISTINCT * FROM {inp}\")\n"


def _sql_cast(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    col = step.params.get("column", "")
    dtype = step.params.get("dtype", "VARCHAR")
    duck_type = {"str": "VARCHAR", "int": "BIGINT", "float": "DOUBLE", "datetime": "TIMESTAMP"}.get(dtype, dtype.upper())
    if col:
        return (
            f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS "
            f"SELECT * EXCLUDE ({col}), CAST({col} AS {duck_type}) AS {col} FROM {inp}\")\n"
        )
    return f"con.execute(\"CREATE OR REPLACE TABLE {step.output_alias} AS SELECT * FROM {inp}\")\n"


def _sql_write_csv(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    dest = _p(step.params.get("destination", "outputs/output.csv"))
    return (
        f'Path("{dest}").parent.mkdir(parents=True, exist_ok=True)\n'
        f'con.execute(f\'COPY {inp} TO "{dest}" (FORMAT CSV, HEADER)\')\n'
    )


def _sql_write_parquet(step: PipelineStep) -> str:
    inp = step.params.get("input", "df")
    dest = _p(step.params.get("destination", "outputs/output.parquet"))
    return (
        f'Path("{dest}").parent.mkdir(parents=True, exist_ok=True)\n'
        f'con.execute(f\'COPY {inp} TO "{dest}" (FORMAT PARQUET)\')\n'
    )


SQL_OPERATION_MAP = {
    "read_csv": _sql_read_csv,
    "read_excel": _sql_read_excel,
    "read_json": _sql_read_json,
    "read_parquet": _sql_read_parquet,
    "filter": _sql_filter,
    "join": _sql_join,
    "aggregate": _sql_aggregate,
    "sort": _sql_sort,
    "rename": _sql_rename,
    "drop_columns": _sql_drop_columns,
    "fill_nulls": _sql_fill_nulls,
    "dedup": _sql_dedup,
    "cast": _sql_cast,
    "write_csv": _sql_write_csv,
    "write_parquet": _sql_write_parquet,
}


def generate_sql_code(plan: PipelinePlan) -> str:
    lines = [SQL_HEADER, f'# Pipeline: {plan.name}\n# Generated from: {plan.nl_prompt}\n\n']
    for step in plan.steps:
        fn = SQL_OPERATION_MAP.get(step.operation)
        if fn is None:
            lines.append(f"# WARNING: unknown SQL operation '{step.operation}' — skipped\n")
            continue
        lines.append(f"# Step: {step.description}\n")
        lines.append(f'print("PIPEFORGE:STEP_START:{step.step_id}", flush=True)\n')
        try:
            lines.append(fn(step))
        except Exception as exc:
            lines.append(f"# ERROR generating step {step.step_id}: {exc}\n")
        lines.append(f'print("PIPEFORGE:STEP_END:{step.step_id}:success", flush=True)\n')
        lines.append("\n")
    return "".join(lines)


def generate_code(plan: PipelinePlan) -> str:
    lines = [HEADER, f'# Pipeline: {plan.name}\n# Generated from: {plan.nl_prompt}\n\n']
    for step in plan.steps:
        fn = OPERATION_MAP.get(step.operation)
        if fn is None:
            lines.append(f"# WARNING: unknown operation '{step.operation}' — skipped\n")
            continue
        lines.append(f"# Step: {step.description}\n")
        lines.append(f'print("PIPEFORGE:STEP_START:{step.step_id}", flush=True)\n')
        try:
            lines.append(fn(step))
        except Exception as exc:
            lines.append(f"# ERROR generating step {step.step_id}: {exc}\n")
        lines.append(f'print("PIPEFORGE:STEP_END:{step.step_id}:success", flush=True)\n')
        lines.append("\n")
    return "".join(lines)
