import calendar
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import Clase, ClaseDetalle
from app.models.clase import Clase as ClaseORM
from app.models.turno import Turno as TurnoORM
from app.repositories.capacity import occupied_subq


class AbstractClaseRepository(ABC):

    @abstractmethod
    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    async def get_last_date(self, turno_id: int) -> Optional[date]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_activity(self, activity_id: int) -> List[Clase]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
        raise NotImplementedError


class ClaseRepository(AbstractClaseRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> List[int]:
        clases = [
            ClaseORM(turno_id=turno_id, date=d, capacity=capacity, is_active=True)
            for d in dates
        ]
        self._session.add_all(clases)
        await self._session.flush()
        return [c.id for c in clases]

    async def get_last_date(self, turno_id: int) -> Optional[date]:
        result = await self._session.execute(
            select(func.max(ClaseORM.date)).where(ClaseORM.turno_id == turno_id)
        )
        return result.scalar_one_or_none()

    async def list_by_activity(self, activity_id: int) -> List[Clase]:
        today = date.today()
        result = await self._session.execute(
            select(ClaseORM)
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.is_active == True,
                ClaseORM.is_active == True,
                ClaseORM.date >= today,
            )
            .order_by(ClaseORM.date)
        )
        return [self._to_domain(orm) for orm in result.scalars()]

    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
        now_art = datetime.now(timezone(timedelta(hours=-3)))
        today = now_art.date()
        next_month = today.month % 12 + 1
        next_month_year = today.year + (1 if today.month == 12 else 0)
        end_date = date(next_month_year, next_month, calendar.monthrange(next_month_year, next_month)[1])

        enrolled_subquery = occupied_subq(ClaseORM.turno_id, ClaseORM.id, ClaseORM.date)
        result = await self._session.execute(
            select(ClaseORM, TurnoORM.start_time, TurnoORM.end_time, enrolled_subquery.label("enrolled"))
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date <= end_date,
                or_(
                    ClaseORM.date > today,
                    and_(
                        ClaseORM.date == today,
                        TurnoORM.start_time > now_art.time(),
                    ),
                ),
            )
            .order_by(ClaseORM.date)
        )
        return [
            ClaseDetalle(
                id=row.Clase.id,
                turno_id=row.Clase.turno_id,
                date=row.Clase.date,
                start_time=row.start_time,
                end_time=row.end_time,
                capacity=row.Clase.capacity,
                enrolled=row.enrolled,
                is_active=row.Clase.is_active,
            )
            for row in result
        ]

    def _to_domain(self, orm: ClaseORM) -> Clase:
        return Clase(
            id=orm.id,
            turno_id=orm.turno_id,
            date=orm.date,
            capacity=orm.capacity,
            is_active=orm.is_active,
        )
