from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import List, Tuple

from sqlalchemy import and_, func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import Clase, ClaseDetalle
from app.domain.enrollment import EnrollmentStatus
from app.models.clase import Clase as ClaseORM
from app.models.enrollment import Enrollment as EnrollmentORM, EnrollmentSlot as EnrollmentSlotORM
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

    @abstractmethod
    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
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
                TurnoORM.is_active,
                ClaseORM.is_active,
                tuple_(TurnoORM.month, TurnoORM.year).in_(months),
            )
            .order_by(ClaseORM.date)
        )
        return [self._to_domain(orm) for orm in result.scalars()]

    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
        enrolled_subquery = (
            select(func.count())
            .select_from(EnrollmentSlotORM)
            .join(EnrollmentORM, EnrollmentSlotORM.enrollment_id == EnrollmentORM.id)
            .where(
                EnrollmentSlotORM.clase_id == ClaseORM.id,
                EnrollmentORM.status.in_([EnrollmentStatus.PENDING, EnrollmentStatus.CONFIRMED]),
            )
            .scalar_subquery()
        )
        result = await self._session.execute(
            select(ClaseORM, TurnoORM.start_time, TurnoORM.end_time, enrolled_subquery.label("enrolled"))
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                or_(
                    ClaseORM.date > datetime.now(timezone.utc).date(),
                    and_(
                        ClaseORM.date == datetime.now(timezone.utc).date(),
                        TurnoORM.start_time > datetime.now(timezone.utc).time(),
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
