from pydantic_settings import BaseSettings
from pathlib import Path

# Resolve .env from the project root (two levels up from this file: backend/app/core/ → root)
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./pipeforge.db"
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")
    max_upload_size_mb: int = 1000
    execution_timeout_seconds: int = 60
    large_file_threshold_mb: int = 10

    # LLM — set the key matching your chosen provider
    llm_model: str = "gemini/gemini-2.0-flash-lite"  # change prefix to switch provider
    gemini_api_key: str = ""        # gemini/...  models
    groq_api_key: str = ""          # groq/...    models  (free tier, recommended)
    anthropic_api_key: str = ""     # claude-...  models
    openrouter_api_key: str = ""    # openrouter/... models

    # CORS — comma-separated in env: CORS_ORIGINS=http://localhost:5173,https://myapp.com
    cors_origins: list[str] = ["http://localhost:5173"]

    # Auth (Phase 5)
    secret_key: str = "dev-secret-change-in-production"
    encryption_key: str = ""
    access_token_expire_minutes: int = 60

    model_config = {
        "env_file": str(_ROOT_ENV),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
