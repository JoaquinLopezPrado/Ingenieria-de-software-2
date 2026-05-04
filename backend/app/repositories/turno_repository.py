from abc import ABC, abstractmethod
from datetime import time
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.turno import DiaSemana, Turno
from app.models.turno import Turno as TurnoORM, TurnoDia as TurnoDiaORM


class AbstractTurnoRepository(ABC):

    @abstractmethod
    async def get_by_activity_month_year_name(
        self, activity_id: int, month: int, year: int, name: str
    ) -> Optional[Turno]:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        activity_id: int,
        name: str,
        time: time,
        capacity: int,
        month: int,
        year: int,
        days: List[DiaSemana],
    ) -> Turno:
        raise NotImplementedError


class TurnoRepository(AbstractTurnoRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_activity_month_year_name(
        self, activity_id: int, month: int, year: int, name: str
    ) -> Optional[Turno]:
        result = await self._session.execute(
            select(TurnoORM)
            .options(selectinload(TurnoORM.days))
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.month == month,
                TurnoORM.year == year,
                TurnoORM.name == name,
                TurnoORM.is_active == True,
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def create(
        self,
        activity_id: int,
        name: str,
        time: time,
        capacity: int,
        month: int,
        year: int,
        days: List[DiaSemana],
    ) -> Turno:
        orm = TurnoORM(
            activity_id=activity_id,
            name=name,
            time=time,
            capacity=capacity,
            month=month,
            year=year,
            is_active=True,
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
            name=orm.name,
            time=orm.time,
            capacity=orm.capacity,
            month=orm.month,
            year=orm.year,
            is_active=orm.is_active,
            days=[DiaSemana(dia_orm.dia) for dia_orm in orm.days],
        )
