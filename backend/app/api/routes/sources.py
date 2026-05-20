import json
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, AsyncSessionLocal
from app.models.source import DataSource
from app.models.user import User
from app.schemas.source import DataSourceOut, SchemaColumnOut, UploadResponse
from app.services.schema_detector import detect_schema, get_file_type
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


class DbConnectRequest(BaseModel):
    db_type: str          # "sqlite" | "postgresql"
    connection_string: str
    query: str = "SELECT * FROM main_table LIMIT 1000"
    name: str | None = None

CHUNK_SIZE = 65_536  # 64 KB


async def _stream_to_disk(upload: UploadFile, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with dest.open("wb") as f:
        while chunk := await upload.read(CHUNK_SIZE):
            f.write(chunk)
            total += len(chunk)
    return total


async def _analyze_source(source_id: str, file_path: Path, file_size_bytes: int) -> None:
    async with AsyncSessionLocal() as session:
        source = await session.get(DataSource, source_id)
        if not source:
            return
        source.processing_status = "processing"
        await session.commit()
        try:
            result = detect_schema(
                file_path,
                file_size_bytes=file_size_bytes,
                large_threshold_mb=settings.large_file_threshold_mb,
            )
            source.schema_json = result.to_json()
            source.row_count = result.row_count
            source.column_count = result.column_count
            source.processing_status = "ready"
            source.processing_progress = 100
        except Exception as exc:
            source.processing_status = "error"
            source.processing_error = str(exc)
        await session.commit()


def _source_to_out(source: DataSource) -> DataSourceOut:
    schema_columns = None
    if source.schema_json:
        raw = json.loads(source.schema_json)
        schema_columns = [SchemaColumnOut(**c) for c in raw]
    return DataSourceOut(
        id=source.id,
        filename=source.filename,
        file_type=source.file_type,
        file_size_bytes=source.file_size_bytes,
        row_count=source.row_count,
        column_count=source.column_count,
        processing_status=source.processing_status,
        processing_progress=source.processing_progress,
        processing_error=source.processing_error,
        schema_columns=schema_columns,
        uploaded_at=source.uploaded_at,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_sources(
    files: list[UploadFile],
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    source_ids: list[str] = []
    for upload in files:
        try:
            file_type = get_file_type(Path(upload.filename or "unknown"))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {upload.filename}",
            )

        source_id = str(uuid.uuid4())
        dest = settings.upload_dir / source_id / (upload.filename or "file")
        file_size = await _stream_to_disk(upload, dest)

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_bytes:
            dest.unlink(missing_ok=True)
            raise HTTPException(
                status_code=413,
                detail=f"'{upload.filename}' exceeds the {settings.max_upload_size_mb} MB upload limit",
            )

        source = DataSource(
            id=source_id,
            user_id=current_user.id,
            filename=upload.filename or "file",
            file_type=file_type,
            file_path=str(dest),
            file_size_bytes=file_size,
            processing_status="pending",
        )
        db.add(source)
        source_ids.append(source_id)

        background_tasks.add_task(_analyze_source, source_id, dest, file_size)

    await db.commit()
    return UploadResponse(source_ids=source_ids, status="processing")


@router.get("", response_model=list[DataSourceOut])
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(DataSource)
        .where(DataSource.user_id == current_user.id)
        .order_by(DataSource.uploaded_at.desc())
    )
    return [_source_to_out(s) for s in result.scalars().all()]


@router.get("/{source_id}", response_model=DataSourceOut)
async def get_source(
    source_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    source = await db.get(DataSource, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_to_out(source)


@router.get("/{source_id}/preview")
async def preview_source(
    source_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    source = await db.get(DataSource, source_id)
    if not source or source.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.processing_status != "ready":
        raise HTTPException(status_code=425, detail="Source is still processing")

    from app.services.schema_detector import _read_pandas

    file_type = source.file_type
    df = _read_pandas(Path(source.file_path), file_type)
    preview = df.head(100).fillna("").to_dict(orient="records")
    return {"columns": list(df.columns), "rows": preview, "total_rows": source.row_count}


@router.post("/connect", response_model=UploadResponse)
async def connect_database(
    req: DbConnectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Connect to an external database, run a query, and register the result as a DataSource."""
    import asyncio as _asyncio
    from app.services.db_connector import query_database
    from app.services.schema_detector import SchemaResult, SchemaColumn

    try:
        loop = _asyncio.get_running_loop()
        df = await loop.run_in_executor(
            None, lambda: query_database(req.db_type, req.connection_string, req.query)
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Database connection failed: {exc}")

    # Save the DataFrame as a CSV so the pipeline executor can read it
    source_id = str(uuid.uuid4())
    safe_name = req.name or f"{req.db_type}_query"
    filename = f"{safe_name}.csv"
    dest_dir = settings.upload_dir / source_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    df.to_csv(dest, index=False)

    # Build schema from the in-memory DataFrame (no need for a second disk pass)
    columns: list[SchemaColumn] = []
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique())
        sample = series.dropna().head(5).tolist()
        columns.append(SchemaColumn(
            name=str(col),
            dtype=str(series.dtype),
            null_count=null_count,
            unique_count=unique_count,
            sample_values=sample,
        ))

    schema_result = SchemaResult(
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
    )

    source = DataSource(
        id=source_id,
        user_id=current_user.id,
        source_type="database",
        filename=filename,
        file_type="csv",
        file_path=str(dest),
        file_size_bytes=dest.stat().st_size,
        connection_string=req.connection_string,
        db_query=req.query,
        schema_json=schema_result.to_json(),
        row_count=schema_result.row_count,
        column_count=schema_result.column_count,
        processing_status="ready",
        processing_progress=100,
    )
    db.add(source)
    await db.commit()

    return UploadResponse(source_ids=[source_id], status="ready")
