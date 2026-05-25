from abc import ABC, abstractmethod
from datetime import time
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import exists, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enrollment import EnrollmentStatus, EnrollmentType
from app.domain.turno import DiaSemana, Turno
from app.models.clase import Clase as ClaseORM
from app.models.enrollment import Enrollment as EnrollmentORM
from app.models.turno import Turno as TurnoORM, TurnoDia as TurnoDiaORM

_MONTHLY_ACTIVE_STATUSES = [EnrollmentStatus.PENDING, EnrollmentStatus.CONFIRMED]


class AbstractTurnoRepository(ABC):

    @abstractmethod
    async def get_by_id(self, turno_id: int) -> Optional[Turno]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_activity_month_year_description(
        self, activity_id: int, month: int, year: int, description: str
    ) -> Optional[Turno]:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        activity_id: Optional[int],
        has_availability: Optional[bool],
        months: List[Tuple[int, int]],
        page: int,
        page_size: int,
        include_inactive: bool = False,
    ) -> Tuple[List[Turno], int]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        activity_id: int,
        description: str,
        instructor: str,
        start_time: time,
        end_time: time,
        capacity: int,
        price: Decimal,
        class_price: Decimal,
        month: int,
        year: int,
        days: List[DiaSemana],
        is_active: bool = False,
    ) -> Turno:
        raise NotImplementedError


class TurnoRepository(AbstractTurnoRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def list(
        self,
        activity_id: Optional[int],
        has_availability: Optional[bool],
        months: List[Tuple[int, int]],
        page: int,
        page_size: int,
        include_inactive: bool = False,
    ) -> Tuple[List[Turno], int]:
        base = select(TurnoORM).where(tuple_(TurnoORM.month, TurnoORM.year).in_(months))
        if not include_inactive:
            base = base.where(TurnoORM.is_active == True)
        base = base.order_by(TurnoORM.year, TurnoORM.month)

        if activity_id is not None:
            base = base.where(TurnoORM.activity_id == activity_id)

        if has_availability is not None:
            clase_exists = exists().where(
                ClaseORM.turno_id == TurnoORM.id,
                ClaseORM.is_active == True,
            )
            base = base.where(clase_exists if has_availability else ~clase_exists)

        total = (await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )).scalar_one()

        enrolled_subq = (
            select(func.count(EnrollmentORM.id))
            .where(
                EnrollmentORM.turno_id == TurnoORM.id,
                EnrollmentORM.enrollment_type == EnrollmentType.MONTHLY,
                EnrollmentORM.status.in_(_MONTHLY_ACTIVE_STATUSES),
            )
            .correlate(TurnoORM)
            .scalar_subquery()
        )

        rows = (await self._session.execute(
            base
            .options(selectinload(TurnoORM.days))
            .add_columns(enrolled_subq.label("enrolled"))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).all()

        return [self._to_domain(orm, enrolled) for orm, enrolled in rows], total

    async def get_by_id(self, turno_id: int) -> Optional[Turno]:
        result = await self._session.execute(
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(TurnoORM.id == turno_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_activity_month_year_description(
        self, activity_id: int, month: int, year: int, description: str
    ) -> Optional[Turno]:
        result = await self._session.execute(
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.month == month,
                TurnoORM.year == year,
                TurnoORM.description == description,
                TurnoORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(
        self,
        activity_id: int,
        description: str,
        instructor: str,
        start_time: time,
        end_time: time,
        capacity: int,
        price: Decimal,
        class_price: Decimal,
        month: int,
        year: int,
        days: List[DiaSemana],
        is_active: bool = False,
    ) -> Turno:
        orm = TurnoORM(
            activity_id=activity_id,
            description=description,
            instructor=instructor,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            price=price,
            class_price=class_price,
            month=month,
            year=year,
            is_active=is_active,
        )
        self._session.add(orm)
        await self._session.flush()

        for dia in days:
            self._session.add(TurnoDiaORM(turno_id=orm.id, dia=dia))

        await self._session.flush()
        await self._session.refresh(orm, ["days"])
        return self._to_domain(orm)

    def _to_domain(self, orm: TurnoORM, enrolled: int = 0) -> Turno:
        return Turno(
            id=orm.id,
            activity_id=orm.activity_id,
            description=orm.description,
            instructor=orm.instructor,
            start_time=orm.start_time,
            end_time=orm.end_time,
            capacity=orm.capacity,
            price=orm.price,
            class_price=orm.class_price,
            month=orm.month,
            year=orm.year,
            is_active=orm.is_active,
            days=[DiaSemana(dia_orm.dia) for dia_orm in orm.days],
            enrolled=enrolled,
        )
