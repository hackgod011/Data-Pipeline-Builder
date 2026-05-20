from pydantic import BaseModel
from datetime import datetime
from typing import Any


class StepLog(BaseModel):
    step_id: str
    status: str
    start_time: str | None = None
    end_time: str | None = None
    rows_in: int | None = None
    rows_out: int | None = None
    message: str = ""


class ColumnProfile(BaseModel):
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
    sample_values: list[Any] = []


class ProfileResult(BaseModel):
    row_count: int
    column_count: int
    quality_score: int
    columns: list[ColumnProfile]


class ExecutionOut(BaseModel):
    id: str
    pipeline_id: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    step_logs: list[StepLog] | None
    output_file_path: str | None
    output_profile: ProfileResult | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogMessage(BaseModel):
    type: str  # log | status | step_status | error
    timestamp: str
    step_id: str | None = None
    message: str = ""
    status: str | None = None
    rows_in: int | None = None
    rows_out: int | None = None
