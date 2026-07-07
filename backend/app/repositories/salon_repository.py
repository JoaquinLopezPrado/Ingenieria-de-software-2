from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.salon import Salon
from app.models.salon import Salon as SalonORM


class AbstractSalonRepository(ABC):

    @abstractmethod
    async def get_active_by_name(self, name: str) -> Optional[Salon]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_id(self, salon_id: int) -> Optional[Salon]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, salon_id: int) -> Optional[Salon]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, name: str, capacity: int) -> Salon:
        raise NotImplementedError

    @abstractmethod
    async def list_active(self) -> list[Salon]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Salon]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, salon_id: int, name: str, capacity: int) -> Salon:
        raise NotImplementedError


class SalonRepository(AbstractSalonRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_by_name(self, name: str) -> Optional[Salon]:
        result = await self._session.execute(
            select(SalonORM).where(
                SalonORM.name == name,
                SalonORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_active_by_id(self, salon_id: int) -> Optional[Salon]:
        result = await self._session.execute(
            select(SalonORM).where(
                SalonORM.id == salon_id,
                SalonORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_id(self, salon_id: int) -> Optional[Salon]:
        result = await self._session.execute(
            select(SalonORM).where(SalonORM.id == salon_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(self, name: str, capacity: int) -> Salon:
        orm = SalonORM(name=name, capacity=capacity, is_active=True)
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def list_active(self) -> list[Salon]:
        result = await self._session.execute(
            select(SalonORM).where(SalonORM.is_active == True)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def list_all(self) -> list[Salon]:
        result = await self._session.execute(select(SalonORM))
        return [self._to_domain(row) for row in result.scalars().all()]

    async def update(self, salon_id: int, name: str, capacity: int) -> Salon:
        result = await self._session.execute(
            select(SalonORM).where(SalonORM.id == salon_id)
        )
        orm = result.scalar_one()
        orm.name = name
        orm.capacity = capacity
        await self._session.flush()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: SalonORM) -> Salon:
        return Salon(
            id=orm.id,
            name=orm.name,
            capacity=orm.capacity,
            is_active=orm.is_active,
        )
