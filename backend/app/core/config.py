from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings validated via pydantic-settings.
    Loads from environment variables or .env file.
    """

    APP_NAME: str = "BetterLife"
    APP_DESCRIPTION: str = "BetterLife - Comprehensive AI-Powered Blood Report & Health Insights"
    APP_ICON: str = "🌱"
    APP_TAGLINE: str = "Discover a Better, Healthier You with AI"
    ENVIRONMENT: str = Field(
        default="development", description="Environment: development, test, production"
    )
    DEBUG: bool = False

    # Application Limits
    MAX_UPLOAD_SIZE_MB: int = Field(default=20, ge=1, le=100)
    MAX_PDF_PAGES: int = Field(default=50, ge=1, le=200)
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, ge=5, le=1440)
    ANALYSIS_DAILY_LIMIT: int = Field(default=15, ge=1, le=500)

    # Ollama Settings (Self-hosted model endpoint)
    OLLAMA_BASE_URL: str = Field(default="https://ollama.calmalpha.in")
    OLLAMA_PRIMARY_MODEL: str = "gemma4:e4b"
    OLLAMA_FALLBACK_MODELS: str = "phi4-mini:latest,granite4.1:3b,qwen3.5:4b-mlx"

    # Supabase Auth & Database Settings (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Database
    DATABASE_URL: str = Field(
        default="",
        description="Database connection URL",
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            db_path = Path(__file__).resolve().parent.parent.parent / "betterlife_platform.db"
            return f"sqlite:///{db_path}"
        return v

    # Security & CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    SECRET_KEY: str = Field(
        default="betterlife-dev-insecure-secret-key-change-in-production", min_length=16
    )

    # UI Theme
    PRIMARY_COLOR: str = "#0ea5e9"
    SECONDARY_COLOR: str = "#0284c7"

    @property
    def fallback_models_list(self) -> list[str]:
        return [m.strip() for m in self.OLLAMA_FALLBACK_MODELS.split(",") if m.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
