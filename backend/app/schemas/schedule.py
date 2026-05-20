from pydantic import BaseModel
from datetime import datetime


class ScheduleCreate(BaseModel):
    cron_expression: str


class ScheduleOut(BaseModel):
    id: str
    pipeline_id: str
    pipeline_name: str | None = None
    cron_expression: str
    is_active: bool
    created_at: datetime
    last_run_at: datetime | None
    next_run_at: datetime | None

    model_config = {"from_attributes": True}
