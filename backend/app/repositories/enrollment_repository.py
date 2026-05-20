from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enrollment import Enrollment, EnrollmentStatus, EnrollmentType
from app.domain.payment import EnrollmentPaymentDetails
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.enrollment import Enrollment as EnrollmentORM, EnrollmentSlot as EnrollmentSlotORM
from app.models.turno import Turno as TurnoORM

_ACTIVE_STATUSES = [EnrollmentStatus.PENDING, EnrollmentStatus.CONFIRMED]
_TTL_MINUTES = 10


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
    async def update_payment(self, enrollment_id: int, new_status: EnrollmentStatus, payment_id: str) -> None:
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

        clases_con_cupo = []
        clases_sin_cupo = []
        for clase in future_clases:
            if await self._clase_tiene_cupo(clase):
                clases_con_cupo.append(clase)
            else:
                clases_sin_cupo.append(clase)

        precio_por_clase = Decimal(turno.price) / len(all_clases)
        amount = (precio_por_clase * len(clases_con_cupo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        enrollment_orm = EnrollmentORM(
            turno_id=turno_id,
            user_id=user_id,
            enrollment_type=EnrollmentType.MONTHLY,
            amount=amount,
            status=EnrollmentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=_TTL_MINUTES),
        )
        self._session.add(enrollment_orm)
        await self._session.flush()

        for clase in clases_con_cupo:
            self._session.add(EnrollmentSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase.id))
        await self._session.flush()

        return self._to_domain(enrollment_orm, [c.id for c in clases_sin_cupo])

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
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=_TTL_MINUTES),
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
        result = await self._session.execute(
            select(
                EnrollmentORM.id,
                EnrollmentORM.user_id,
                EnrollmentORM.status,
                EnrollmentORM.amount,
                ActivityORM.name,
                TurnoORM.description,
                EnrollmentORM.expires_at,
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
        )

    async def update_payment(self, enrollment_id: int, new_status: EnrollmentStatus, payment_id: str) -> None:
        await self._session.execute(
            update(EnrollmentORM)
            .where(EnrollmentORM.id == enrollment_id)
            .values(status=new_status, payment_id=payment_id)
        )

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
            detail="Ya tenés un lugar reservado en esta clase.",
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
