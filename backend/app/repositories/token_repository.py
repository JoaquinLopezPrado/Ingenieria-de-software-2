from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshToken as RefreshTokenORM


class AbstractTokenRepository(ABC):

    @abstractmethod
    async def save(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_hash(self, token_hash: str) -> bool:
        raise NotImplementedError


class TokenRepository(AbstractTokenRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._session.add(RefreshTokenORM(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
        await self._session.flush()

    async def delete_by_hash(self, token_hash: str) -> bool:
        result = await self._session.execute(
            delete(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
        )
        return result.rowcount > 0