from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.activity import Activity
from app.models.activity import Activity as ActivityORM


class AbstractActivityRepository(ABC):

    @abstractmethod
    async def get_active_by_name(self, name: str) -> Optional[Activity]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_id(self, activity_id: int) -> Optional[Activity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, name: str, description: str) -> Activity:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self) -> list[Activity]:
        raise NotImplementedError


class ActivityRepository(AbstractActivityRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_by_name(self, name: str) -> Optional[Activity]:
        result = await self._session.execute(
            select(ActivityORM).where(
                ActivityORM.name == name,
                ActivityORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_active_by_id(self, activity_id: int) -> Optional[Activity]:
        result = await self._session.execute(
            select(ActivityORM).where(
                ActivityORM.id == activity_id,
                ActivityORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(self, name: str, description: str) -> Activity:
        orm = ActivityORM(name=name, description=description, is_active=True)
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def list_active(self) -> list[Activity]:
        result = await self._session.execute(
            select(ActivityORM).where(ActivityORM.is_active == True)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    def _to_domain(self, orm: ActivityORM) -> Activity:
        return Activity(
            id=orm.id,
            name=orm.name,
            description=orm.description,
            is_active=orm.is_active,
        )
