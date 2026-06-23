import calendar
from datetime import date, time, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status

from app.domain.clase import Clase, ClaseDetalle
from app.domain.turno import DiaSemana, Turno
from app.repositories.activity_repository import AbstractActivityRepository
from app.repositories.clase_repository import AbstractClaseRepository
from app.repositories.config_repository import AbstractConfigRepository
from app.repositories.turno_repository import AbstractTurnoRepository

_DEFAULT_PAGE_SIZE = 20
_MONTHS_AHEAD = 3

_DIA_A_WEEKDAY = {
    DiaSemana.LUNES: 0,
    DiaSemana.MARTES: 1,
    DiaSemana.MIERCOLES: 2,
    DiaSemana.JUEVES: 3,
    DiaSemana.VIERNES: 4,
    DiaSemana.SABADO: 5,
    DiaSemana.DOMINGO: 6,
}


def _generate_dates_in_range(start: date, end: date, days: List[DiaSemana]) -> List[date]:
    from datetime import timedelta
    target_weekdays = {_DIA_A_WEEKDAY[d] for d in days}
    result = []
    current = start
    while current <= end:
        if current.weekday() in target_weekdays:
            result.append(current)
        current += timedelta(days=1)
    return result


def _end_date_months_ahead(start: date, months: int) -> date:
    target_month = start.month + months
    target_year = start.year + (target_month - 1) // 12
    target_month = ((target_month - 1) % 12) + 1
    last_day = calendar.monthrange(target_year, target_month)[1]
    return date(target_year, target_month, last_day)


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
        items, total = await self._turno_repo.list(activity_id, has_availability, page, page_size)
        return items, total, page_size

    async def list_all(
        self,
        activity_id: Optional[int],
        has_availability: Optional[bool],
        page: int,
    ) -> Tuple[List[Turno], int, int]:
        page_size = await self._config_repo.get_int("turnos_page_size", _DEFAULT_PAGE_SIZE)
        items, total = await self._turno_repo.list(activity_id, has_availability, page, page_size, include_inactive=True)
        return items, total, page_size

    async def create(
        self,
        activity_id: int,
        description: str,
        instructor: str,
        start_time: time,
        end_time: time,
        capacity: int,
        class_price: Decimal,
        start_date: date,
        days: List[DiaSemana],
        is_active: bool = False,
    ) -> Turno:
        activity = await self._activity_repo.get_active_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada.",
            )

        existing = await self._turno_repo.get_by_activity_description_time(
            activity_id, description, start_time, end_time
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un turno activo con esa actividad, descripción y horario.",
            )

        turno = await self._turno_repo.create(
            activity_id, description, instructor, start_time, end_time, capacity, class_price, days, is_active
        )

        end_date = _end_date_months_ahead(start_date, _MONTHS_AHEAD)
        dates = _generate_dates_in_range(start_date, end_date, days)
        if dates:
            await self._clase_repo.create_many(turno.id, dates, capacity, start_time, end_time)

        return turno

    async def list_clases_by_turno(self, turno_id: int, include_past: bool = False) -> List[ClaseDetalle]:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado.",
            )
        return await self._clase_repo.list_by_turno(turno_id, include_past=include_past)

    async def generate_upcoming_classes(self, turno_id: int) -> int:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado.")

        last_date = await self._clase_repo.get_last_date(turno_id)
        start = (last_date + timedelta(days=1)) if last_date else date.today()
        end = _end_date_months_ahead(start, _MONTHS_AHEAD)
        dates = _generate_dates_in_range(start, end, turno.days)

        if not dates:
            return 0

        # Los abonados no materializan slots: su asiento se cuenta al vuelo sobre
        # la suscripción activa. El cron solo genera las filas Clase.
        clase_ids = await self._clase_repo.create_many(
            turno.id, dates, turno.capacity, turno.start_time, turno.end_time
        )
        return len(clase_ids)

    async def list_clases_by_activity(self, activity_id: int) -> List[Clase]:
        activity = await self._activity_repo.get_active_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada.",
            )
        return await self._clase_repo.list_by_activity(activity_id)
