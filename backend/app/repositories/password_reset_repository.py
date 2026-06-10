from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import PasswordResetToken as PasswordResetTokenORM


class AbstractPasswordResetRepository(ABC):

    @abstractmethod
    async def save(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[PasswordResetTokenORM]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_hash(self, token_hash: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_user_id(self, user_id: int) -> None:
        raise NotImplementedError


class PasswordResetRepository(AbstractPasswordResetRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self._session.add(PasswordResetTokenORM(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
        await self._session.flush()

    async def get_by_hash(self, token_hash: str) -> Optional[PasswordResetTokenORM]:
        result = await self._session.execute(
            select(PasswordResetTokenORM).where(PasswordResetTokenORM.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def delete_by_hash(self, token_hash: str) -> bool:
        result = await self._session.execute(
            delete(PasswordResetTokenORM).where(PasswordResetTokenORM.token_hash == token_hash)
        )
        return result.rowcount > 0

    async def delete_by_user_id(self, user_id: int) -> None:
        await self._session.execute(
            delete(PasswordResetTokenORM).where(PasswordResetTokenORM.user_id == user_id)
        )
