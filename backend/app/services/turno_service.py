import calendar
from datetime import date, time
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from app.domain.clase import Clase
from app.domain.turno import DiaSemana, Turno
from app.repositories.activity_repository import AbstractActivityRepository
from app.repositories.clase_repository import AbstractClaseRepository
from app.repositories.config_repository import AbstractConfigRepository
from app.repositories.turno_repository import AbstractTurnoRepository

_DEFAULT_PAGE_SIZE = 20
_DEFAULT_NEXT_MONTH_PREVIEW_DAYS = 10


def _months_to_show(today: date, preview_days: int) -> List[Tuple[int, int]]:
    _, days_in_month = calendar.monthrange(today.year, today.month)
    days_remaining = days_in_month - today.day
    months = [(today.month, today.year)]
    if days_remaining <= preview_days:
        next_month = today.month % 12 + 1
        next_year = today.year + (1 if today.month == 12 else 0)
        months.append((next_month, next_year))
    return months

_DIA_A_WEEKDAY = {
    DiaSemana.LUNES: 0,
    DiaSemana.MARTES: 1,
    DiaSemana.MIERCOLES: 2,
    DiaSemana.JUEVES: 3,
    DiaSemana.VIERNES: 4,
    DiaSemana.SABADO: 5,
    DiaSemana.DOMINGO: 6,
}


def _generate_dates(month: int, year: int, days: List[DiaSemana]) -> List[date]:
    target_weekdays = {_DIA_A_WEEKDAY[d] for d in days}
    _, days_in_month = calendar.monthrange(year, month)
    return [
        date(year, month, day)
        for day in range(1, days_in_month + 1)
        if date(year, month, day).weekday() in target_weekdays
    ]


class TurnoService:

    def __init__(
        self,
        turno_repo: AbstractTurnoRepository,
        clase_repo: AbstractClaseRepository,
        activity_repo: AbstractActivityRepository,
        config_repo: AbstractConfigRepository,
    ):
        self._turno_repo = turno_repo
        self._clase_repo = clase_repo
        self._activity_repo = activity_repo
        self._config_repo = config_repo

    async def list(
        self,
        activity_id: Optional[int],
        has_availability: Optional[bool],
        page: int,
    ) -> Tuple[List[Turno], int, int]:
        page_size = await self._config_repo.get_int("turnos_page_size", _DEFAULT_PAGE_SIZE)
        preview_days = await self._config_repo.get_int("next_month_preview_days", _DEFAULT_NEXT_MONTH_PREVIEW_DAYS)
        months = _months_to_show(date.today(), preview_days)
        items, total = await self._turno_repo.list(activity_id, has_availability, months, page, page_size)
        return items, total, page_size

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
        is_active: bool = False,
    ) -> Turno:
        activity = await self._activity_repo.get_active_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada.",
            )

        existing = await self._turno_repo.get_by_activity_month_year_description(
            activity_id, month, year, description
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un turno con esa descripción para esa actividad en ese mes.",
            )

        turno = await self._turno_repo.create(
            activity_id, description, instructor, start_time, end_time, capacity, price, month, year, days, is_active
        )

        dates = _generate_dates(month, year, days)
        await self._clase_repo.create_many(turno.id, dates, capacity)

        return turno

    async def list_clases_by_activity(self, activity_id: int) -> List[Clase]:
        activity = await self._activity_repo.get_active_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada.",
            )
        preview_days = await self._config_repo.get_int("next_month_preview_days", _DEFAULT_NEXT_MONTH_PREVIEW_DAYS)
        months = _months_to_show(date.today(), preview_days)
        return await self._clase_repo.list_by_activity_and_months(activity_id, months)
