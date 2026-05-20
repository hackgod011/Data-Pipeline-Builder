from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    min: Any | None = None
    max: Any | None = None
    mean: float | None = None
    std: float | None = None
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class ProfileResult:
    row_count: int
    column_count: int
    quality_score: int  # 0–100; 100 - average_null_pct across all columns
    columns: list[ColumnProfile]


def _to_python(val: Any) -> Any:
    """Convert numpy scalars to native Python so they are JSON-serializable."""
    if val is None:
        return None
    try:
        return val.item()  # numpy scalar → Python scalar
    except AttributeError:
        return val


def profile_file(path: Path) -> ProfileResult:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in {".parquet", ".pq"}:
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Cannot profile file type: {suffix}")

    row_count = len(df)
    column_count = len(df.columns)
    columns: list[ColumnProfile] = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = round(null_count / row_count * 100, 1) if row_count > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        unique_pct = round(unique_count / row_count * 100, 1) if row_count > 0 else 0.0

        min_val = max_val = mean_val = std_val = None
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                min_val = round(float(non_null.min()), 4)
                max_val = round(float(non_null.max()), 4)
                mean_val = round(float(non_null.mean()), 4)
                std_val = round(float(non_null.std()), 4) if len(non_null) > 1 else 0.0

        sample_values = [_to_python(v) for v in series.dropna().head(5).tolist()]

        columns.append(ColumnProfile(
            name=str(col),
            dtype=str(series.dtype),
            null_count=null_count,
            null_pct=null_pct,
            unique_count=unique_count,
            unique_pct=unique_pct,
            min=min_val,
            max=max_val,
            mean=mean_val,
            std=std_val,
            sample_values=sample_values,
        ))

    avg_null_pct = sum(c.null_pct for c in columns) / len(columns) if columns else 0.0
    quality_score = max(0, min(100, round(100 - avg_null_pct)))

    return ProfileResult(
        row_count=row_count,
        column_count=column_count,
        quality_score=quality_score,
        columns=columns,
    )
