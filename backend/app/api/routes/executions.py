import asyncio
import dataclasses
import glob
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import AsyncSessionLocal, get_db
from app.models.execution import Execution
from app.models.pipeline import Pipeline
from app.models.user import User
from app.schemas.execution import ExecutionOut, ProfileResult, StepLog
from app.services.executor import run_pipeline_code
from app.services.profiler import profile_file

router = APIRouter(tags=["executions"])

# In-memory WebSocket subscriber registry: execution_id → list[asyncio.Queue]
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
LOG_BUFFER_MAX = 500


def subscribe(execution_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[execution_id].append(q)
    return q


def unsubscribe(execution_id: str, q: asyncio.Queue) -> None:
    try:
        _subscribers[execution_id].remove(q)
    except ValueError:
        pass


async def _broadcast(execution_id: str, msg: dict) -> None:
    for q in list(_subscribers.get(execution_id, [])):
        await q.put(msg)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_and_build_step_events(stdout: str) -> list[dict]:
    """Parse PIPEFORGE step markers from subprocess stdout into broadcast events."""
    started: dict[str, bool] = {}
    events: list[dict] = []

    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("PIPEFORGE:STEP_START:"):
            step_id = line[len("PIPEFORGE:STEP_START:"):]
            started[step_id] = True
            events.append({"step_id": step_id, "status": "running"})
        elif line.startswith("PIPEFORGE:STEP_END:"):
            parts = line.split(":", 3)
            if len(parts) == 4:
                step_id, status = parts[2], parts[3]
                started.pop(step_id, None)
                events.append({"step_id": step_id, "status": status})

    # Steps that started but never finished → failed
    for step_id in started:
        events.append({"step_id": step_id, "status": "failed"})

    return events


async def _run_execution(execution_id: str, code: str) -> None:
    """Background task: run code, broadcast step events, update DB, run profiler."""
    async with AsyncSessionLocal() as db:
        exe = await db.get(Execution, execution_id)
        if not exe:
            return
        exe.status = "running"
        exe.started_at = datetime.now(timezone.utc)
        await db.commit()

    await _broadcast(execution_id, {
        "type": "status",
        "timestamp": _now(),
        "status": "running",
        "message": "Execution started",
    })

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: run_pipeline_code(
            code,
            timeout=settings.execution_timeout_seconds,
            output_dir=settings.output_dir,
        ),
    )

    # Broadcast per-step status events parsed from stdout
    step_events = _parse_and_build_step_events(result.stdout)
    for ev in step_events:
        await _broadcast(execution_id, {
            "type": "step_status",
            "timestamp": _now(),
            "step_id": ev["step_id"],
            "status": ev["status"],
            "message": f"Step {ev['step_id']}: {ev['status']}",
        })

    log_lines = (result.stdout + "\n" + result.stderr).strip().splitlines()
    # Strip internal PIPEFORGE markers from the visible log buffer
    visible_lines = [line for line in log_lines if not line.startswith("PIPEFORGE:")]
    log_buffer = "\n".join(visible_lines[-LOG_BUFFER_MAX:])

    # Run data quality profiler on the output file if execution succeeded
    profile_json: str | None = None
    output_file_path: str | None = None

    if result.status == "success":
        output_dir_str = str(settings.output_dir)
        outputs = (
            glob.glob(os.path.join(output_dir_str, "*.csv"))
            + glob.glob(os.path.join(output_dir_str, "*.parquet"))
        )
        if outputs:
            output_file_path = max(outputs, key=os.path.getmtime)
            try:
                profile = await loop.run_in_executor(
                    None, lambda: profile_file(Path(output_file_path))
                )
                profile_json = json.dumps(dataclasses.asdict(profile))
            except Exception:
                pass  # profiler failure is non-fatal

    async with AsyncSessionLocal() as db:
        exe = await db.get(Execution, execution_id)
        if not exe:
            return
        exe.status = result.status
        exe.completed_at = datetime.now(timezone.utc)
        exe.error_message = result.error_message or None
        exe.log_buffer = log_buffer
        exe.output_file_path = output_file_path
        exe.output_profile_json = profile_json
        await db.commit()

    await _broadcast(execution_id, {
        "type": "status",
        "timestamp": _now(),
        "status": result.status,
        "message": result.error_message or "Execution completed successfully",
    })


@router.post("/api/v1/pipelines/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    if not pipeline.generated_code:
        raise HTTPException(status_code=400, detail="Pipeline has no generated code")

    execution_id = str(uuid.uuid4())
    exe = Execution(id=execution_id, pipeline_id=pipeline_id, status="pending")
    db.add(exe)
    await db.commit()

    asyncio.create_task(_run_execution(execution_id, pipeline.generated_code))

    return {"execution_id": execution_id, "status": "pending"}


@router.get("/api/v1/executions/{execution_id}", response_model=ExecutionOut)
async def get_execution(
    execution_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    exe = await db.get(Execution, execution_id)
    if not exe:
        raise HTTPException(status_code=404, detail="Execution not found")
    # Verify ownership via pipeline
    pipeline = await db.get(Pipeline, exe.pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    step_logs = None
    if exe.step_logs_json:
        step_logs = [StepLog(**s) for s in json.loads(exe.step_logs_json)]
    profile = None
    if exe.output_profile_json:
        profile = ProfileResult(**json.loads(exe.output_profile_json))
    return ExecutionOut(
        id=exe.id,
        pipeline_id=exe.pipeline_id,
        status=exe.status,
        started_at=exe.started_at,
        completed_at=exe.completed_at,
        error_message=exe.error_message,
        step_logs=step_logs,
        output_file_path=exe.output_file_path,
        output_profile=profile,
        created_at=exe.created_at,
    )


@router.get("/api/v1/executions/{execution_id}/profile", response_model=ProfileResult)
async def get_execution_profile(
    execution_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    exe = await db.get(Execution, execution_id)
    if not exe:
        raise HTTPException(status_code=404, detail="Execution not found")
    pipeline = await db.get(Pipeline, exe.pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")
    if not exe.output_profile_json:
        raise HTTPException(status_code=404, detail="No profile available for this execution")
    return ProfileResult(**json.loads(exe.output_profile_json))


@router.get("/api/v1/outputs/{filename}")
async def download_output(
    filename: str,
    _current_user: Annotated[User, Depends(get_current_user)],
):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = settings.output_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(str(path), filename=filename, media_type="application/octet-stream")


@router.get("/api/v1/pipelines/{pipeline_id}/executions")
async def list_pipeline_executions(
    pipeline_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    pipeline = await db.get(Pipeline, pipeline_id)
    if not pipeline or pipeline.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    result = await db.execute(
        select(Execution)
        .where(Execution.pipeline_id == pipeline_id)
        .order_by(Execution.created_at.desc())
    )
    exes = result.scalars().all()
    return [
        {
            "id": e.id,
            "status": e.status,
            "created_at": e.created_at,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
        }
        for e in exes
    ]
