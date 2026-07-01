from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "local"
    log_level: str = "INFO"
    research_store: str = "memory"
    llm_provider: str = "mock"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5435/research_workspace"
    redis_url: str = "redis://localhost:6382/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
