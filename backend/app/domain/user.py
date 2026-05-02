import enum
from typing import Optional


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"


class Role:
    def __init__(self, id: int, name: str, description: Optional[str] = None):
        self.id = id
        self.name = name
        self.description = description


class User:
    def __init__(
        self,
        id: int,
        email: str,
        role: Role,
        auth_provider: AuthProvider,
        is_active: bool,
        is_2fa_enabled: bool,
        token_version: int = 0,
        hashed_password: Optional[str] = None,
        google_id: Optional[str] = None,
        totp_secret: Optional[str] = None,
    ):
        self.id = id
        self.email = email
        self.role = role
        self.auth_provider = auth_provider
        self.is_active = is_active
        self.is_2fa_enabled = is_2fa_enabled
        self.token_version = token_version
        self.hashed_password = hashed_password
        self.google_id = google_id
        self.totp_secret = totp_secret
