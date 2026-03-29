from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "AI DD API"
    environment: str = "development"

    # Database — PostgreSQL (shared across all modules)
    database_url: str = "postgresql+psycopg://aidd:aidd_dev_pass@localhost:5432/aidd"

    # Auth — JWT
    secret_key: str = "change-this-to-a-random-32-char-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # AI — Groq API (llama-3.3-70b-versatile, free tier)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Async Queue — Celery + Redis (Upstash free tier)
    redis_url: str = "redis://localhost:6379/0"

    # Storage — local filesystem for dev, GCS for prod
    upload_dir: str = "uploads"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
