from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
import app.models.pipeline   # noqa: F401
import app.models.execution  # noqa: F401
import app.models.user       # noqa: F401
import app.models.schedule   # noqa: F401
from app.api.routes import auth as auth_router
from app.api.routes import sources as sources_router
from app.api.routes import pipelines as pipelines_router
from app.api.routes import executions as executions_router
from app.api.routes import ws as ws_router
from app.api.routes import schedules as schedules_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.services.scheduler import start_scheduler, load_active_schedules
    await start_scheduler()
    await load_active_schedules()

    yield

    from app.services.scheduler import stop_scheduler
    await stop_scheduler()
    await engine.dispose()


app = FastAPI(title="PipeForge API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _catch_all(request: Request, exc: Exception) -> JSONResponse:
    origin = request.headers.get("origin", "")
    allow_origin = origin if origin in settings.cors_origins else settings.cors_origins[0]
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Credentials": "true",
        },
    )


app.include_router(auth_router.router)
app.include_router(sources_router.router)
app.include_router(pipelines_router.router)
app.include_router(executions_router.router)
app.include_router(ws_router.router)
app.include_router(schedules_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
