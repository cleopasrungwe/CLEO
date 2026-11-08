
from app.core.config import Settings


def test_default_settings():
    settings = Settings(_env_file=None)

    assert settings.APP_NAME == "CLEO"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"


def test_environment_variables_override_defaults(monkeypatch):
    monkeypatch.setenv("APP_NAME", "CLEO_TEST")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.APP_NAME == "CLEO_TEST"
    assert settings.ENVIRONMENT == "testing"
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"


def test_invalid_environment_is_rejected():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            ENVIRONMENT="invalid",
        )
