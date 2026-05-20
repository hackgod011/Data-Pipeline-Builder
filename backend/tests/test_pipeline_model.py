import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.models.pipeline import Pipeline


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(engine)
    async with S() as s:
        yield s
    await engine.dispose()


async def test_create_pipeline(session):
    p = Pipeline(
        id="pipe-001",
        name="Test Pipeline",
        nl_prompt="count rows by region",
        plan_json='{"steps":[]}',
        code_mode="pandas",
        version=1,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    assert p.version == 1
    assert p.created_at is not None
