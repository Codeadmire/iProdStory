"""
Central application settings loaded from environment variables.
All secrets and infra URLs live here — never hardcoded elsewhere.
"""
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "Product Marketing AI"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = False

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/prodmarketing"
    DATABASE_URL_UNPOOLED: str = ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_postgres_dialect(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # ── Redis / Celery ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── Object Storage ────────────────────────────────────────────────────
    STORAGE_BACKEND: str = "local"        # "local" | "s3"
    LOCAL_STORAGE_PATH: str = "./media"
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""             # MinIO compat: e.g. http://minio:9000
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    MEDIA_BASE_URL: str = "http://localhost:8000/media"

    # ── AI ────────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    DEFAULT_AI_MODEL: str = "gemini-1.5-flash-latest"

    # ── LinkedIn OAuth ────────────────────────────────────────────────────
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:3000/auth/linkedin/callback"
    LINKEDIN_SCOPE: str = "openid profile email w_member_social"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ── Rate Limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # ── Crawl Defaults ────────────────────────────────────────────────────
    CRAWL_MAX_PAGES_DEFAULT: int = 50
    CRAWL_MAX_DEPTH_DEFAULT: int = 3
    CRAWL_TIMEOUT_MS: int = 30_000

    # ── Monitoring ────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env.local", ".env.local"), 
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
