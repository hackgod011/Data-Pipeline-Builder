import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.models.user import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Stable test user returned by the overridden get_current_user dep
_TEST_USER = User(
    id="test-user-id",
    email="test@pipeforge.dev",
    password_hash="$2b$12$irrelevant",
    is_active=True,
)


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with Session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine, db_session, tmp_path, monkeypatch):
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(cfg.settings, "output_dir", tmp_path / "outputs")
    (tmp_path / "uploads").mkdir()
    (tmp_path / "outputs").mkdir()

    # Patch AsyncSessionLocal in all routes modules so background tasks
    # use the same in-memory DB as the test session.
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    import app.api.routes.sources as sources_mod
    import app.api.routes.executions as executions_mod
    import app.api.routes.ws as ws_mod
    import app.core.database as db_mod
    import app.services.scheduler as scheduler_mod
    monkeypatch.setattr(sources_mod, "AsyncSessionLocal", test_session_factory)
    monkeypatch.setattr(executions_mod, "AsyncSessionLocal", test_session_factory)
    monkeypatch.setattr(ws_mod, "AsyncSessionLocal", test_session_factory)
    monkeypatch.setattr(db_mod, "AsyncSessionLocal", test_session_factory)
    monkeypatch.setattr(scheduler_mod, "AsyncSessionLocal", test_session_factory)

    async def override_db():
        yield db_session

    async def override_current_user():
        # Ensure the test user exists in the in-memory DB
        existing = await db_session.get(User, _TEST_USER.id)
        if not existing:
            db_session.add(_TEST_USER)
            await db_session.commit()
        return _TEST_USER

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
