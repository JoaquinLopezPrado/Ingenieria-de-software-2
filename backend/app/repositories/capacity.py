"""Fórmula única de capacidad, compartida por todos los repositorios.

    cupo(clase) = clase.capacity
                − suscripciones que ocupan asiento en el turno
                − slots sueltos activos en esa clase

Las suscripciones NO materializan slots: su ocupación se cuenta directamente sobre
la tabla ``subscriptions``. Las clases sueltas sí usan slots por fecha puntual.
"""
from sqlalchemy import func, or_, select, union

from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import OCCUPYING_SUBSCRIPTION_STATUSES
from app.models.clase import Clase as ClaseORM
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM

# Estados de inscripción suelta que ocupan un lugar en la clase.
ACTIVE_SINGLE_STATUSES = (
    SingleEnrollmentStatus.PENDING,
    SingleEnrollmentStatus.CONFIRMED,
    SingleEnrollmentStatus.DEPOSIT_PAID,
)


def subscription_covers(ref_date):
    """Condición: la suscripción cubre ``ref_date`` (dentro de [start_date, ends_on]).

    ``ref_date`` puede ser un ``date`` Python (consulta a nivel turno / "hoy") o una
    columna (``ClaseORM.date``) para capacidad por clase. Una baja programada
    (``ends_on`` seteada) libera el asiento recién para las fechas posteriores a
    ``ends_on``: el saliente sigue ocupando su período pagado.
    """
    return (
        SubscriptionORM.start_date <= ref_date,
        or_(SubscriptionORM.ends_on.is_(None), ref_date <= SubscriptionORM.ends_on),
    )


def active_subscriptions_subq(turno_id_col, ref_date):
    """Subquery escalar: suscripciones que ocupan el turno en ``ref_date``."""
    return (
        select(func.count(SubscriptionORM.id))
        .where(
            SubscriptionORM.turno_id == turno_id_col,
            SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
            *subscription_covers(ref_date),
        )
        .scalar_subquery()
    )


def active_single_slots_subq(clase_id_col):
    """Subquery escalar: slots sueltos activos en la clase dada."""
    return (
        select(func.count(SingleSlotORM.id))
        .join(SingleEnrollmentORM, SingleEnrollmentORM.id == SingleSlotORM.enrollment_id)
        .where(
            SingleSlotORM.clase_id == clase_id_col,
            SingleEnrollmentORM.status.in_(ACTIVE_SINGLE_STATUSES),
        )
        .scalar_subquery()
    )


def occupied_subq(clase_turno_id_col, clase_id_col, clase_date_col):
    """Usuarios únicos que ocupan un cupo: abonados activos UNION sueltos activos.

    UNION (sin ALL) elimina duplicados: un usuario con abono Y clase suelta en la misma
    fecha cuenta solo una vez, evitando el doble conteo al suscribirse mensualmente.
    """
    sub_subs = (
        select(SubscriptionORM.user_id)
        .where(
            SubscriptionORM.turno_id == clase_turno_id_col,
            SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
            *subscription_covers(clase_date_col),
        )
        .correlate_except(SubscriptionORM)
    )
    sub_singles = (
        select(SingleEnrollmentORM.user_id)
        .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
        .where(
            SingleSlotORM.clase_id == clase_id_col,
            SingleEnrollmentORM.status.in_(ACTIVE_SINGLE_STATUSES),
        )
        .correlate_except(SingleEnrollmentORM, SingleSlotORM)
    )
    combined = union(sub_subs, sub_singles).lateral()
    return select(func.count()).select_from(combined).scalar_subquery()
