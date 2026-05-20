from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class PipelineStep(BaseModel):
    step_id: str
    type: str  # extract | transform | load | validate
    operation: str
    params: dict[str, Any] = Field(default_factory=dict)
    output_alias: str
    description: str
    depends_on: list[str] = Field(default_factory=list)


class PipelinePlan(BaseModel):
    pipeline_id: str
    name: str
    nl_prompt: str
    version: int = 1
    steps: list[PipelineStep]


class ClarifyingResponse(BaseModel):
    clarifying_questions: list[str]


class GenerateRequest(BaseModel):
    nl_prompt: str
    source_ids: list[str]
    pipeline_name: str = "Untitled Pipeline"
    code_mode: str = "pandas"


class GenerateResponse(BaseModel):
    pipeline_id: str
    plan: PipelinePlan | None = None
    generated_code: str | None = None
    clarifying_questions: list[str] = Field(default_factory=list)


class PipelineOut(BaseModel):
    id: str
    name: str
    nl_prompt: str
    plan: PipelinePlan
    generated_code: str | None
    code_mode: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineUpdateRequest(BaseModel):
    plan: PipelinePlan
    code_mode: str = "pandas"
