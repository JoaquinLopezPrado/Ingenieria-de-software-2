from abc import ABC, abstractmethod
from datetime import time
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import exists, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.turno import DiaSemana, Turno
from app.models.clase import Clase as ClaseORM
from app.models.turno import Turno as TurnoORM, TurnoDia as TurnoDiaORM


class AbstractTurnoRepository(ABC):

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
        month: int,
        year: int,
        days: List[DiaSemana],
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
    ) -> Tuple[List[Turno], int]:
        query = (
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(TurnoORM.is_active == True)
            .where(tuple_(TurnoORM.month, TurnoORM.year).in_(months))
            .order_by(TurnoORM.year, TurnoORM.month)
        )

        if activity_id is not None:
            query = query.where(TurnoORM.activity_id == activity_id)

        if has_availability is not None:
            clase_exists = exists().where(
                ClaseORM.turno_id == TurnoORM.id,
                ClaseORM.is_active == True,
            )
            query = query.where(clase_exists if has_availability else ~clase_exists)

        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        )
        return [self._to_domain(orm) for orm in result.scalars()], total

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
        month: int,
        year: int,
        days: List[DiaSemana],
    ) -> Turno:
        orm = TurnoORM(
            activity_id=activity_id,
            description=description,
            instructor=instructor,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            price=price,
            month=month,
            year=year,
        )
        self._session.add(orm)
        await self._session.flush()

        for dia in days:
            self._session.add(TurnoDiaORM(turno_id=orm.id, dia=dia))

        await self._session.flush()
        await self._session.refresh(orm, ["days"])
        return self._to_domain(orm)

    def _to_domain(self, orm: TurnoORM) -> Turno:
        return Turno(
            id=orm.id,
            activity_id=orm.activity_id,
            description=orm.description,
            instructor=orm.instructor,
            start_time=orm.start_time,
            end_time=orm.end_time,
            capacity=orm.capacity,
            price=orm.price,
            month=orm.month,
            year=orm.year,
            is_active=orm.is_active,
            days=[DiaSemana(dia_orm.dia) for dia_orm in orm.days],
        )
