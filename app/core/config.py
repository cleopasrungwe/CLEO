from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the CLEO application."""

    APP_NAME: str = "CLEO"
    APP_DESCRIPTION: str = "Cognitive Logic & Executive Operator"
    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    DEBUG: bool = False

    LOG_LEVEL: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    # Database configuration
    DATABASE_URL: str = "sqlite:///./cleo.db"

    # AI provider configuration
    AI_PROVIDER: Literal["openai", "local"] = "openai"

    OPENAI_API_KEY: str = ""

    OPENAI_MODEL: str = "gpt-5.5"

    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3.2:3b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Shared settings instance used throughout CLEO
settings = Settings()