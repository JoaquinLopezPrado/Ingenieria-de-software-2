from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.payment import SingleDetails
from app.domain.single_enrollment import MySingleEnrollment, SingleEnrollment, SingleEnrollmentStatus
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.turno import Turno as TurnoORM
from app.repositories.capacity import ACTIVE_SINGLE_STATUSES
from app.repositories.clase_cancellation_repository import ClaseCancellationRepository

_ART = timezone(timedelta(hours=-3))
_DEPOSIT_RATIO = Decimal("0.30")
_DEPOSIT_DEADLINE_HOURS = 1

_ACTIVE = list(ACTIVE_SINGLE_STATUSES)


@dataclass
class DepositInfo:
    enrollment_id: int
    user_id: int
    status: SingleEnrollmentStatus
    deposit_amount: Decimal
    deposit_payment_id: str
    clase_start: datetime


class AbstractSingleEnrollmentRepository(ABC):

    @abstractmethod
    async def create_single(self, clase_ids: list[int], user_id: int, credit_id: int | None = None) -> SingleEnrollment:
        raise NotImplementedError

    @abstractmethod
    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        raise NotImplementedError

    @abstractmethod
    async def get_single_details(self, enrollment_id: int) -> SingleDetails:
        raise NotImplementedError

    @abstractmethod
    async def update_payment(self, enrollment_id: int, new_status: SingleEnrollmentStatus, payment_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def confirm_deposit(self, enrollment_id: int, deposit_payment_id: str, deposit_amount: Decimal) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def confirm_balance(self, enrollment_id: int, payment_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def cancel_deposit_with_refund(self, enrollment_id: int, user_id: int, refund_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def cancel_deposit_no_refund(self, enrollment_id: int, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_deposit_info(self, enrollment_id: int, user_id: int) -> "DepositInfo | None":
        raise NotImplementedError

    @abstractmethod
    async def cancel_expired(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def cancel_pending(self, enrollment_id: int, user_id: int) -> bool:
        raise NotImplementedError


class SingleEnrollmentRepository(AbstractSingleEnrollmentRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    # ------------------------------------------------------------------ #
    # Creación                                                            #
    # ------------------------------------------------------------------ #

    async def create_single(self, clase_ids: list[int], user_id: int, credit_id: int | None = None) -> SingleEnrollment:
        clases: list[ClaseORM] = []
        turno: TurnoORM | None = None
        for clase_id in sorted(clase_ids):
            clase = await self._lock_clase(clase_id)
            await self._check_capacity(clase)
            if turno is None:
                turno = await self._get_turno(clase.turno_id)
            await self._check_schedule_conflict(user_id, clase.date, turno.start_time, turno.end_time)
            await self._check_duplicate(clase_id, user_id)
            clases.append(clase)

        amount = Decimal(turno.class_price) * len(clases)

        credit_repo = ClaseCancellationRepository(self._session)
        credit = None
        if credit_id is not None:
            credit = await credit_repo.get_credit_by_id(credit_id, user_id)
            if credit is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El crédito no es válido o ya fue utilizado.",
                )
            # Un crédito = una clase: cubre una clase completa sin importar el precio
            # de origen ni la actividad. Se canjea en cualquier turno.
            amount = max(Decimal("0.00"), amount - Decimal(turno.class_price))

        if amount == Decimal("0.00"):
            enrollment_orm = SingleEnrollmentORM(
                turno_id=turno.id,
                user_id=user_id,
                amount=Decimal("0.00"),
                status=SingleEnrollmentStatus.CONFIRMED,
                expires_at=None,
            )
        else:
            enrollment_orm = SingleEnrollmentORM(
                turno_id=turno.id,
                user_id=user_id,
                amount=amount,
                status=SingleEnrollmentStatus.PENDING,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes),
            )
        self._session.add(enrollment_orm)
        await self._session.flush()

        for clase in clases:
            self._session.add(SingleSlotORM(enrollment_id=enrollment_orm.id, clase_id=clase.id))
        await self._session.flush()

        if credit is not None:
            await credit_repo.mark_credit_used(credit.id, clases[0].id)

        return self._to_domain(enrollment_orm)

    # ------------------------------------------------------------------ #
    # Consultas                                                           #
    # ------------------------------------------------------------------ #

    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        result = await self._session.execute(
            select(SingleEnrollmentORM)
            .options(
                selectinload(SingleEnrollmentORM.slots).selectinload(SingleSlotORM.clase),
                selectinload(SingleEnrollmentORM.turno).selectinload(TurnoORM.activity),
            )
            .where(
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status.in_(_ACTIVE),
            )
            .order_by(SingleEnrollmentORM.created_at.desc())
        )
        enrollments: list[MySingleEnrollment] = []
        for e in result.scalars():
            for slot in e.slots:
                clase = slot.clase
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
                    deposit_amount=e.deposit_amount,
                    deposit_payment_id=e.deposit_payment_id,
                ))
        return enrollments

    async def get_single_details(self, enrollment_id: int) -> SingleDetails:
        num_classes_subq = (
            select(func.count(SingleSlotORM.id))
            .where(SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .correlate(SingleEnrollmentORM)
            .scalar_subquery()
        )
        result = await self._session.execute(
            select(
                SingleEnrollmentORM.id,
                SingleEnrollmentORM.user_id,
                SingleEnrollmentORM.status,
                SingleEnrollmentORM.amount,
                ActivityORM.name,
                TurnoORM.description,
                SingleEnrollmentORM.expires_at,
                TurnoORM.class_price,
                num_classes_subq.label("num_classes"),
                TurnoORM.activity_id,
                TurnoORM.start_time,
            )
            .join(TurnoORM, TurnoORM.id == SingleEnrollmentORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(SingleEnrollmentORM.id == enrollment_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada.")

        dates_result = await self._session.execute(
            select(ClaseORM.date)
            .join(SingleSlotORM, SingleSlotORM.clase_id == ClaseORM.id)
            .where(SingleSlotORM.enrollment_id == enrollment_id)
            .order_by(ClaseORM.date)
        )
        clase_dates = [r[0] for r in dates_result]
        clase_start = (
            datetime.combine(clase_dates[0], row[10]).replace(tzinfo=_ART) if clase_dates else None
        )

        return SingleDetails(
            enrollment_id=row[0],
            user_id=row[1],
            status=row[2],
            amount=row[3],
            activity_name=row[4],
            turno_description=row[5],
            expires_at=row[6],
            class_price_snapshot=row[7],
            num_classes_snapshot=row[8] or 1,
            activity_id=row[9],
            clase_dates=clase_dates,
            clase_start=clase_start,
        )

    # ------------------------------------------------------------------ #
    # Transiciones de pago                                                #
    # ------------------------------------------------------------------ #

    async def update_payment(self, enrollment_id: int, new_status: SingleEnrollmentStatus, payment_id: str) -> bool:
        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.PENDING,
            )
            .values(status=new_status, payment_id=payment_id)
        )
        return result.rowcount > 0

    async def confirm_deposit(self, enrollment_id: int, deposit_payment_id: str, deposit_amount: Decimal) -> bool:
        slot_result = await self._session.execute(
            select(ClaseORM.date, TurnoORM.start_time)
            .join(SingleSlotORM, SingleSlotORM.clase_id == ClaseORM.id)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .where(SingleSlotORM.enrollment_id == enrollment_id)
            .order_by(ClaseORM.date, TurnoORM.start_time)
            .limit(1)
        )
        row = slot_result.first()
        if row is None:
            return False
        clase_start = datetime.combine(row[0], row[1]).replace(tzinfo=_ART)
        deposit_expires_at = clase_start - timedelta(hours=_DEPOSIT_DEADLINE_HOURS)

        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.PENDING,
            )
            .values(
                status=SingleEnrollmentStatus.DEPOSIT_PAID,
                deposit_payment_id=deposit_payment_id,
                deposit_amount=deposit_amount,
                expires_at=deposit_expires_at,
            )
        )
        return result.rowcount > 0

    async def confirm_balance(self, enrollment_id: int, payment_id: str) -> bool:
        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.DEPOSIT_PAID,
            )
            .values(status=SingleEnrollmentStatus.CONFIRMED, payment_id=payment_id)
        )
        return result.rowcount > 0

    async def cancel_deposit_with_refund(self, enrollment_id: int, user_id: int, refund_id: str) -> bool:
        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.DEPOSIT_PAID,
            )
            .values(status=SingleEnrollmentStatus.REFUNDED, refund_id=refund_id)
        )
        return result.rowcount > 0

    async def cancel_deposit_no_refund(self, enrollment_id: int, user_id: int) -> bool:
        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.DEPOSIT_PAID,
            )
            .values(status=SingleEnrollmentStatus.CANCELLED)
        )
        return result.rowcount > 0

    async def get_deposit_info(self, enrollment_id: int, user_id: int) -> "DepositInfo | None":
        result = await self._session.execute(
            select(
                SingleEnrollmentORM.id,
                SingleEnrollmentORM.user_id,
                SingleEnrollmentORM.status,
                SingleEnrollmentORM.deposit_amount,
                SingleEnrollmentORM.deposit_payment_id,
                ClaseORM.date,
                TurnoORM.start_time,
            )
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .join(ClaseORM, ClaseORM.id == SingleSlotORM.clase_id)
            .join(TurnoORM, TurnoORM.id == SingleEnrollmentORM.turno_id)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.DEPOSIT_PAID,
            )
            .order_by(ClaseORM.date, TurnoORM.start_time)
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        clase_start = datetime.combine(row[5], row[6]).replace(tzinfo=_ART)
        return DepositInfo(
            enrollment_id=row[0],
            user_id=row[1],
            status=row[2],
            deposit_amount=row[3],
            deposit_payment_id=row[4],
            clase_start=clase_start,
        )

    async def cancel_expired(self) -> int:
        now = datetime.now(timezone.utc)
        pending = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.status == SingleEnrollmentStatus.PENDING,
                SingleEnrollmentORM.expires_at.isnot(None),
                SingleEnrollmentORM.expires_at <= now,
            )
            .values(status=SingleEnrollmentStatus.CANCELLED)
        )
        deposit = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.status == SingleEnrollmentStatus.DEPOSIT_PAID,
                SingleEnrollmentORM.expires_at.isnot(None),
                SingleEnrollmentORM.expires_at <= now,
            )
            .values(status=SingleEnrollmentStatus.DEPOSIT_FORFEITED)
        )
        return pending.rowcount + deposit.rowcount

    async def cancel_pending(self, enrollment_id: int, user_id: int) -> bool:
        result = await self._session.execute(
            update(SingleEnrollmentORM)
            .where(
                SingleEnrollmentORM.id == enrollment_id,
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status == SingleEnrollmentStatus.PENDING,
            )
            .values(status=SingleEnrollmentStatus.CANCELLED)
        )
        return result.rowcount > 0

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

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

    async def _get_turno(self, turno_id: int) -> TurnoORM:
        result = await self._session.execute(select(TurnoORM).where(TurnoORM.id == turno_id))
        return result.scalar_one()

    async def _check_capacity(self, clase: ClaseORM) -> None:
        from app.repositories.capacity import occupied_subq
        occupied = (await self._session.execute(
            select(occupied_subq(clase.turno_id, clase.id, clase.date))
        )).scalar_one()
        if occupied >= clase.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay lugares disponibles en esta clase.",
            )

    async def _check_schedule_conflict(self, user_id: int, clase_date: date, start_time: time, end_time: time) -> None:
        result = await self._session.execute(
            select(SingleEnrollmentORM)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .join(ClaseORM, ClaseORM.id == SingleSlotORM.clase_id)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .where(
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status.in_(_ACTIVE),
                ClaseORM.date == clase_date,
                TurnoORM.start_time < end_time,
                TurnoORM.end_time > start_time,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return
        if self._is_stale_pending(existing):
            existing.status = SingleEnrollmentStatus.CANCELLED
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés otra clase suelta en ese día y horario.",
        )

    async def _check_duplicate(self, clase_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(SingleEnrollmentORM)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .where(
                SingleSlotORM.clase_id == clase_id,
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status.in_(_ACTIVE),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return
        if self._is_stale_pending(existing):
            existing.status = SingleEnrollmentStatus.CANCELLED
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés un lugar reservado en esta clase.",
        )

    @staticmethod
    def _is_stale_pending(orm: SingleEnrollmentORM) -> bool:
        return (
            orm.status == SingleEnrollmentStatus.PENDING
            and orm.expires_at is not None
            and orm.expires_at <= datetime.now(timezone.utc)
        )

    @staticmethod
    def _to_domain(orm: SingleEnrollmentORM) -> SingleEnrollment:
        return SingleEnrollment(
            id=orm.id,
            turno_id=orm.turno_id,
            user_id=orm.user_id,
            amount=orm.amount,
            status=orm.status,
            expires_at=orm.expires_at,
            payment_id=orm.payment_id,
            created_at=orm.created_at,
            deposit_amount=orm.deposit_amount,
            deposit_payment_id=orm.deposit_payment_id,
            refund_id=orm.refund_id,
        )
