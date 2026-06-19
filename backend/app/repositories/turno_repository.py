from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.turno import DiaSemana, Turno
from app.models.clase import Clase as ClaseORM
from app.models.turno import Turno as TurnoORM, TurnoDia as TurnoDiaORM
from app.repositories.capacity import active_subscriptions_subq, occupied_subq


class AbstractTurnoRepository(ABC):

    @abstractmethod
    async def get_by_id(self, turno_id: int) -> Optional[Turno]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_activity_description_time(
        self, activity_id: int, description: str, start_time: time, end_time: time
    ) -> Optional[Turno]:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        activity_id: Optional[int],
        has_availability: Optional[bool],
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
        class_price: Decimal,
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
        page: int,
        page_size: int,
        include_inactive: bool = False,
    ) -> Tuple[List[Turno], int]:
        base = select(TurnoORM)
        if not include_inactive:
            base = base.where(TurnoORM.is_active == True)
        base = base.order_by(TurnoORM.start_time, TurnoORM.description)

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

        _ART = timezone(timedelta(hours=-3))
        now_art = datetime.now(_ART)
        today = now_art.date()
        now_time = now_art.time()

        # Ocupación de abonados a nivel turno: la del período vigente (hoy).
        enrolled_subq = active_subscriptions_subq(TurnoORM.id, today)
        occupied = occupied_subq(ClaseORM.turno_id, ClaseORM.id, ClaseORM.date)

        future_date_filter = or_(
            ClaseORM.date > today,
            and_(
                ClaseORM.date == today,
                TurnoORM.start_time > now_time,
            ),
        )

        remaining_subq = (
            select(func.count(ClaseORM.id))
            .where(
                ClaseORM.turno_id == TurnoORM.id,
                ClaseORM.is_active == True,
                ClaseORM.capacity > occupied,
                future_date_filter,
            )
            .correlate(TurnoORM)
            .scalar_subquery()
        )

        future_subq = (
            select(func.count(ClaseORM.id))
            .where(
                ClaseORM.turno_id == TurnoORM.id,
                ClaseORM.is_active == True,
                future_date_filter,
            )
            .correlate(TurnoORM)
            .scalar_subquery()
        )

        rows = (await self._session.execute(
            base
            .options(selectinload(TurnoORM.days))
            .add_columns(enrolled_subq.label("enrolled"))
            .add_columns(remaining_subq.label("remaining"))
            .add_columns(future_subq.label("future_count"))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).all()

        return [
            self._to_domain(orm, enrolled, remaining > 0, future_count > 0)
            for orm, enrolled, remaining, future_count in rows
        ], total

    async def get_by_id(self, turno_id: int) -> Optional[Turno]:
        result = await self._session.execute(
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(TurnoORM.id == turno_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_activity_description_time(
        self, activity_id: int, description: str, start_time: time, end_time: time
    ) -> Optional[Turno]:
        result = await self._session.execute(
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.description == description,
                TurnoORM.start_time == start_time,
                TurnoORM.end_time == end_time,
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
        class_price: Decimal,
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
            class_price=class_price,
            is_active=is_active,
        )
        self._session.add(orm)
        await self._session.flush()

        for dia in days:
            self._session.add(TurnoDiaORM(turno_id=orm.id, dia=dia))

        await self._session.flush()
        await self._session.refresh(orm, ["days"])
        return self._to_domain(orm)

    def _to_domain(
        self,
        orm: TurnoORM,
        enrolled: int = 0,
        has_remaining_classes: bool = True,
        has_future_classes: bool = True,
    ) -> Turno:
        return Turno(
            id=orm.id,
            activity_id=orm.activity_id,
            description=orm.description,
            instructor=orm.instructor,
            start_time=orm.start_time,
            end_time=orm.end_time,
            capacity=orm.capacity,
            class_price=orm.class_price,
            is_active=orm.is_active,
            days=[DiaSemana(dia_orm.dia) for dia_orm in orm.days],
            enrolled=enrolled,
            has_remaining_classes=has_remaining_classes,
            has_future_classes=has_future_classes,
        )
