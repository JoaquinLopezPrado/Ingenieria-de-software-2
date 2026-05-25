import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import uuid

from app.core.config import settings

_ALGORITHM = "HS256"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: int, token_version: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "ver": token_version,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }

    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "jti": str(uuid.uuid4()),
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
    }

    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> tuple[int, int]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError
        return int(payload["sub"]), int(payload["ver"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise


def decode_refresh_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError) as e:
        raise ValueError from e


def create_google_state_token(mode: str = "login", user_id: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict = {
        "type": "oauth_state",
        "mode": mode,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }
    if user_id is not None:
        payload["user_id"] = user_id
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_google_state_token(token: str) -> dict | None:
    """Devuelve {"mode": str, "user_id": int|None} o None si el token es inválido."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        if payload.get("type") != "oauth_state":
            return None
        return {
            "mode": payload.get("mode", "login"),
            "user_id": payload.get("user_id"),
        }
    except jwt.PyJWTError:
        return None


def create_google_pending_token(google_id: str, email: str, first_name: str, last_name: str) -> str:
    """Token de corta vida para completar el registro de un usuario nuevo de Google."""
    now = datetime.now(timezone.utc)
    payload = {
        "type": "google_pending",
        "google_id": google_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=1),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_google_pending_token(token: str) -> dict:
    payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    if payload.get("type") != "google_pending":
        raise ValueError("Token type inválido")
    return {
        "google_id": payload["google_id"],
        "email": payload["email"],
        "first_name": payload["first_name"],
        "last_name": payload["last_name"],
    }