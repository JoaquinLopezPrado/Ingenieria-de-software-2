import calendar
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, case, func, or_, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.clase import Clase, ClaseDetalle
from app.domain.subscription import OCCUPYING_SUBSCRIPTION_STATUSES
from app.domain.attendance import AttendanceStatus
from app.models.attendance import Attendance as AttendanceORM
from app.models.clase import Clase as ClaseORM
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM
from app.models.turno import Turno as TurnoORM
from app.repositories.capacity import ACTIVE_SINGLE_STATUSES


class AbstractClaseRepository(ABC):

    @abstractmethod
    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    async def get_last_date(self, turno_id: int) -> Optional[date]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_activity(self, activity_id: int) -> List[Clase]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
        raise NotImplementedError


class ClaseRepository(AbstractClaseRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_many(self, turno_id: int, dates: List[date], capacity: int) -> List[int]:
        clases = [
            ClaseORM(turno_id=turno_id, date=d, capacity=capacity, is_active=True)
            for d in dates
        ]
        self._session.add_all(clases)
        await self._session.flush()
        return [c.id for c in clases]

    async def get_last_date(self, turno_id: int) -> Optional[date]:
        result = await self._session.execute(
            select(func.max(ClaseORM.date)).where(ClaseORM.turno_id == turno_id)
        )
        return result.scalar_one_or_none()

    async def list_by_activity(self, activity_id: int) -> List[Clase]:
        today = date.today()
        result = await self._session.execute(
            select(ClaseORM)
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .where(
                TurnoORM.activity_id == activity_id,
                TurnoORM.is_active == True,
                ClaseORM.is_active == True,
                ClaseORM.date >= today,
            )
            .order_by(ClaseORM.date)
        )
        return [self._to_domain(orm) for orm in result.scalars()]

    async def list_by_turno(self, turno_id: int, include_past: bool = False) -> List[ClaseDetalle]:
        now_art = datetime.now(timezone(timedelta(hours=-3)))
        today = now_art.date()
        next_month = today.month % 12 + 1
        next_month_year = today.year + (1 if today.month == 12 else 0)
        end_date = date(next_month_year, next_month, calendar.monthrange(next_month_year, next_month)[1])

        # Non-correlated enrolled count via UNION + GROUP BY + LEFT JOIN
        sub_subs = (
            select(ClaseORM.id.label("clase_id"), SubscriptionORM.user_id.label("user_id"))
            .join(SubscriptionORM, SubscriptionORM.turno_id == ClaseORM.turno_id)
            .where(
                ClaseORM.turno_id == turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.start_date <= ClaseORM.date,
                or_(SubscriptionORM.ends_on.is_(None), ClaseORM.date <= SubscriptionORM.ends_on),
            )
        )
        sub_singles = (
            select(SingleSlotORM.clase_id.label("clase_id"), SingleEnrollmentORM.user_id.label("user_id"))
            .join(SingleEnrollmentORM, SingleEnrollmentORM.id == SingleSlotORM.enrollment_id)
            .join(ClaseORM, ClaseORM.id == SingleSlotORM.clase_id)
            .where(
                ClaseORM.turno_id == turno_id,
                SingleEnrollmentORM.status.in_(ACTIVE_SINGLE_STATUSES),
            )
        )
        combined = union(sub_subs, sub_singles).subquery()
        enrolled_per_clase = (
            select(combined.c.clase_id, func.count().label("cnt"))
            .group_by(combined.c.clase_id)
            .subquery()
        )

        attendance_per_clase = (
            select(
                AttendanceORM.clase_id,
                func.count(case((AttendanceORM.status == AttendanceStatus.PRESENTE, 1))).label("presentes"),
            )
            .group_by(AttendanceORM.clase_id)
            .subquery()
        )

        date_filters = [ClaseORM.date <= end_date]
        if include_past:
            three_months_ago = today.replace(day=1)
            for _ in range(3):
                if three_months_ago.month == 1:
                    three_months_ago = three_months_ago.replace(year=three_months_ago.year - 1, month=12)
                else:
                    three_months_ago = three_months_ago.replace(month=three_months_ago.month - 1)
            date_filters.append(ClaseORM.date >= three_months_ago)
        else:
            date_filters.append(
                or_(
                    ClaseORM.date > today,
                    and_(ClaseORM.date == today, TurnoORM.start_time > now_art.time()),
                )
            )

        result = await self._session.execute(
            select(
                ClaseORM, TurnoORM.start_time, TurnoORM.end_time,
                func.coalesce(enrolled_per_clase.c.cnt, 0).label("enrolled"),
                func.coalesce(attendance_per_clase.c.presentes, 0).label("presentes_count"),
            )
            .join(TurnoORM, ClaseORM.turno_id == TurnoORM.id)
            .outerjoin(enrolled_per_clase, enrolled_per_clase.c.clase_id == ClaseORM.id)
            .outerjoin(attendance_per_clase, attendance_per_clase.c.clase_id == ClaseORM.id)
            .where(
                ClaseORM.turno_id == turno_id,
                # Mostrar clases activas + canceladas (is_active=False por cancelación tiene cancelled_at).
                # Las inactivas por otras razones (sin cancelled_at) no se muestran.
                (ClaseORM.is_active == True) | (ClaseORM.cancelled_at.isnot(None)),
                *date_filters,
            )
            .order_by(ClaseORM.date)
        )
        return [
            ClaseDetalle(
                id=row.Clase.id,
                turno_id=row.Clase.turno_id,
                date=row.Clase.date,
                start_time=row.start_time,
                end_time=row.end_time,
                capacity=row.Clase.capacity,
                enrolled=row.enrolled,
                presentes_count=row.presentes_count,
                is_active=row.Clase.is_active,
                cancelled_reason=row.Clase.cancelled_reason,
                cancelled_at=row.Clase.cancelled_at,
            )
            for row in result
        ]

    def _to_domain(self, orm: ClaseORM) -> Clase:
        return Clase(
            id=orm.id,
            turno_id=orm.turno_id,
            date=orm.date,
            capacity=orm.capacity,
            is_active=orm.is_active,
        )
