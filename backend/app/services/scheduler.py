import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.schedule import Schedule
from app.models.pipeline import Pipeline
from app.models.execution import Execution

_scheduler = AsyncIOScheduler()


async def start_scheduler() -> None:
    _scheduler.start()


async def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)


async def _run_scheduled_execution(schedule_id: str, pipeline_id: str) -> None:
    """Job function: create an execution and run the pipeline code."""
    from app.api.routes.executions import _run_execution  # avoid circular at module level

    async with AsyncSessionLocal() as db:
        pipeline = await db.get(Pipeline, pipeline_id)
        if not pipeline or not pipeline.generated_code:
            return

        execution_id = str(uuid.uuid4())
        exe = Execution(id=execution_id, pipeline_id=pipeline_id, status="pending")
        db.add(exe)

        schedule = await db.get(Schedule, schedule_id)
        if schedule:
            schedule.last_run_at = datetime.now(timezone.utc)
        await db.commit()

    await _run_execution(execution_id, pipeline.generated_code)

    # Update next_run_at after the job fires
    async with AsyncSessionLocal() as db:
        schedule = await db.get(Schedule, schedule_id)
        if schedule:
            job = _scheduler.get_job(schedule_id)
            if job and job.next_run_time:
                schedule.next_run_at = job.next_run_time
            await db.commit()


def _add_job(schedule_id: str, pipeline_id: str, cron_expression: str) -> datetime | None:
    """Register a cron job; return the next_run_time or None."""
    trigger = CronTrigger.from_crontab(cron_expression, timezone="UTC")
    job = _scheduler.add_job(
        _run_scheduled_execution,
        trigger,
        args=[schedule_id, pipeline_id],
        id=schedule_id,
        replace_existing=True,
    )
    return job.next_run_time


def remove_job(schedule_id: str) -> None:
    if _scheduler.get_job(schedule_id):
        _scheduler.remove_job(schedule_id)


def get_next_run(schedule_id: str) -> datetime | None:
    job = _scheduler.get_job(schedule_id)
    return job.next_run_time if job else None


async def load_active_schedules() -> None:
    """On startup: re-register all active schedules from DB."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Schedule).where(Schedule.is_active == True))  # noqa: E712
        schedules = result.scalars().all()
        for s in schedules:
            next_run = _add_job(s.id, s.pipeline_id, s.cron_expression)
            if next_run:
                s.next_run_at = next_run
        await db.commit()


async def upsert_schedule(schedule_id: str, pipeline_id: str, cron_expression: str) -> datetime | None:
    # _add_job is synchronous and fast (just registers with APScheduler in-process)
    return _add_job(schedule_id, pipeline_id, cron_expression)
