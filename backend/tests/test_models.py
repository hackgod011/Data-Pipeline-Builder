import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.models.source import DataSource


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine)
    async with SessionLocal() as s:
        yield s
    await engine.dispose()


async def test_create_data_source(session):
    source = DataSource(
        id="test-id-123",
        filename="sales.csv",
        file_type="csv",
        file_path="uploads/test-id-123/sales.csv",
        file_size_bytes=1024,
        processing_status="pending",
        processing_progress=0,
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    assert source.id == "test-id-123"
    assert source.processing_status == "pending"
    assert source.uploaded_at is not None
