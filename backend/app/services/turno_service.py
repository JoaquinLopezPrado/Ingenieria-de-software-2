import calendar
from datetime import date, time
from typing import List

from fastapi import HTTPException, status

from app.domain.turno import DiaSemana, Turno
from app.repositories.activity_repository import AbstractActivityRepository
from app.repositories.clase_repository import AbstractClaseRepository
from app.repositories.turno_repository import AbstractTurnoRepository

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
    ):
        self._turno_repo = turno_repo
        self._clase_repo = clase_repo
        self._activity_repo = activity_repo

    async def create(
        self,
        activity_id: int,
        description: str,
        start_time: time,
        end_time: time,
        capacity: int,
        month: int,
        year: int,
        days: List[DiaSemana],
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
            activity_id, description, start_time, end_time, capacity, month, year, days
        )

        dates = _generate_dates(month, year, days)
        await self._clase_repo.create_many(turno.id, dates, capacity)

        return turno
