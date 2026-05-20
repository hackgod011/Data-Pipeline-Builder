import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.pipeline import Pipeline, PipelineVersion
from app.models.source import DataSource
from app.models.user import User
from app.schemas.pipeline import (
    GenerateRequest, GenerateResponse, PipelineOut, PipelinePlan, PipelineUpdateRequest,
)
from app.services.code_generator import generate_code, generate_sql_code
from app.services.nl_parser import parse_nl_to_plan

router = APIRouter(prefix="/api/v1/pipelines", tags=["pipelines"])


def _build_schema_context(sources: list[DataSource]) -> list[dict]:
    context = []
    for src in sources:
        if not src.schema_json:
            continue
        cols = json.loads(src.schema_json)
        context.append({"name": src.filename, "columns": cols})
    return context


def _pipeline_to_out(pipeline: Pipeline) -> PipelineOut:
    return PipelineOut(
        id=pipeline.id,
        name=pipeline.name,
        nl_prompt=pipeline.nl_prompt,
        plan=PipelinePlan(**json.loads(pipeline.plan_json)),
        generated_code=pipeline.generated_code,
        code_mode=pipeline.code_mode,
        version=pipeline.version,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_pipeline(
    req: GenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sources = []
    for sid in req.source_ids:
        src = await db.get(DataSource, sid)
        if not src or src.user_id != current_user.id:
            raise HTTPException(status_code=404, detail=f"Source {sid} not found")
        sources.append(src)

    try:
        schema_context = _build_schema_context(sources)
        pipeline_id = str(uuid.uuid4())
        result = await parse_nl_to_plan(
            nl_prompt=req.nl_prompt,
            schema_context=schema_context,
            pipeline_id=pipeline_id,
            pipeline_name=req.pipeline_name,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pipeline generation failed: {exc}") from exc

    if isinstance(result, list):
        return GenerateResponse(
            pipeline_id=pipeline_id,
            clarifying_questions=result,
        )

    plan: PipelinePlan = result
    mode = req.code_mode if req.code_mode in {"pandas", "sql"} else "pandas"
    code = generate_sql_code(plan) if mode == "sql" else generate_code(plan)

    pipeline = Pipeline(
        id=pipeline_id,
        user_id=current_user.id,
        name=plan.name,
        nl_prompt=req.nl_prompt,
        plan_json=plan.model_dump_json(),
        generated_code=code,
        code_mode=mode,
        version=1,
    )
    db.add(pipeline)
    await db.commit()

    return GenerateResponse(
        pipeline_id=pipeline_id,
        plan=plan,
        generated_code=code,
    )


@router.get("", response_model=list[PipelineOut])
async def list_pipelines(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Pipeline)
        .where(Pipeline.user_id == current_user.id)
        .order_by(Pipeline.created_at.desc())
    )
    return [_pipeline_to_out(p) for p in result.scalars().all()]


@router.get("/{pipeline_id}", response_model=PipelineOut)
async def get_pipeline(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await db.get(Pipeline, pipeline_id)
    if not p or p.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return _pipeline_to_out(p)


@router.put("/{pipeline_id}", response_model=PipelineOut)
async def update_pipeline(
    pipeline_id: str,
    req: PipelineUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await db.get(Pipeline, pipeline_id)
    if not p or p.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    version = PipelineVersion(
        id=str(uuid.uuid4()),
        pipeline_id=pipeline_id,
        version=p.version,
        plan_json=p.plan_json,
        generated_code=p.generated_code,
    )
    db.add(version)

    mode = req.code_mode if req.code_mode in {"pandas", "sql"} else "pandas"
    code = generate_sql_code(req.plan) if mode == "sql" else generate_code(req.plan)
    p.plan_json = req.plan.model_dump_json()
    p.generated_code = code
    p.code_mode = mode
    p.version += 1
    await db.commit()
    await db.refresh(p)
    return _pipeline_to_out(p)


@router.get("/{pipeline_id}/code")
async def get_pipeline_code(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await db.get(Pipeline, pipeline_id)
    if not p or p.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"code": p.generated_code or "", "mode": p.code_mode}


@router.get("/{pipeline_id}/export")
async def export_pipeline_script(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await db.get(Pipeline, pipeline_id)
    if not p or p.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    filename = f"pipeline_{pipeline_id[:8]}.py"
    return Response(
        content=p.generated_code or "",
        media_type="text/x-python",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{pipeline_id}/versions")
async def get_pipeline_versions(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    p = await db.get(Pipeline, pipeline_id)
    if not p or p.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    result = await db.execute(
        select(PipelineVersion)
        .where(PipelineVersion.pipeline_id == pipeline_id)
        .order_by(PipelineVersion.version.desc())
    )
    versions = result.scalars().all()
    return [
        {"id": v.id, "version": v.version, "created_at": v.created_at}
        for v in versions
    ]
