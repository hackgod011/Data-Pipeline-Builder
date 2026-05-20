from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import pandas as pd
import duckdb


EXTENSION_TO_TYPE: dict[str, str] = {
    ".csv": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".json": "json",
    ".parquet": "parquet",
}

LARGE_FILE_TYPES = {"csv", "json", "parquet"}


@dataclass
class SchemaColumn:
    name: str
    dtype: str
    null_count: int
    unique_count: int
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class SchemaResult:
    columns: list[SchemaColumn]
    row_count: int
    column_count: int

    def to_json(self) -> str:
        return json.dumps(
            [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "null_count": c.null_count,
                    "unique_count": c.unique_count,
                    "sample_values": [str(v) for v in c.sample_values],
                }
                for c in self.columns
            ]
        )


def get_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in EXTENSION_TO_TYPE:
        raise ValueError(f"Unsupported file extension: {ext}")
    return EXTENSION_TO_TYPE[ext]


def _duckdb_read_expr(path: Path, file_type: str) -> str:
    p = str(path).replace("\\", "/")
    if file_type == "csv":
        return f"read_csv_auto('{p}')"
    if file_type == "parquet":
        return f"read_parquet('{p}')"
    if file_type == "json":
        return f"read_json_auto('{p}')"
    raise ValueError(f"DuckDB does not support: {file_type}")


def _detect_large(path: Path, file_type: str) -> SchemaResult:
    con = duckdb.connect()
    tbl = _duckdb_read_expr(path, file_type)

    row_count: int = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    describe = con.execute(f"DESCRIBE SELECT * FROM {tbl}").df()

    columns: list[SchemaColumn] = []
    for _, row in describe.iterrows():
        col = row["column_name"]
        dtype = str(row["column_type"])
        stats = con.execute(
            f'SELECT COUNT(*) - COUNT("{col}") AS nc, '
            f'COUNT(DISTINCT "{col}") AS uc FROM {tbl}'
        ).fetchone()
        samples = con.execute(
            f'SELECT "{col}" FROM {tbl} WHERE "{col}" IS NOT NULL LIMIT 5'
        ).fetchall()
        columns.append(
            SchemaColumn(
                name=col,
                dtype=dtype,
                null_count=int(stats[0]),
                unique_count=int(stats[1]),
                sample_values=[str(s[0]) for s in samples],
            )
        )
    con.close()
    return SchemaResult(columns=columns, row_count=row_count, column_count=len(columns))


def _read_pandas(path: Path, file_type: str) -> pd.DataFrame:
    if file_type == "csv":
        return pd.read_csv(path)
    if file_type == "excel":
        return pd.read_excel(path, engine="openpyxl")
    if file_type == "json":
        return pd.read_json(path)
    if file_type == "parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported: {file_type}")


def _detect_small(path: Path, file_type: str) -> SchemaResult:
    df = _read_pandas(path, file_type)
    columns: list[SchemaColumn] = []
    for col in df.columns:
        series = df[col]
        samples = [str(v) for v in series.dropna().head(5).tolist()]
        columns.append(
            SchemaColumn(
                name=str(col),
                dtype=str(series.dtype),
                null_count=int(series.isna().sum()),
                unique_count=int(series.nunique()),
                sample_values=samples,
            )
        )
    return SchemaResult(
        columns=columns, row_count=len(df), column_count=len(df.columns)
    )


def detect_schema(
    path: Path,
    file_size_bytes: int,
    large_threshold_mb: int = 10,
) -> SchemaResult:
    file_type = get_file_type(path)
    threshold = large_threshold_mb * 1024 * 1024
    if file_size_bytes >= threshold and file_type in LARGE_FILE_TYPES:
        return _detect_large(path, file_type)
    return _detect_small(path, file_type)
