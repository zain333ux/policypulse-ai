from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PolicyPulse AI API"
    environment: str = "development"
    analysis_orchestrator: str = "python"
    llm_provider: str | None = None
    frontend_origin: str = "http://localhost:3000,http://127.0.0.1:3000"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    xai_api_key: str | None = None
    xai_model: str = "grok-4.3"
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None
    google_script_url: str | None = None
    google_script_secret: str | None = None
    job_ttl_seconds: int = 3600
    analysis_daily_limit: int = 3
    guest_demo_daily_limit: int = 5
    max_upload_bytes: int = 5 * 1024 * 1024
    max_policy_characters: int = 50_000
    max_comments: int = 500
    max_comment_characters: int = 4_000
    max_total_comment_characters: int = 250_000
    llm_timeout_seconds: float = Field(default=45.0, ge=5, le=120)


@lru_cache
def get_settings() -> Settings:
    return Settings()
