from typing import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import decode_access_token

_bearer = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id, token_version = decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )
    user = await UserRepository(db).get_by_id(user_id)
    if not user or user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )
    return user


async def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    return user.id


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permisos para realizar esta acción.",
        )
    return user
