"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env then repository-root .env
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(_BACKEND_DIR / ".env"),
            str(_REPO_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "NyaySetu"
    app_env: str = "development"
    app_debug: bool = False

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        ),
    )
    refresh_token_expire_days: int = Field(default=7, ge=1)

    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("CORS_ORIGINS", "BACKEND_CORS_ORIGINS"),
    )

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, value: str) -> str:
        secret = value.strip()
        if len(secret) < 16:
            raise ValueError("JWT_SECRET must be at least 16 characters")
        return secret

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        if not origins:
            return ["http://localhost:3000"]
        if "*" in origins and self.app_env.lower() == "production":
            raise ValueError("CORS_ORIGINS cannot be '*' in production")
        return origins

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
