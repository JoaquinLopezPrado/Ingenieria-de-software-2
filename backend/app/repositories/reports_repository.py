from collections import defaultdict
from datetime import date, datetime, time, timezone
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.attendance import AttendanceStatus
from app.models.activity import Activity as ActivityORM
from app.models.attendance import Attendance as AttendanceORM
from app.models.clase import Clase as ClaseORM
from app.models.payment import Payment as PaymentORM
from app.models.subscription import Subscription as SubscriptionORM
from app.models.turno import Turno as TurnoORM


def _utc(d: date, end: bool = False) -> datetime:
    t = time(23, 59, 59) if end else time(0, 0, 0)
    return datetime.combine(d, t, tzinfo=timezone.utc)


class ReportsRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_ingresos(
        self, desde: date, hasta: date
    ) -> List[Tuple[int, int, float]]:
        """Retorna lista de (mes, anio, total) para pagos en el rango."""
        rows = await self._session.execute(
            select(
                PaymentORM.month_snapshot,
                PaymentORM.year_snapshot,
                func.sum(PaymentORM.amount).label("total"),
            )
            .where(
                PaymentORM.confirmed_at >= _utc(desde),
                PaymentORM.confirmed_at <= _utc(hasta, end=True),
            )
            .group_by(PaymentORM.year_snapshot, PaymentORM.month_snapshot)
            .order_by(PaymentORM.year_snapshot, PaymentORM.month_snapshot)
        )
        return rows.all()

    async def get_ocupacion(
        self, desde: date, hasta: date
    ) -> List[Tuple[str, float]]:
        """Retorna lista de (franja_label, ocupacion_pct) agrupada por franja horaria."""
        turnos_rows = await self._session.execute(
            select(
                TurnoORM.id,
                TurnoORM.start_time,
                TurnoORM.end_time,
                TurnoORM.capacity,
            )
            .join(ClaseORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                ClaseORM.date >= desde,
                ClaseORM.date <= hasta,
                ClaseORM.is_active.is_(True),
                TurnoORM.is_active.is_(True),
            )
            .distinct()
        )
        turnos = turnos_rows.all()
        if not turnos:
            return []

        turno_ids = [t.id for t in turnos]

        sub_rows = await self._session.execute(
            select(
                SubscriptionORM.turno_id,
                func.count(SubscriptionORM.id).label("enrolled"),
            )
            .where(
                SubscriptionORM.turno_id.in_(turno_ids),
                SubscriptionORM.start_date <= hasta,
                or_(
                    SubscriptionORM.cancelled_at.is_(None),
                    SubscriptionORM.cancelled_at >= _utc(desde),
                ),
            )
            .group_by(SubscriptionORM.turno_id)
        )
        enrolled_by_turno = {r.turno_id: r.enrolled for r in sub_rows.all()}

        slot_enrolled: dict[tuple, int] = defaultdict(int)
        slot_capacity: dict[tuple, int] = defaultdict(int)

        for t in turnos:
            key = (t.start_time, t.end_time)
            slot_enrolled[key] += enrolled_by_turno.get(t.id, 0)
            slot_capacity[key] += t.capacity

        result = []
        for key in sorted(slot_capacity.keys()):
            start_t, end_t = key
            label = (
                f"{start_t.hour}:{start_t.minute:02d}"
                f"–{end_t.hour}:{end_t.minute:02d}"
            )
            cap = slot_capacity[key]
            pct = round(slot_enrolled[key] / cap * 100, 1) if cap > 0 else 0.0
            result.append((label, pct))

        return result

    async def get_ausencias(
        self, desde: date, hasta: date
    ) -> Tuple[List[Tuple[str, int]], int, int]:
        """Retorna (items: [(actividad, ausencias)], total_ausencias, total_registros)."""
        items_rows = await self._session.execute(
            select(
                ActivityORM.name,
                func.count(AttendanceORM.id).label("ausencias"),
            )
            .join(ClaseORM, ClaseORM.id == AttendanceORM.clase_id)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(
                AttendanceORM.status == AttendanceStatus.AUSENTE,
                ClaseORM.date >= desde,
                ClaseORM.date <= hasta,
            )
            .group_by(ActivityORM.name)
            .order_by(func.count(AttendanceORM.id).desc())
        )
        items = [(r.name, r.ausencias) for r in items_rows.all()]

        totals_row = await self._session.execute(
            select(func.count(AttendanceORM.id))
            .join(ClaseORM, ClaseORM.id == AttendanceORM.clase_id)
            .where(
                ClaseORM.date >= desde,
                ClaseORM.date <= hasta,
            )
        )
        total_registros = totals_row.scalar_one() or 0
        total_ausencias = sum(c for _, c in items)

        return items, total_ausencias, total_registros

    async def get_cancelaciones(
        self, desde: date, hasta: date
    ) -> Tuple[List[Tuple[str, int]], int]:
        """Retorna (items: [(actividad, cancelaciones)], total)."""
        rows = await self._session.execute(
            select(
                ActivityORM.name,
                func.count(SubscriptionORM.id).label("cancelaciones"),
            )
            .join(TurnoORM, TurnoORM.id == SubscriptionORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(
                SubscriptionORM.cancelled_at >= _utc(desde),
                SubscriptionORM.cancelled_at <= _utc(hasta, end=True),
            )
            .group_by(ActivityORM.name)
            .order_by(func.count(SubscriptionORM.id).desc())
        )
        items = [(r.name, r.cancelaciones) for r in rows.all()]
        total = sum(c for _, c in items)
        return items, total
