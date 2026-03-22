import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class Environment(str, Enum):
    LOCAL = "local"
    PROD = "prod"


_env = os.getenv("APP_ENV", "local")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{_env}",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    environment: Environment = Environment.LOCAL
    debug: bool = False
    app_name: str = "Centro de Actividades API"

    # Database
    database_url: str

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30


settings = Settings()
