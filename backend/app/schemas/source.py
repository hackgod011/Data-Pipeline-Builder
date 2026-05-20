from pydantic import BaseModel
from datetime import datetime
from typing import Any


class SchemaColumnOut(BaseModel):
    name: str
    dtype: str
    null_count: int
    unique_count: int
    sample_values: list[Any]


class DataSourceOut(BaseModel):
    id: str
    source_type: str = "file"
    filename: str
    file_type: str
    file_size_bytes: int
    row_count: int | None
    column_count: int | None
    processing_status: str
    processing_progress: int
    processing_error: str | None
    schema_columns: list[SchemaColumnOut] | None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    source_ids: list[str]
    status: str
