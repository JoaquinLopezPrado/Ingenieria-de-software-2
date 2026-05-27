from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.domain.enrollment import Enrollment, EnrollmentStatus, EnrollmentType, MyMonthlyEnrollment, MySingleEnrollment
from app.domain.payment import EnrollmentPaymentDetails
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.enrollment import Enrollment as EnrollmentORM, EnrollmentSlot as EnrollmentSlotORM
from app.models.turno import Turno as TurnoORM

_ACTIVE_STATUSES = [EnrollmentStatus.PENDING, EnrollmentStatus.CONFIRMED]


class AbstractEnrollmentRepository(ABC):

    @abstractmethod
    async def create_monthly(self, turno_id: int, user_id: int) -> Enrollment:
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
    async def get_monthly_by_user(self, user_id: int) -> list[MyMonthlyEnrollment]:
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
    # Inscripción mensual                                                  #
    # ------------------------------------------------------------------ #

    async def create_monthly(self, turno_id: int, user_id: int) -> Enrollment:
        turno = await self._lock_turno(turno_id)
        await self._check_turno_capacity(turno)
        await self._check_duplicate_monthly(turno_id, user_id)

        # Todas las clases del turno, ordenadas por id (orden fijo → sin deadlocks).
        all_clases = await self._lock_clases_of_turno(turno_id)
        if not all_clases:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El turno no tiene clases configuradas.",
            )

        today = date.today()
        future_clases = [c for c in all_clases if c.date >= today]
        if not future_clases:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No quedan clases futuras en este turno.",
            )

        existing_single_result = await self._session.execute(
            select(EnrollmentSlotORM.clase_id)
            .join(EnrollmentORM, EnrollmentORM.id == EnrollmentSlotORM.enrollment_id)
            .where(
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.SINGLE,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
                EnrollmentSlotORM.clase_id.in_([c.id for c in future_clases]),
            )
        )
        already_enrolled_ids = {row[0] for row in existing_single_result.all()}

        clases_con_cupo = []
        clases_excluidas = []
        for clase in future_clases:
            if clase.id in already_enrolled_ids:
                clases_excluidas.append(clase)
            elif await self._clase_tiene_cupo(clase):
                clases_con_cupo.append(clase)
            else:
                clases_excluidas.append(clase)

        if not clases_con_cupo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Todas las clases futuras de este turno tienen el cupo completo.",
            )

        precio_por_clase = Decimal(turno.price) / len(all_clases)
        amount = (precio_por_clase * len(clases_con_cupo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        enrollment_orm = EnrollmentORM(
            turno_id=turno_id,
            user_id=user_id,
            enrollment_type=EnrollmentType.MONTHLY,
            amount=amount,
            status=EnrollmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes),
        )
        self._session.add(enrollment_orm)
        await self._session.flush()

        for clase in clases_con_cupo:
            self._session.add(EnrollmentSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase.id))
        await self._session.flush()

        return self._to_domain(enrollment_orm, [c.id for c in clases_excluidas])

    # ------------------------------------------------------------------ #
    # Inscripción a clase suelta                                           #
    # ------------------------------------------------------------------ #

    async def create_single(self, clase_id: int, user_id: int) -> Enrollment:
        clase = await self._lock_clase(clase_id)
        await self._check_clase_capacity(clase)
        await self._check_duplicate_single(clase_id, user_id)

        turno = await self._get_turno(clase.turno_id)
        total_clases = await self._count_active_clases(clase.turno_id)
        precio_por_clase = (Decimal(turno.price) / total_clases).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        enrollment_orm = EnrollmentORM(
            turno_id=clase.turno_id,
            user_id=user_id,
            enrollment_type=EnrollmentType.SINGLE,
            amount=precio_por_clase,
            status=EnrollmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes),
        )
        self._session.add(enrollment_orm)
        await self._session.flush()

        self._session.add(EnrollmentSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase_id))
        await self._session.flush()

        return self._to_domain(enrollment_orm, [])

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
                TurnoORM.month,
                TurnoORM.year,
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
            month=row[10],
            year=row[11],
            enrollment_type=row[12],
        )

    async def update_payment(self, enrollment_id: int, new_status: EnrollmentStatus, payment_id: str) -> bool:
        result = await self._session.execute(
            update(EnrollmentORM)
            .where(EnrollmentORM.id == enrollment_id, EnrollmentORM.status == EnrollmentStatus.PENDING)
            .values(status=new_status, payment_id=payment_id)
        )
        return result.rowcount > 0

    # ------------------------------------------------------------------ #
    # Consultas por usuario                                                #
    # ------------------------------------------------------------------ #

    async def get_monthly_by_user(self, user_id: int) -> list[MyMonthlyEnrollment]:
        result = await self._session.execute(
            select(EnrollmentORM)
            .options(
                selectinload(EnrollmentORM.turno).selectinload(TurnoORM.activity),
                selectinload(EnrollmentORM.turno).selectinload(TurnoORM.days),
            )
            .where(
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.MONTHLY,
                EnrollmentORM.status.in_(_ACTIVE_STATUSES),
            )
            .order_by(EnrollmentORM.created_at.desc())
        )
        return [
            MyMonthlyEnrollment(
                enrollment_id=e.id,
                status=e.status,
                amount=e.amount,
                expires_at=e.expires_at,
                created_at=e.created_at,
                turno_id=e.turno.id,
                turno_description=e.turno.description,
                month=e.turno.month,
                year=e.turno.year,
                start_time=e.turno.start_time,
                end_time=e.turno.end_time,
                instructor=e.turno.instructor,
                activity_name=e.turno.activity.name,
                days=[d.dia for d in e.turno.days],
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

    async def _lock_clases_of_turno(self, turno_id: int) -> list[ClaseORM]:
        """Bloquea todas las clases del turno en orden ascendente de id para evitar deadlocks."""
        result = await self._session.execute(
            select(ClaseORM)
            .where(ClaseORM.turno_id == turno_id, ClaseORM.is_active == True)
            .order_by(ClaseORM.id)
            .with_for_update()
        )
        return list(result.scalars().all())

    async def _check_turno_capacity(self, turno: TurnoORM) -> None:
        result = await self._session.execute(
            select(func.count(EnrollmentORM.id)).where(
                EnrollmentORM.turno_id == turno.id,
                EnrollmentORM.enrollment_type == EnrollmentType.MONTHLY,
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

    async def _count_active_clases(self, turno_id: int) -> int:
        result = await self._session.execute(
            select(func.count(ClaseORM.id)).where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
            )
        )
        return result.scalar_one()

    async def _check_duplicate_monthly(self, turno_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(EnrollmentORM).where(
                EnrollmentORM.turno_id == turno_id,
                EnrollmentORM.user_id == user_id,
                EnrollmentORM.enrollment_type == EnrollmentType.MONTHLY,
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
            detail="Ya tenés una inscripción activa para este turno.",
        )

    async def _check_duplicate_single(self, clase_id: int, user_id: int) -> None:
        """Rechaza si el usuario ya tiene un slot activo para esta clase (sea por mensual o suelta)."""
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
            detail="Ya tenés un lugar reservado una clase de este turno.",
        )

    def _to_domain(self, orm: EnrollmentORM, excluded_clase_ids: list[int]) -> Enrollment:
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
            excluded_clase_ids=excluded_clase_ids,
        )
