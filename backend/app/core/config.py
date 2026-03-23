import os
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Render / Git
    render_git_commit: Optional[str] = "development"
    render_git_branch: Optional[str] = "local"
    # Se setea al momento de iniciar la app en el servidor
    deploy_timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Database
    database_url: str

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30

    @property
    def short_sha(self) -> str:
        """Deriva el hash corto de 7 caracteres."""
        if self.render_git_commit and len(self.render_git_commit) > 7:
            return self.render_git_commit[:7]
        return "dev"


settings = Settings()
