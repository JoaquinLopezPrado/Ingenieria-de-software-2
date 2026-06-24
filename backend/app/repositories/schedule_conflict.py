"""Detección de solape horario en las inscripciones de un cliente.

Regla: un cliente no puede ocupar dos ``Clase`` distintas que se pisen en fecha y
horario (cross-actividad). Todo converge a nivel ``Clase`` (fecha + snapshot de
horario): suscripciones, clases sueltas y promoción de lista de espera se comparan
con la misma lógica, sin razonar día-de-semana recurrente vs fecha concreta.

La lista de espera NO ocupa asiento, por eso no figura como ocupación firme: solo
se valida el alta contra la ocupación firme ya existente. La promoción de waitlist
pasa por ``SubscriptionService.create``, así que hereda esta validación.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import OCCUPYING_SUBSCRIPTION_STATUSES
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.single_enrollment import (
    SingleEnrollment as SingleEnrollmentORM,
    SingleEnrollmentSlot as SingleSlotORM,
)
from app.models.subscription import Subscription as SubscriptionORM
from app.models.turno import Turno as TurnoORM

# Sueltas que ocupan asiento. Una PENDING con TTL vencido se excluye al vuelo: la
# propia reserva abandonada del cliente no debe bloquearlo al reintentar (el job de
# expiración la cancela aparte).
_OCCUPYING_SINGLE_STATUSES = (
    SingleEnrollmentStatus.PENDING,
    SingleEnrollmentStatus.CONFIRMED,
    SingleEnrollmentStatus.DEPOSIT_PAID,
)


@dataclass(frozen=True)
class Slot:
    """Una ocupación concreta: una clase con su fecha y rango horario snapshot."""
    clase_id: int
    date: date
    start_time: time
    end_time: time
    turno_description: str
    activity_name: str


def _overlaps(a: Slot, b: Slot) -> bool:
    """Solape estricto de rangos en la misma fecha.

    Clases adyacentes que se tocan en el borde (10–11 y 11–12) NO se solapan.
    """
    return a.date == b.date and a.start_time < b.end_time and b.start_time < a.end_time


def _row_to_slot(row) -> Slot:
    return Slot(
        clase_id=row[0],
        date=row[1],
        start_time=row[2],
        end_time=row[3],
        turno_description=row[4],
        activity_name=row[5],
    )


_SLOT_COLUMNS = (
    ClaseORM.id,
    ClaseORM.date,
    ClaseORM.start_time,
    ClaseORM.end_time,
    TurnoORM.description,
    ActivityORM.name,
)


async def _load_target_slots(session: AsyncSession, clase_ids: list[int]) -> list[Slot]:
    rows = (await session.execute(
        select(*_SLOT_COLUMNS)
        .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
        .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
        .where(ClaseORM.id.in_(clase_ids))
    )).all()
    return [_row_to_slot(r) for r in rows]


async def _load_occupied_slots(session: AsyncSession, user_id: int, from_date: date) -> list[Slot]:
    """Clases que el cliente ya ocupa de forma firme (abonos + sueltas), desde ``from_date``."""
    base = (
        select(*_SLOT_COLUMNS)
        .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
        .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
        .where(ClaseORM.is_active.is_(True), ClaseORM.date >= from_date)
    )

    # Abonos: la suscripción ocupa las clases de su turno dentro de [start_date, ends_on].
    sub_rows = (await session.execute(
        base
        .join(SubscriptionORM, SubscriptionORM.turno_id == ClaseORM.turno_id)
        .where(
            SubscriptionORM.user_id == user_id,
            SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
            SubscriptionORM.start_date <= ClaseORM.date,
            or_(SubscriptionORM.ends_on.is_(None), ClaseORM.date <= SubscriptionORM.ends_on),
        )
    )).all()

    # Sueltas: cada slot apunta a una clase puntual. Se excluyen las PENDING vencidas.
    now = datetime.now(timezone.utc)
    single_rows = (await session.execute(
        base
        .join(SingleSlotORM, SingleSlotORM.clase_id == ClaseORM.id)
        .join(SingleEnrollmentORM, SingleEnrollmentORM.id == SingleSlotORM.enrollment_id)
        .where(
            SingleEnrollmentORM.user_id == user_id,
            SingleEnrollmentORM.status.in_(_OCCUPYING_SINGLE_STATUSES),
            or_(
                SingleEnrollmentORM.status != SingleEnrollmentStatus.PENDING,
                SingleEnrollmentORM.expires_at.is_(None),
                SingleEnrollmentORM.expires_at > now,
            ),
        )
    )).all()

    by_id: dict[int, Slot] = {}
    for row in (*sub_rows, *single_rows):
        slot = _row_to_slot(row)
        by_id[slot.clase_id] = slot
    return list(by_id.values())


def _find_internal_overlap(targets: list[Slot]) -> tuple[Slot, Slot] | None:
    """Solape entre dos clases del propio pedido (caso inscripción múltiple de sueltas)."""
    by_date: dict[date, list[Slot]] = defaultdict(list)
    for t in sorted(targets, key=lambda s: (s.date, s.start_time)):
        for prev in by_date[t.date]:
            if prev.clase_id != t.clase_id and _overlaps(prev, t):
                return prev, t
        by_date[t.date].append(t)
    return None


def _conflict_message(occupied: Slot) -> str:
    return (
        f"Se solapa con tu inscripción a «{occupied.activity_name} – "
        f"{occupied.turno_description}» del {occupied.date.strftime('%d/%m')} de "
        f"{occupied.start_time.strftime('%H:%M')} a {occupied.end_time.strftime('%H:%M')}."
    )


async def assert_no_schedule_conflict(
    session: AsyncSession, user_id: int, target_clase_ids: list[int]
) -> None:
    """Lanza 409 si las clases destino se pisan entre sí o con la ocupación del cliente.

    ``target_clase_ids`` son las clases que el cliente pasaría a ocupar (suscripción →
    clases futuras del turno; suelta → clases elegidas; waitlist → clases futuras del
    turno). Una clase que el cliente ya ocupa y que ES una de las destino no cuenta como
    conflicto (misma clase, mismo asiento: ej. convertir una suelta en abono).
    """
    if not target_clase_ids:
        return

    targets = await _load_target_slots(session, target_clase_ids)
    if not targets:
        return

    internal = _find_internal_overlap(targets)
    if internal is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Elegiste dos clases que se solapan en horario; revisá tu selección.",
        )

    target_ids = {t.clase_id for t in targets}
    from_date = min(t.date for t in targets)
    occupied_by_date: dict[date, list[Slot]] = defaultdict(list)
    for o in await _load_occupied_slots(session, user_id, from_date):
        if o.clase_id in target_ids:
            continue  # misma clase: auto-coincidencia, no es conflicto
        occupied_by_date[o.date].append(o)

    for t in targets:
        for o in occupied_by_date.get(t.date, ()):
            if _overlaps(t, o):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=_conflict_message(o),
                )
