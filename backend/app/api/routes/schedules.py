import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.pipeline import Pipeline
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleOut
from app.services.scheduler import remove_job, upsert_schedule

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


def _schedule_to_out(s: Schedule, pipeline_name: str | None = None) -> ScheduleOut:
    return ScheduleOut(
        id=s.id,
        pipeline_id=s.pipeline_id,
        pipeline_name=pipeline_name,
        cron_expression=s.cron_expression,
        is_active=s.is_active,
        created_at=s.created_at,
        last_run_at=s.last_run_at,
        next_run_at=s.next_run_at,
    )


@router.put("/pipelines/{pipeline_id}", response_model=ScheduleOut)
async def upsert_pipeline_schedule(
    pipeline_id: str,
    body: ScheduleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Check for an existing schedule on this pipeline for this user
    result = await db.execute(
        select(Schedule)
        .where(Schedule.pipeline_id == pipeline_id, Schedule.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()

    if schedule:
        schedule.cron_expression = body.cron_expression
        schedule.is_active = True
    else:
        schedule = Schedule(
            id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            cron_expression=body.cron_expression,
            is_active=True,
        )
        db.add(schedule)
        await db.flush()

    next_run = await upsert_schedule(schedule.id, pipeline_id, body.cron_expression)
    schedule.next_run_at = next_run
    await db.commit()
    await db.refresh(schedule)
    return _schedule_to_out(schedule, pipeline.name)


@router.delete("/pipelines/{pipeline_id}", status_code=204)
async def delete_pipeline_schedule(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Schedule)
        .where(Schedule.pipeline_id == pipeline_id, Schedule.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found for this pipeline")
    remove_job(schedule.id)
    await db.delete(schedule)
    await db.commit()


@router.get("/pipelines/{pipeline_id}", response_model=ScheduleOut)
async def get_pipeline_schedule(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    result = await db.execute(
        select(Schedule)
        .where(Schedule.pipeline_id == pipeline_id, Schedule.user_id == current_user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found for this pipeline")
    return _schedule_to_out(schedule, pipeline.name)


@router.get("", response_model=list[ScheduleOut])
async def list_schedules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Schedule).where(Schedule.user_id == current_user.id).order_by(Schedule.created_at.desc())
    )
    schedules = result.scalars().all()
    out = []
    for s in schedules:
        p = await db.get(Pipeline, s.pipeline_id)
        out.append(_schedule_to_out(s, p.name if p else None))
    return out


@router.patch("/{schedule_id}/toggle", response_model=ScheduleOut)
async def toggle_schedule(
    schedule_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    schedule = await db.get(Schedule, schedule_id)
    if not schedule or schedule.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.is_active = not schedule.is_active
    if schedule.is_active:
        next_run = await upsert_schedule(schedule.id, schedule.pipeline_id, schedule.cron_expression)
        schedule.next_run_at = next_run
    else:
        remove_job(schedule.id)
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    p = await db.get(Pipeline, schedule.pipeline_id)
    return _schedule_to_out(schedule, p.name if p else None)
