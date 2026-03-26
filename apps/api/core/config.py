from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "AI DD API"
    environment: str = "development"

    # Database
    database_url: str = "postgresql+psycopg://aidd:aidd_dev_pass@localhost:5432/aidd"

    # Auth
    secret_key: str = "change-this-to-a-random-32-char-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    # Google Cloud — EU only, non-negotiable
    google_cloud_project: str = ""
    google_cloud_region: str = "europe-west3"
    gcs_bucket_name: str = "aidd-documents-dev"
    vertex_ai_location: str = "europe-west3"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
