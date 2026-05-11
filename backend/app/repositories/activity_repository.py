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
    async def create(self, name: str, instructor: str) -> Activity:
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

    async def create(self, name: str, instructor: str) -> Activity:
        orm = ActivityORM(name=name, instructor=instructor, is_active=True)
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: ActivityORM) -> Activity:
        return Activity(
            id=orm.id,
            name=orm.name,
            instructor=orm.instructor,
            is_active=orm.is_active,
        )
