import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear in-memory rate-limit counters before every test so tests don't bleed into each other."""
    from app.core.limiter import limiter
    storage = getattr(limiter, "_storage", None)
    if storage and hasattr(storage, "reset"):
        storage.reset()
    yield


@pytest.fixture
async def auth_client(tmp_path, monkeypatch):
    """Isolated client with real auth stack — no dependency overrides."""
    from app.core import config as cfg
    monkeypatch.setattr(cfg.settings, "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(cfg.settings, "output_dir", tmp_path / "outputs")
    (tmp_path / "uploads").mkdir()
    (tmp_path / "outputs").mkdir()

    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    import app.api.routes.sources as sources_mod
    import app.api.routes.executions as executions_mod
    import app.api.routes.ws as ws_mod
    import app.core.database as db_mod
    import app.services.scheduler as scheduler_mod
    monkeypatch.setattr(sources_mod, "AsyncSessionLocal", Session)
    monkeypatch.setattr(executions_mod, "AsyncSessionLocal", Session)
    monkeypatch.setattr(ws_mod, "AsyncSessionLocal", Session)
    monkeypatch.setattr(db_mod, "AsyncSessionLocal", Session)
    monkeypatch.setattr(scheduler_mod, "AsyncSessionLocal", Session)

    async def override_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "Secure123",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "alice@example.com"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_client: AsyncClient):
    payload = {"email": "bob@example.com", "password": "Secure123"}
    await auth_client.post("/api/v1/auth/register", json=payload)
    r = await auth_client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_password_too_short(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "Ab1",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_uppercase(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/register", json={
        "email": "nocase@example.com",
        "password": "alllower1",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_password_no_digit(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/register", json={
        "email": "nodigit@example.com",
        "password": "NoDigitHere",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Secure123",
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "email": "carol@example.com",
        "password": "Secure123",
    })
    r = await auth_client.post("/api/v1/auth/login", json={
        "email": "carol@example.com",
        "password": "Secure123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "email": "dave@example.com",
        "password": "Secure123",
    })
    r = await auth_client.post("/api/v1/auth/login", json={
        "email": "dave@example.com",
        "password": "WrongPass9",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "Secure123",
    })
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# /me — protected endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_with_valid_token(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "email": "eve@example.com",
        "password": "Secure123",
    })
    login = await auth_client.post("/api/v1/auth/login", json={
        "email": "eve@example.com",
        "password": "Secure123",
    })
    token = login.json()["access_token"]
    r = await auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "eve@example.com"


@pytest.mark.asyncio
async def test_me_without_token(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(auth_client: AsyncClient):
    r = await auth_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bogus.token.here"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(auth_client: AsyncClient):
    await auth_client.post("/api/v1/auth/register", json={
        "email": "frank@example.com",
        "password": "Secure123",
    })
    login = await auth_client.post("/api/v1/auth/login", json={
        "email": "frank@example.com",
        "password": "Secure123",
    })
    refresh_token = login.json()["refresh_token"]
    r = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_rejected(auth_client: AsyncClient):
    """Passing an access token to the refresh endpoint must be rejected."""
    await auth_client.post("/api/v1/auth/register", json={
        "email": "grace@example.com",
        "password": "Secure123",
    })
    login = await auth_client.post("/api/v1/auth/login", json={
        "email": "grace@example.com",
        "password": "Secure123",
    })
    access_token = login.json()["access_token"]
    r = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(auth_client: AsyncClient):
    r = await auth_client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage"})
    assert r.status_code == 401
