from app.core.config import settings


def test_settings_have_defaults():
    assert settings.large_file_threshold_mb == 10
    assert settings.execution_timeout_seconds == 60
    assert "sqlite" in settings.database_url
