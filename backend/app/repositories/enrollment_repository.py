from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.domain.enrollment import Enrollment, EnrollmentStatus, EnrollmentType, MySubscriptionEnrollment, MySingleEnrollment
from app.domain.payment import EnrollmentPaymentDetails
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.enrollment import Enrollment as EnrollmentORM, EnrollmentSlot as EnrollmentSlotORM
from app.models.turno import Turno as TurnoORM

_ACTIVE_STATUSES = [EnrollmentStatus.PENDING, EnrollmentStatus.CONFIRMED]


class AbstractEnrollmentRepository(ABC):

    @abstractmethod
    async def create_subscription(self, turno_id: int, user_id: int) -> Enrollment:
        raise NotImplementedError

    @abstractmethod
    async def create_single(self, clase_id: int, user_id: int) -> Enrollment:
        raise NotImplementedError

    @abstractmethod
    async def get_payment_details(self, enrollment_id: int) -> EnrollmentPaymentDetails:
        raise NotImplementedError

    @abstractmethod
    async def update_payment(self, enrollment_id: int, new_status: EnrollmentStatus, payment_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_subscriptions_by_user(self, user_id: int) -> list[MySubscriptionEnrollment]:
        raise NotImplementedError

    @abstractmethod
    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        raise NotImplementedError

    @abstractmethod
    async def cancel_expired(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def cancel_pending(self, enrollment_id: int, user_id: int) -> bool:
        raise NotImplementedError


class EnrollmentRepository(AbstractEnrollmentRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    # ------------------------------------------------------------------ #
    # Suscripción mensual                                                  #
    # ------------------------------------------------------------------ #

    async def create_subscription(self, turno_id: int, user_id: int) -> Enrollment:
        turno = await self._lock_turno(turno_id)
        await self._check_turno_capacity(turno)
        await self._check_duplicate_subscription(turno_id, user_id)

        future_clases = await self._get_future_clases(turno_id)
        if not future_clases:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El turno no tiene clases futuras disponibles.",
            )

        today = date.today()
        this_month_clases = [c for c in future_clases if c.date.month == today.month and c.date.year == today.year]
        if this_month_clases:
            payment_clases = this_month_clases
        else:
            # Tomar el próximo mes disponible entre las clases futuras
            first_key = (future_clases[0].date.month, future_clases[0].date.year)
            payment_clases = [c for c in future_clases if (c.date.month, c.date.year) == first_key]

        amount = Decimal(turno.class_price) * len(payment_clases)

        enrollment_orm = EnrollmentORM(
            turno_id=turno_id,
            user_id=user_id,
            enrollment_type=EnrollmentType.SUBSCRIPTION,
            amount=amount,
            status=EnrollmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes),
        )
        self._session.add(enrollment_orm)
        await self._session.flush()

        for clase in future_clases:
            self._session.add(EnrollmentSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase.id))
        await self._session.flush()

        return self._to_domain(enrollment_orm)

    # ------------------------------------------------------------------ #
    # Inscripción a clase suelta                                           #
    # ------------------------------------------------------------------ #

    async def create_single(self, clase_id: int, user_id: int) -> Enrollment:
        clase = await self._lock_clase(clase_id)
        await self._check_clase_capacity(clase)
        turno = await self._get_turno(clase.turno_id)
        await self._check_schedule_conflict_single(user_id, clase.date, turno.start_time, turno.end_time)
        await self._check_duplicate_single(clase_id, user_id)

        amount = Decimal(turno.class_price)

        enrollment_orm = EnrollmentORM(
            turno_id=clase.turno_id,
            user_id=user_id,
            enrollment_type=EnrollmentType.SINGLE,
            amount=amount,
            status=EnrollmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes),
        )
        self._session.add(enrollment_orm)
        await self._session.flush()

        self._session.add(EnrollmentSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase_id))
        await self._session.flush()

        return self._to_domain(enrollment_orm)

    # ------------------------------------------------------------------ #
    # Pagos                                                                #
    # ------------------------------------------------------------------ #

    async def get_payment_details(self, enrollment_id: int) -> EnrollmentPaymentDetails:
        num_classes_subq = (
            select(func.count(EnrollmentSlotORM.id))
            .where(EnrollmentSlotORM.enrollment_id == EnrollmentORM.id)
            .correlate(EnrollmentORM)
            .scalar_subquery()
        )
        result = await self._session.execute(
            select(
                EnrollmentORM.id,
                EnrollmentORM.user_id,
                EnrollmentORM.status,
                EnrollmentORM.amount,
                ActivityORM.name,
                TurnoORM.description,
                EnrollmentORM.expires_at,
                TurnoORM.class_price,
                num_classes_subq.label("num_classes"),
                TurnoORM.activity_id,
                EnrollmentORM.enrollment_type,
            )
            .join(TurnoORM, TurnoORM.id == EnrollmentORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(EnrollmentORM.id == enrollment_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inscripción no encontrada.",
            )
        today = date.today()
        return EnrollmentPaymentDetails(
            enrollment_id=row[0],
            user_id=row[1],
            status=row[2],
            price=row[3],
            activity_name=row[4],
            turno_description=row[5],
            expires_at=row[6],
            class_price_snapshot=row[7],
            num_classes_snapshot=row[8] or 1,
            activity_id=row[9],
            month=today.month,
            year=today.year,
            enrollment_type=row[10],
        )

    async def update_payment(self, enrollment_id: int, new_status: EnrollmentStatus, payment_id: str) -> bool:
        values: dict = {"status": new_status, "payment_id": payment_id}
        if new_status == EnrollmentStatus.CONFIRMED:
            values["last_payment_date"] = date.today()
        result = await self._session.execute(
            update(EnrollmentORM)
            .where(EnrollmentORM.id == enrollment_id, EnrollmentORM.status == EnrollmentStatus.PENDING)
            .values(**values)
        )
        return result.rowcount > 0

    # ------------------------------------------------------------------ #
    # Consultas por usuario                                                #
    # ------------------------------------------------------------------ #

    async def get_subscriptions_by_user(self, user_id: int) -> list[MySubscriptionEnrollment]:
        result = await self._session.execute(
            select(EnrollmentORM)
            .options(
                selectinload(EnrollmentORM.turno).selectinload(TurnoORM.activity),
                selectinload(EnrollmentORM.turno).selectinload(TurnoORM.days),
            )
            .where(
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.SUBSCRIPTION,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
            .order_by(EnrollmentORM.created_at.desc())
        )
        return [
            MySubscriptionEnrollment(
                enrollment_id=e.id,
                status=e.status,
                amount=e.amount,
                expires_at=e.expires_at,
                created_at=e.created_at,
                turno_id=e.turno.id,
                turno_description=e.turno.description,
                start_time=e.turno.start_time,
                end_time=e.turno.end_time,
                instructor=e.turno.instructor,
                activity_name=e.turno.activity.name,
                days=[d.dia for d in e.turno.days],
                last_payment_date=e.last_payment_date,
            )
            for e in result.scalars()
        ]

    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        result = await self._session.execute(
            select(EnrollmentORM)
            .options(
                selectinload(EnrollmentORM.slots).selectinload(EnrollmentSlotORM.clase),
                selectinload(EnrollmentORM.turno).selectinload(TurnoORM.activity),
            )
            .where(
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.SINGLE,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
            .order_by(EnrollmentORM.created_at.desc())
        )
        enrollments = []
        for e in result.scalars():
            clase = e.slots[0].clase
            enrollments.append(MySingleEnrollment(
                enrollment_id=e.id,
                status=e.status,
                amount=e.amount,
                expires_at=e.expires_at,
                created_at=e.created_at,
                turno_id=e.turno_id,
                clase_id=clase.id,
                clase_date=clase.date,
                start_time=e.turno.start_time,
                end_time=e.turno.end_time,
                turno_description=e.turno.description,
                instructor=e.turno.instructor,
                activity_name=e.turno.activity.name,
            ))
        return enrollments

    async def cancel_expired(self) -> int:
        result = await self._session.execute(
            update(EnrollmentORM)
            .where(
                EnrollmentORM.status == EnrollmentStatus.PENDING,
                EnrollmentORM.expires_at.isnot(None),
                EnrollmentORM.expires_at <= datetime.now(timezone.utc),
            )
            .values(status=EnrollmentStatus.CANCELLED)
        )
        return result.rowcount

    async def cancel_pending(self, enrollment_id: int, user_id: int) -> bool:
        result = await self._session.execute(
            update(EnrollmentORM)
            .where(
                EnrollmentORM.id == enrollment_id,
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.status == EnrollmentStatus.PENDING,
            )
            .values(status=EnrollmentStatus.CANCELLED)
        )
        return result.rowcount > 0

    # ------------------------------------------------------------------ #
    # Helpers de lock y validación                                         #
    # ------------------------------------------------------------------ #

    async def _lock_turno(self, turno_id: int) -> TurnoORM:
        result = await self._session.execute(
            select(TurnoORM).where(TurnoORM.id == turno_id).with_for_update()
        )
        turno = result.scalar_one_or_none()
        if turno is None or not turno.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El turno no existe o no está disponible.",
            )
        return turno

    async def _get_turno(self, turno_id: int) -> TurnoORM:
        result = await self._session.execute(
            select(TurnoORM).where(TurnoORM.id == turno_id)
        )
        return result.scalar_one()

    async def _lock_clase(self, clase_id: int) -> ClaseORM:
        result = await self._session.execute(
            select(ClaseORM).where(ClaseORM.id == clase_id).with_for_update()
        )
        clase = result.scalar_one_or_none()
        if clase is None or not clase.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La clase no existe o no está disponible.",
            )
        return clase

    async def _get_future_clases(self, turno_id: int) -> list[ClaseORM]:
        today = date.today()
        result = await self._session.execute(
            select(ClaseORM)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date >= today,
            )
            .order_by(ClaseORM.id)
            .with_for_update()
        )
        return list(result.scalars().all())

    async def _check_turno_capacity(self, turno: TurnoORM) -> None:
        result = await self._session.execute(
            select(func.count(EnrollmentORM.id)).where(
                EnrollmentORM.turno_id == turno.id,
                EnrollmentORM.enrollment_type == EnrollmentType.SUBSCRIPTION,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
        )
        if result.scalar_one() >= turno.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay lugares disponibles en este turno.",
            )

    async def _clase_tiene_cupo(self, clase: ClaseORM) -> bool:
        result = await self._session.execute(
            select(func.count(EnrollmentSlotORM.id))
            .join(EnrollmentORM, EnrollmentORM.id == EnrollmentSlotORM.enrollment_id)
            .where(
                EnrollmentSlotORM.clase_id == clase.id,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
        )
        return result.scalar_one() < clase.capacity

    async def _check_clase_capacity(self, clase: ClaseORM) -> None:
        if not await self._clase_tiene_cupo(clase):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay lugares disponibles en esta clase.",
            )

    async def _check_duplicate_subscription(self, turno_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(EnrollmentORM).where(
                EnrollmentORM.turno_id == turno_id,
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.SUBSCRIPTION,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return

        if (
            existing.status == EnrollmentStatus.PENDING
            and existing.expires_at is not None
            and existing.expires_at <= datetime.now(timezone.utc)
        ):
            existing.status = EnrollmentStatus.CANCELLED
            return

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés una suscripción activa para este turno.",
        )

    async def _check_schedule_conflict_single(
        self, user_id: int, clase_date: date, start_time: time, end_time: time
    ) -> None:
        result = await self._session.execute(
            select(EnrollmentORM)
            .join(EnrollmentSlotORM, EnrollmentSlotORM.enrollment_id == EnrollmentORM.id)
            .join(ClaseORM, ClaseORM.id == EnrollmentSlotORM.clase_id)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .where(
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.SINGLE,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
                ClaseORM.date == clase_date,
                TurnoORM.start_time < end_time,
                TurnoORM.end_time > start_time,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return

        if (
            existing.status == EnrollmentStatus.PENDING
            and existing.expires_at is not None
            and existing.expires_at <= datetime.now(timezone.utc)
        ):
            existing.status = EnrollmentStatus.CANCELLED
            return

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés otra clase suelta en ese día y horario.",
        )

    async def _check_duplicate_single(self, clase_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(EnrollmentORM)
            .join(EnrollmentSlotORM, EnrollmentSlotORM.enrollment_id == EnrollmentORM.id)
            .where(
                EnrollmentSlotORM.clase_id == clase_id,
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return

        if (
            existing.status == EnrollmentStatus.PENDING
            and existing.expires_at is not None
            and existing.expires_at <= datetime.now(timezone.utc)
        ):
            existing.status = EnrollmentStatus.CANCELLED
            return

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés un lugar reservado en esta clase.",
        )

    def _to_domain(self, orm: EnrollmentORM) -> Enrollment:
        return Enrollment(
            id=orm.id,
            turno_id=orm.turno_id,
            user_id=orm.user_id,
            enrollment_type=orm.enrollment_type,
            amount=orm.amount,
            status=orm.status,
            expires_at=orm.expires_at,
            payment_id=orm.payment_id,
            created_at=orm.created_at,
            last_payment_date=orm.last_payment_date,
        )
