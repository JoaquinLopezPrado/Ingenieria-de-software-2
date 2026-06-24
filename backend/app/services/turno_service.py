import calendar
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import Clase, ClaseDetalle
from app.domain.turno import DiaSemana, Turno
from app.repositories.activity_repository import AbstractActivityRepository
from app.repositories.clase_cancellation_repository import ClaseCancellationRepository
from app.repositories.clase_repository import AbstractClaseRepository
from app.repositories.config_repository import AbstractConfigRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.turno_repository import AbstractTurnoRepository
from app.schemas.clases import CancelClaseRequest
from app.schemas.turno import DeactivationImpactResponse, UpdateTurnoPreviewResponse
from app.services.clase_cancellation_service import ClaseCancellationService
from app.services.email_service import EmailService

_ART = timezone(timedelta(hours=-3))

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
        session: Optional[AsyncSession] = None,
    ):
        self._turno_repo = turno_repo
        self._clase_repo = clase_repo
        self._activity_repo = activity_repo
        self._config_repo = config_repo
        self._session = session

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

    async def update(self, turno_id: int, req, admin_id: int) -> Turno:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado.")

        await self._check_no_conflict(turno, req)

        today = datetime.now(_ART).date()
        horario_cambia = req.start_time != turno.start_time or req.end_time != turno.end_time
        quitados = set(turno.days) - set(req.days)
        agregados = set(req.days) - set(turno.days)

        # 1. Campos del turno (nuevo horario, capacidad, precio, etc.)
        await self._turno_repo.update_fields(
            turno_id, req.description, req.instructor, req.start_time,
            req.end_time, req.capacity, req.class_price,
        )
        # 2. Días del turno
        if quitados or agregados:
            await self._turno_repo.set_days(turno_id, req.days)
        # 3. Cancelar clases futuras de días quitados (genera créditos + emails)
        if quitados:
            await self._cancel_clases_on_days(turno_id, quitados, today, admin_id)
        # 4. Generar clases futuras de días agregados (hasta el horizonte actual)
        if agregados:
            await self._generate_clases_on_days(turno_id, agregados, req, today)
        # 5. Propagar el nuevo horario a las clases futuras de días conservados.
        #    La capacidad NO se propaga: cada clase conserva su snapshot.
        if horario_cambia:
            await self._clase_repo.update_future_time(turno_id, req.start_time, req.end_time, today)

        # 6. Avisar por email a inscriptos que conservan su lugar (los que perdieron
        #    clases ya recibieron el email de cancelación al generarse sus créditos).
        if horario_cambia or quitados or agregados:
            await self._notify_schedule_change(turno, req, today)

        return await self._turno_repo.get_by_id(turno_id)

    async def update_preview(self, turno_id: int, req) -> UpdateTurnoPreviewResponse:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado.")

        today = datetime.now(_ART).date()
        horario_cambia = req.start_time != turno.start_time or req.end_time != turno.end_time
        quitados = set(turno.days) - set(req.days)
        agregados = set(req.days) - set(turno.days)

        clases_a_cancelar = 0
        creditos = 0
        clientes: set[int] = set()
        if quitados:
            weekdays = {_DIA_A_WEEKDAY[d] for d in quitados}
            cancellation_repo = ClaseCancellationRepository(self._session)
            for clase_id, clase_date in await self._clase_repo.list_future_active(turno_id, today):
                if clase_date.weekday() not in weekdays:
                    continue
                clases_a_cancelar += 1
                preview = await cancellation_repo.get_cancel_preview(clase_id)
                for a in preview.afectados:
                    if a.tipo in ("suscripcion", "individual_completo"):
                        creditos += 1
                        clientes.add(a.user_id)

        clases_a_generar = 0
        if agregados:
            last_date = await self._clase_repo.get_last_date(turno_id)
            start = today + timedelta(days=1)
            if last_date and last_date >= start:
                clases_a_generar = len(_generate_dates_in_range(start, last_date, list(agregados)))

        usuarios_a_notificar = 0
        if horario_cambia or quitados or agregados:
            recipients = await ClaseCancellationRepository(self._session).get_schedule_change_recipients(turno_id, today)
            usuarios_a_notificar = len(recipients)

        return UpdateTurnoPreviewResponse(
            horario_cambia=horario_cambia,
            dias_agregados=sorted(agregados, key=lambda d: _DIA_A_WEEKDAY[d]),
            dias_quitados=sorted(quitados, key=lambda d: _DIA_A_WEEKDAY[d]),
            clases_a_cancelar=clases_a_cancelar,
            clientes_afectados=len(clientes),
            creditos_a_generar=creditos,
            clases_a_generar=clases_a_generar,
            usuarios_a_notificar=usuarios_a_notificar,
        )

    async def set_active(self, turno_id: int, is_active: bool, admin_id: int) -> Turno:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado.")
        if not is_active:
            # Baja total: cancelar clases futuras (créditos + emails) y dar de baja
            # las suscripciones que ocupan el turno (condonando sus cargos impagos).
            today = datetime.now(_ART).date()
            cancellation_service = ClaseCancellationService(self._session)
            reason = "El turno fue dado de baja y ya no se dictará."
            clase_ids = [cid for cid, _ in await self._clase_repo.list_future_active(turno_id, today)]
            # Un solo mail-resumen por afectado (no uno por clase). Crédito solo por lo pagado.
            await cancellation_service.cancel_turno_baja(turno_id, clase_ids, reason, admin_id)
            await SubscriptionRepository(self._session).cancel_all_for_turno(turno_id)
        await self._turno_repo.set_active(turno_id, is_active)
        return await self._turno_repo.get_by_id(turno_id)

    async def deactivation_impact(self, turno_id: int) -> DeactivationImpactResponse:
        turno = await self._turno_repo.get_by_id(turno_id)
        if not turno:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado.")
        today = datetime.now(_ART).date()
        cancellation_repo = ClaseCancellationRepository(self._session)
        clases = await self._clase_repo.list_future_active(turno_id, today)
        creditos = 0
        clientes: set[int] = set()
        for clase_id, _clase_date in clases:
            preview = await cancellation_repo.get_cancel_preview(clase_id)
            for a in preview.afectados:
                if a.tipo in ("suscripcion", "individual_completo"):
                    creditos += 1
                    clientes.add(a.user_id)
        subs = await SubscriptionRepository(self._session).count_occupying_for_turno(turno_id)
        recipients = await cancellation_repo.get_schedule_change_recipients(turno_id, today)
        return DeactivationImpactResponse(
            clases_a_cancelar=len(clases),
            creditos_a_generar=creditos,
            clientes_afectados=len(clientes),
            suscripciones_a_baja=subs,
            usuarios_a_notificar=len(recipients),
        )

    async def _check_no_conflict(self, turno: Turno, req) -> None:
        if (
            req.description == turno.description
            and req.start_time == turno.start_time
            and req.end_time == turno.end_time
        ):
            return
        existing = await self._turno_repo.get_by_activity_description_time(
            turno.activity_id, req.description, req.start_time, req.end_time
        )
        if existing and existing.id != turno.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un turno activo con esa actividad, descripción y horario.",
            )

    async def _cancel_clases_on_days(
        self, turno_id: int, dias: set, today: date, admin_id: int
    ) -> None:
        weekdays = {_DIA_A_WEEKDAY[d] for d in dias}
        cancellation_service = ClaseCancellationService(self._session)
        req = CancelClaseRequest(reason="El turno modificó sus días y esta clase ya no se dicta.")
        for clase_id, clase_date in await self._clase_repo.list_future_active(turno_id, today):
            if clase_date.weekday() in weekdays:
                await cancellation_service.cancel(clase_id, req, admin_id)

    async def _notify_schedule_change(self, turno: Turno, req, today: date) -> None:
        recipients = await ClaseCancellationRepository(self._session).get_schedule_change_recipients(turno.id, today)
        if not recipients:
            return
        activity = await self._activity_repo.get_active_by_id(turno.activity_id)
        activity_name = activity.name if activity else ""
        dias_str = ", ".join(
            d.value.capitalize() for d in sorted(req.days, key=lambda x: _DIA_A_WEEKDAY[x])
        )
        horario_str = (
            f"{req.start_time.hour}:{req.start_time.minute:02d} a "
            f"{req.end_time.hour}:{req.end_time.minute:02d}"
        )
        email = EmailService()
        for _uid, to_email, first_name in recipients:
            email.send_cambio_horario_turno(
                to=to_email,
                first_name=first_name or "cliente",
                activity_name=activity_name,
                turno_description=req.description,
                dias_str=dias_str,
                horario_str=horario_str,
            )

    async def _generate_clases_on_days(
        self, turno_id: int, dias: set, req, today: date
    ) -> None:
        last_date = await self._clase_repo.get_last_date(turno_id)
        start = today + timedelta(days=1)
        if not last_date or last_date < start:
            return
        dates = _generate_dates_in_range(start, last_date, list(dias))
        if dates:
            await self._clase_repo.create_many(turno_id, dates, req.capacity, req.start_time, req.end_time)

    async def list_clases_by_activity(self, activity_id: int) -> List[Clase]:
        activity = await self._activity_repo.get_active_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Actividad no encontrada.",
            )
        return await self._clase_repo.list_by_activity(activity_id)
