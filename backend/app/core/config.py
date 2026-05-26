import os
from datetime import datetime
from enum import Enum
from typing import List, Optional

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

    # Database: Estos valores se setean leyendo el .env.local o .env.prod dependiendo del entorno
    db_user: str
    db_password: str
    db_host: str
    db_port: int = 5432
    db_name: str

    # La URL de la base de datos se construye dinámicamente a partir de los otros campos
    @property
    def database_url(self) -> str:
        """Construye la URL asíncrona dinámicamente."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # MercadoPago
    mp_access_token: str = ""
    mp_frontend_url: str = "http://localhost:5173"
    mp_notification_url: Optional[str] = None

    # SMTP (Mailpit local)
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@centroactividades.com"
    smtp_use_tls: bool = False

    # Mailpit HTTP API (ej: https://mailpit-xxx.onrender.com)
    mailpit_api_url: str = ""

    # Resend HTTP API (producción — tiene prioridad sobre SMTP si está seteado)
    resend_api_key: str = ""

    # Enrollment
    enrollment_ttl_minutes: int = 2
    enrollment_expiry_check_seconds: int = 30

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    @property
    def short_sha(self) -> str:
        """Deriva el hash corto de 7 caracteres."""
        if self.render_git_commit and len(self.render_git_commit) > 7:
            return self.render_git_commit[:7]
        return "dev"


settings = Settings()
