from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import Clase
from app.models.clase import Clase as ClaseORM
from app.models.turno import Turno as TurnoORM


class AbstractClaseRepository(ABC):

    @abstractmethod
    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_activity_and_months(
        self, activity_id: int, months: List[Tuple[int, int]]
    ) -> List[Clase]:
        raise NotImplementedError


class ClaseRepository(AbstractClaseRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> None:
        clases = [
            ClaseORM(turno_id=turno_id, date=d, capacity=capacity, is_active=True)
            for d in dates
        ]
        self._session.add_all(clases)
        await self._session.flush()

    async def list_by_activity_and_months(
        self, activity_id: int, months: List[Tuple[int, int]]
    ) -> List[Clase]:
        result = await self._session.execute(
            select(ClaseORM)
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.is_active == True,
                ClaseORM.is_active == True,
                tuple_(TurnoORM.month, TurnoORM.year).in_(months),
            )
            .order_by(ClaseORM.date)
        )
        return [self._to_domain(orm) for orm in result.scalars()]

    def _to_domain(self, orm: ClaseORM) -> Clase:
        return Clase(
            id=orm.id,
            turno_id=orm.turno_id,
            date=orm.date,
            capacity=orm.capacity,
            is_active=orm.is_active,
        )
