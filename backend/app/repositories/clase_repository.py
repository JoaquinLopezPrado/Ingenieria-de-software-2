import calendar
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, or_, select, union, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.clase import Clase, ClaseDetalle, ClaseHoy
from app.models.activity import Activity as ActivityORM
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
    async def create_many(
        self, turno_id: int, dates: List[date], capacity: int, start_time: time, end_time: time
    ) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    async def get_last_date(self, turno_id: int) -> Optional[date]:
        raise NotImplementedError

    @abstractmethod
    async def update_future_time(
        self, turno_id: int, start_time: time, end_time: time, from_date: date
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def list_future_active(self, turno_id: int, from_date: date) -> List[tuple]:
        raise NotImplementedError

    @abstractmethod
    async def reactivate_turno_baja_clases(
        self, turno_id: int, from_date: date, reason: str
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def update_schedule(
        self, clase_id: int, new_date: date, start_time: time, end_time: time, capacity: int
    ) -> ClaseORM:
        raise NotImplementedError

    @abstractmethod
    async def list_by_activity(self, activity_id: int) -> List[Clase]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_turno(self, turno_id: int) -> List[ClaseDetalle]:
        raise NotImplementedError

    @abstractmethod
    async def list_hoy(self, today: date) -> List[ClaseHoy]:
        raise NotImplementedError

    @abstractmethod
    async def get_max_enrolled_future(self, turno_id: int, from_date: date) -> int:
        raise NotImplementedError

    @abstractmethod
    async def update_future_capacity(self, turno_id: int, capacity: int, from_date: date) -> int:
        raise NotImplementedError


class ClaseRepository(AbstractClaseRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_many(
        self, turno_id: int, dates: List[date], capacity: int, start_time: time, end_time: time
    ) -> List[int]:
        clases = [
            ClaseORM(
                turno_id=turno_id,
                date=d,
                start_time=start_time,
                end_time=end_time,
                capacity=capacity,
                is_active=True,
            )
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

    async def update_future_time(
        self, turno_id: int, start_time: time, end_time: time, from_date: date
    ) -> int:
        result = await self._session.execute(
            update(ClaseORM)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date > from_date,
            )
            .values(start_time=start_time, end_time=end_time)
        )
        return result.rowcount

    async def get_max_enrolled_future(self, turno_id: int, from_date: date) -> int:
        from app.repositories.capacity import occupied_subq
        enrolled_col = occupied_subq(ClaseORM.turno_id, ClaseORM.id, ClaseORM.date)
        result = await self._session.execute(
            select(func.max(enrolled_col))
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date > from_date,
            )
        )
        return result.scalar_one() or 0

    async def update_future_capacity(self, turno_id: int, capacity: int, from_date: date) -> int:
        result = await self._session.execute(
            update(ClaseORM)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date > from_date,
            )
            .values(capacity=capacity)
        )
        return result.rowcount

    async def list_future_active(self, turno_id: int, from_date: date) -> List[tuple]:
        result = await self._session.execute(
            select(ClaseORM.id, ClaseORM.date)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date > from_date,
            )
            .order_by(ClaseORM.date)
        )
        return [(row.id, row.date) for row in result]

    async def reactivate_turno_baja_clases(
        self, turno_id: int, from_date: date, reason: str
    ) -> int:
        """Reabre las clases futuras que canceló la baja del turno (match por razón),
        dejando intactas las cancelaciones individuales y las clases ya pasadas."""
        result = await self._session.execute(
            update(ClaseORM)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.cancelled_at.isnot(None),
                ClaseORM.cancelled_reason == reason,
                ClaseORM.date > from_date,
            )
            .values(
                is_active=True,
                cancelled_at=None,
                cancelled_reason=None,
                cancelled_by_id=None,
            )
        )
        return result.rowcount

    async def update_schedule(
        self, clase_id: int, new_date: date, start_time: time, end_time: time, capacity: int
    ) -> ClaseORM:
        clase = await self._session.get(ClaseORM, clase_id)
        if clase is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada.")
        if clase.cancelled_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede modificar una clase cancelada.",
            )
        now_art = datetime.now(timezone(timedelta(hours=-3)))
        today = now_art.date()
        if clase.date < today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede modificar una clase que ya pasó.",
            )
        if new_date < today:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La nueva fecha no puede ser anterior a hoy.",
            )
        if new_date == today and start_time < now_art.time():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede programar la clase en un horario que ya pasó.",
            )
        duplicate = await self._session.execute(
            select(ClaseORM.id).where(
                ClaseORM.turno_id == clase.turno_id,
                ClaseORM.date == new_date,
                ClaseORM.is_active == True,
                ClaseORM.id != clase_id,
            )
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe otra clase de este turno programada para esa fecha.",
            )
        turno = (await self._session.execute(
            select(TurnoORM).options(selectinload(TurnoORM.salon)).where(TurnoORM.id == clase.turno_id)
        )).scalar_one()
        if turno.salon is not None and capacity > turno.salon.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"El cupo de la clase ({capacity}) supera la capacidad física "
                    f"del salón «{turno.salon.name}» ({turno.salon.capacity})."
                ),
            )
        enrolled = await self._count_enrolled(clase.turno_id, clase_id, clase.date)
        if enrolled > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede modificar una clase que ya tiene inscriptos.",
            )
        clase.date = new_date
        clase.start_time = start_time
        clase.end_time = end_time
        clase.capacity = capacity
        await self._session.flush()
        return clase

    async def _count_enrolled(self, turno_id: int, clase_id: int, clase_date: date) -> int:
        """Usuarios únicos que ocupan un lugar en la clase: abonados activos en la
        fecha + sueltas activas. Misma fórmula que la capacidad (ver capacity.py)."""
        sub_subs = (
            select(SubscriptionORM.user_id)
            .where(
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.start_date <= clase_date,
                or_(SubscriptionORM.ends_on.is_(None), clase_date <= SubscriptionORM.ends_on),
            )
        )
        sub_singles = (
            select(SingleEnrollmentORM.user_id)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .where(
                SingleSlotORM.clase_id == clase_id,
                SingleEnrollmentORM.status.in_(ACTIVE_SINGLE_STATUSES),
            )
        )
        combined = union(sub_subs, sub_singles).subquery()
        result = await self._session.execute(select(func.count()).select_from(combined))
        return result.scalar_one()

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

        if include_past:
            # Vista admin: todas las clases del turno (activas y canceladas), sin recorte de fecha.
            clase_filter = (ClaseORM.is_active == True) | (ClaseORM.cancelled_at.isnot(None))
            date_filters = []
        else:
            # Vista pública: solo clases futuras activas, hasta el fin del mes siguiente.
            next_month = today.month % 12 + 1
            next_month_year = today.year + (1 if today.month == 12 else 0)
            end_date = date(next_month_year, next_month, calendar.monthrange(next_month_year, next_month)[1])
            clase_filter = ClaseORM.is_active == True
            date_filters = [
                ClaseORM.date <= end_date,
                or_(
                    ClaseORM.date > today,
                    and_(ClaseORM.date == today, ClaseORM.start_time > now_art.time()),
                ),
            ]

        result = await self._session.execute(
            select(
                ClaseORM,
                func.coalesce(enrolled_per_clase.c.cnt, 0).label("enrolled"),
                func.coalesce(attendance_per_clase.c.presentes, 0).label("presentes_count"),
            )
            .outerjoin(enrolled_per_clase, enrolled_per_clase.c.clase_id == ClaseORM.id)
            .outerjoin(attendance_per_clase, attendance_per_clase.c.clase_id == ClaseORM.id)
            .where(
                ClaseORM.turno_id == turno_id,
                clase_filter,
                *date_filters,
            )
            .order_by(ClaseORM.date)
        )
        return [
            ClaseDetalle(
                id=row.Clase.id,
                turno_id=row.Clase.turno_id,
                date=row.Clase.date,
                start_time=row.Clase.start_time,
                end_time=row.Clase.end_time,
                capacity=row.Clase.capacity,
                enrolled=row.enrolled,
                presentes_count=row.presentes_count,
                is_active=row.Clase.is_active,
                cancelled_reason=row.Clase.cancelled_reason,
                cancelled_at=row.Clase.cancelled_at,
            )
            for row in result
        ]

    async def list_hoy(self, today: date) -> List[ClaseHoy]:
        result = await self._session.execute(
            select(
                ClaseORM.id,
                ActivityORM.name,
                TurnoORM.instructor,
                ClaseORM.start_time,
                ClaseORM.end_time,
                ClaseORM.capacity,
                ClaseORM.is_active,
            )
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(ClaseORM.date == today)
            .order_by(ClaseORM.start_time)
        )
        return [
            ClaseHoy(
                clase_id=row[0],
                activity_name=row[1],
                instructor=row[2],
                start_time=row[3],
                end_time=row[4],
                capacity=row[5],
                is_active=row[6],
            )
            for row in result.all()
        ]

    def _to_domain(self, orm: ClaseORM) -> Clase:
        return Clase(
            id=orm.id,
            turno_id=orm.turno_id,
            date=orm.date,
            capacity=orm.capacity,
            is_active=orm.is_active,
        )
