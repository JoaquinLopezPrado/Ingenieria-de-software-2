from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import AppConfig as AppConfigORM


class AbstractConfigRepository(ABC):

    @abstractmethod
    async def get_int(self, key: str, default: int) -> int:
        raise NotImplementedError


class ConfigRepository(AbstractConfigRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_int(self, key: str, default: int) -> int:
        result = await self._session.execute(
            select(AppConfigORM).where(AppConfigORM.key == key)
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            return default
        try:
            return int(orm.value)
        except ValueError:
            return default
