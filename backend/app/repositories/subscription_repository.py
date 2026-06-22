import calendar
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.payment import SubscriptionChargeDetails
from app.domain.subscription import (
    ChargeStatus,
    MySubscription,
    OCCUPYING_SUBSCRIPTION_STATUSES,
    Subscription,
    SubscriptionCharge,
    SubscriptionStatus,
)
from app.domain.single_enrollment import SingleEnrollmentStatus
from app.models.activity import Activity as ActivityORM
from app.models.clase import Clase as ClaseORM
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM, SubscriptionCharge as SubscriptionChargeORM
from app.models.subscription_class_discount import SubscriptionClassDiscount as DiscountORM
from app.models.turno import Turno as TurnoORM

_ACTIVE_SINGLE_STATUSES = [
    SingleEnrollmentStatus.PENDING,
    SingleEnrollmentStatus.CONFIRMED,
    SingleEnrollmentStatus.DEPOSIT_PAID,
]


class AbstractSubscriptionRepository(ABC):

    @abstractmethod
    async def lock_active_turno(self, turno_id: int) -> TurnoORM:
        raise NotImplementedError

    @abstractmethod
    async def count_occupying_on(self, turno_id: int, ref_date: date) -> int:
        raise NotImplementedError

    @abstractmethod
    async def check_duplicate(self, turno_id: int, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_future_clases(self, turno_id: int) -> list[ClaseORM]:
        raise NotImplementedError

    @abstractmethod
    async def get_single_covered_clase_ids(self, user_id: int, clase_ids: list[int]) -> tuple[set[int], set[int]]:
        raise NotImplementedError

    @abstractmethod
    async def get_full_clase_ids(self, clase_ids: list[int], capacity: int) -> set[int]:
        raise NotImplementedError

    @abstractmethod
    async def count_combined_on(self, turno_id: int, clase_id: int, clase_date: date) -> int:
        raise NotImplementedError

    @abstractmethod
    async def create(
        self,
        turno_id: int,
        user_id: int,
        start_date: date,
        period_month: int,
        period_year: int,
        amount: Decimal,
        original_amount: Decimal,
        due_date: date,
        expires_at: datetime,
    ) -> tuple[Subscription, SubscriptionCharge]:
        raise NotImplementedError

    @abstractmethod
    async def get_subscriptions_by_user(self, user_id: int) -> list[MySubscription]:
        raise NotImplementedError

    @abstractmethod
    async def get_paid_charges_by_user(self, user_id: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def get_charge_details(self, charge_id: int) -> SubscriptionChargeDetails:
        raise NotImplementedError

    @abstractmethod
    async def mark_charge_paid(self, charge_id: int, payment_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def cancel_expired(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def cancel_pending(self, subscription_id: int, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def schedule_cancellation(self, subscription_id: int, user_id: int) -> "date | None":
        raise NotImplementedError

    @abstractmethod
    async def effectivize_scheduled_cancellations(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_active_missing_charge(self, period_month: int, period_year: int, user_id: int | None = None) -> list[tuple[int, int, Decimal]]:
        raise NotImplementedError

    @abstractmethod
    async def count_clases_in_period(self, turno_id: int, period_month: int, period_year: int) -> int:
        raise NotImplementedError

    @abstractmethod
    async def add_charge(self, subscription_id: int, period_month: int, period_year: int, amount: Decimal, original_amount: Decimal, due_date: date) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_overdue(self, min_unpaid: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def admin_cancel(self, subscription_ids: list[int]) -> int:
        raise NotImplementedError


class SubscriptionRepository(AbstractSubscriptionRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def lock_active_turno(self, turno_id: int) -> TurnoORM:
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

    async def count_occupying_on(self, turno_id: int, ref_date: date) -> int:
        """Cuántos abonados ocupan el turno en ``ref_date`` (dentro de [start_date, ends_on])."""
        result = await self._session.execute(
            select(func.count(SubscriptionORM.id)).where(
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.start_date <= ref_date,
                or_(SubscriptionORM.ends_on.is_(None), ref_date <= SubscriptionORM.ends_on),
            )
        )
        return result.scalar_one()

    async def check_duplicate(self, turno_id: int, user_id: int) -> None:
        result = await self._session.execute(
            select(SubscriptionORM)
            .options(selectinload(SubscriptionORM.charges))
            .where(
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.ends_on.is_(None),  # una baja programada no bloquea re-suscribirse
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return

        # Una suscripción PENDING cuyo primer cargo venció se considera abandonada.
        if existing.status == SubscriptionStatus.PENDING and self._first_charge_expired(existing):
            existing.status = SubscriptionStatus.CANCELLED
            return

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya tenés una suscripción activa para este turno.",
        )

    async def get_future_clases(self, turno_id: int) -> list[ClaseORM]:
        today = date.today()
        result = await self._session.execute(
            select(ClaseORM)
            .where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                ClaseORM.date >= today,
            )
            .order_by(ClaseORM.date)
        )
        return list(result.scalars().all())

    async def get_full_clase_ids(self, clase_ids: list[int], capacity: int) -> set[int]:
        """Clases de la lista que ya están a plena capacidad (usuarios únicos, sin doble conteo)."""
        if not clase_ids:
            return set()
        from app.repositories.capacity import occupied_subq
        result = await self._session.execute(
            select(ClaseORM.id).where(
                ClaseORM.id.in_(clase_ids),
                occupied_subq(ClaseORM.turno_id, ClaseORM.id, ClaseORM.date) >= capacity,
            )
        )
        return set(result.scalars().all())

    async def count_combined_on(self, turno_id: int, clase_id: int, clase_date: date) -> int:
        """Ocupación combinada de una clase (usuarios únicos: abonados UNION sueltos)."""
        from app.repositories.capacity import occupied_subq
        result = await self._session.execute(
            select(occupied_subq(turno_id, clase_id, clase_date))
        )
        return result.scalar_one() or 0

    async def get_single_covered_clase_ids(self, user_id: int, clase_ids: list[int]) -> tuple[set[int], set[int]]:
        """Clases que el usuario ya tiene reservadas como sueltas, separadas por estado.

        Retorna (confirmadas, con_seña) para descontar correctamente del cargo:
        las confirmadas están 100% pagas; las con seña solo el 30%.
        """
        if not clase_ids:
            return set(), set()
        result = await self._session.execute(
            select(SingleSlotORM.clase_id, SingleEnrollmentORM.status)
            .join(SingleEnrollmentORM, SingleEnrollmentORM.id == SingleSlotORM.enrollment_id)
            .where(
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status.in_(_ACTIVE_SINGLE_STATUSES),
                SingleSlotORM.clase_id.in_(clase_ids),
            )
        )
        confirmed: set[int] = set()
        deposit_paid: set[int] = set()
        for clase_id, stat in result.all():
            if stat == SingleEnrollmentStatus.DEPOSIT_PAID:
                deposit_paid.add(clase_id)
            else:
                confirmed.add(clase_id)
        return confirmed, deposit_paid

    async def create(
        self,
        turno_id: int,
        user_id: int,
        start_date: date,
        period_month: int,
        period_year: int,
        amount: Decimal,
        original_amount: Decimal,
        due_date: date,
        expires_at: datetime,
    ) -> tuple[Subscription, SubscriptionCharge]:
        sub_orm = SubscriptionORM(
            turno_id=turno_id,
            user_id=user_id,
            status=SubscriptionStatus.PENDING,
            start_date=start_date,
        )
        self._session.add(sub_orm)
        await self._session.flush()

        charge_orm = SubscriptionChargeORM(
            subscription_id=sub_orm.id,
            period_month=period_month,
            period_year=period_year,
            amount=amount,
            original_amount=original_amount,
            status=ChargeStatus.PENDING,
            due_date=due_date,
            expires_at=expires_at,
        )
        self._session.add(charge_orm)
        await self._session.flush()

        return self._sub_to_domain(sub_orm), self._charge_to_domain(charge_orm)

    async def get_subscriptions_by_user(self, user_id: int) -> list[MySubscription]:
        result = await self._session.execute(
            select(SubscriptionORM)
            .options(
                selectinload(SubscriptionORM.turno).selectinload(TurnoORM.activity),
                selectinload(SubscriptionORM.turno).selectinload(TurnoORM.days),
                selectinload(SubscriptionORM.charges),
            )
            .where(
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
            )
            .order_by(SubscriptionORM.created_at.desc())
        )
        items: list[MySubscription] = []
        for sub in result.scalars():
            pending = next(
                (c for c in sub.charges if c.status in (ChargeStatus.PENDING, ChargeStatus.OVERDUE)),
                None,
            )
            items.append(MySubscription(
                subscription_id=sub.id,
                status=sub.status,
                start_date=sub.start_date,
                ends_on=sub.ends_on,
                turno_id=sub.turno.id,
                turno_description=sub.turno.description,
                start_time=sub.turno.start_time,
                end_time=sub.turno.end_time,
                instructor=sub.turno.instructor,
                activity_name=sub.turno.activity.name,
                days=[d.dia for d in sub.turno.days],
                pending_charge=self._charge_to_domain(pending) if pending else None,
            ))
        return items

    async def get_paid_charges_by_user(self, user_id: int) -> list[dict]:
        result = await self._session.execute(
            select(
                SubscriptionChargeORM.id,
                SubscriptionChargeORM.period_month,
                SubscriptionChargeORM.period_year,
                SubscriptionChargeORM.amount,
                SubscriptionChargeORM.paid_at,
                ActivityORM.name,
                TurnoORM.description,
                TurnoORM.instructor,
            )
            .join(SubscriptionORM, SubscriptionORM.id == SubscriptionChargeORM.subscription_id)
            .join(TurnoORM, TurnoORM.id == SubscriptionORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(
                SubscriptionORM.user_id == user_id,
                SubscriptionChargeORM.status == ChargeStatus.PAID,
            )
            .order_by(SubscriptionChargeORM.paid_at.desc())
        )
        return [
            {
                "charge_id": row[0],
                "period_month": row[1],
                "period_year": row[2],
                "amount": row[3],
                "paid_at": row[4],
                "activity_name": row[5],
                "turno_description": row[6],
                "instructor": row[7],
            }
            for row in result.all()
        ]

    async def get_charge_details(self, charge_id: int) -> SubscriptionChargeDetails:
        result = await self._session.execute(
            select(
                SubscriptionChargeORM.id,
                SubscriptionChargeORM.subscription_id,
                SubscriptionORM.user_id,
                SubscriptionChargeORM.status,
                SubscriptionChargeORM.amount,
                ActivityORM.name,
                TurnoORM.description,
                TurnoORM.class_price,
                TurnoORM.activity_id,
                SubscriptionChargeORM.period_month,
                SubscriptionChargeORM.period_year,
                SubscriptionChargeORM.expires_at,
                SubscriptionChargeORM.original_amount,
            )
            .join(SubscriptionORM, SubscriptionORM.id == SubscriptionChargeORM.subscription_id)
            .join(TurnoORM, TurnoORM.id == SubscriptionORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(SubscriptionChargeORM.id == charge_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cargo no encontrado.")

        class_price = row[7]
        original_amount = row[12] if row[12] is not None else row[4]
        num_classes = int(original_amount / class_price) if class_price else 0
        return SubscriptionChargeDetails(
            charge_id=row[0],
            subscription_id=row[1],
            user_id=row[2],
            status=row[3],
            amount=row[4],
            activity_name=row[5],
            turno_description=row[6],
            class_price_snapshot=class_price,
            num_classes_snapshot=num_classes or 1,
            activity_id=row[8],
            period_month=row[9],
            period_year=row[10],
            expires_at=row[11],
            original_amount=original_amount,
        )

    async def mark_charge_paid(self, charge_id: int, payment_id: str) -> bool:
        result = await self._session.execute(
            update(SubscriptionChargeORM)
            .where(
                SubscriptionChargeORM.id == charge_id,
                SubscriptionChargeORM.status.in_([ChargeStatus.PENDING, ChargeStatus.OVERDUE]),
            )
            .values(status=ChargeStatus.PAID, payment_id=payment_id, paid_at=datetime.now(timezone.utc))
        )
        if result.rowcount == 0:
            return False
        # El primer pago activa la suscripción.
        charge = await self._session.get(SubscriptionChargeORM, charge_id)
        await self._session.execute(
            update(SubscriptionORM)
            .where(
                SubscriptionORM.id == charge.subscription_id,
                SubscriptionORM.status == SubscriptionStatus.PENDING,
            )
            .values(status=SubscriptionStatus.ACTIVE)
        )
        return True

    async def cancel_expired(self) -> int:
        now = datetime.now(timezone.utc)
        # Cargos pendientes vencidos.
        expired_charges = (await self._session.execute(
            select(SubscriptionChargeORM.subscription_id)
            .where(
                SubscriptionChargeORM.status == ChargeStatus.PENDING,
                SubscriptionChargeORM.expires_at.isnot(None),
                SubscriptionChargeORM.expires_at <= now,
            )
        )).scalars().all()
        if not expired_charges:
            return 0
        # Solo se auto-cancela una suscripción que nunca se confirmó (sigue PENDING).
        result = await self._session.execute(
            update(SubscriptionORM)
            .where(
                SubscriptionORM.id.in_(expired_charges),
                SubscriptionORM.status == SubscriptionStatus.PENDING,
            )
            .values(status=SubscriptionStatus.CANCELLED, cancelled_at=now)
        )
        await self._session.execute(
            update(SubscriptionChargeORM)
            .where(
                SubscriptionChargeORM.subscription_id.in_(expired_charges),
                SubscriptionChargeORM.status == ChargeStatus.PENDING,
                SubscriptionChargeORM.expires_at <= now,
            )
            .values(status=ChargeStatus.WAIVED)
        )
        return result.rowcount

    async def cancel_pending(self, subscription_id: int, user_id: int) -> bool:
        result = await self._session.execute(
            update(SubscriptionORM)
            .where(
                SubscriptionORM.id == subscription_id,
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status == SubscriptionStatus.PENDING,
            )
            .values(status=SubscriptionStatus.CANCELLED, cancelled_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    async def schedule_cancellation(self, subscription_id: int, user_id: int) -> "date | None":
        """Baja voluntaria de un abonado activo: sigue ocupando el lugar hasta el fin del
        período pagado (ends_on) y luego un job la efectiviza. Anula cargos pendientes."""
        sub = (await self._session.execute(
            select(SubscriptionORM).where(
                SubscriptionORM.id == subscription_id,
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status == SubscriptionStatus.ACTIVE,
            )
        )).scalar_one_or_none()
        if sub is None:
            return None

        last_paid = (await self._session.execute(
            select(SubscriptionChargeORM.period_month, SubscriptionChargeORM.period_year)
            .where(
                SubscriptionChargeORM.subscription_id == subscription_id,
                SubscriptionChargeORM.status == ChargeStatus.PAID,
            )
            .order_by(SubscriptionChargeORM.period_year.desc(), SubscriptionChargeORM.period_month.desc())
            .limit(1)
        )).first()

        if last_paid is not None:
            month, year = last_paid[0], last_paid[1]
            ends_on = date(year, month, calendar.monthrange(year, month)[1])
        else:
            ends_on = date.today()

        sub.ends_on = ends_on
        # Los cargos pendientes/vencidos ya no se cobran.
        await self._session.execute(
            update(SubscriptionChargeORM)
            .where(
                SubscriptionChargeORM.subscription_id == subscription_id,
                SubscriptionChargeORM.status.in_([ChargeStatus.PENDING, ChargeStatus.OVERDUE]),
            )
            .values(status=ChargeStatus.WAIVED)
        )
        await self._session.flush()
        return ends_on

    async def effectivize_scheduled_cancellations(self) -> int:
        today = date.today()
        result = await self._session.execute(
            update(SubscriptionORM)
            .where(
                SubscriptionORM.status == SubscriptionStatus.ACTIVE,
                SubscriptionORM.ends_on.isnot(None),
                SubscriptionORM.ends_on <= today,
            )
            .values(status=SubscriptionStatus.CANCELLED, cancelled_at=datetime.now(timezone.utc))
        )
        return result.rowcount

    # ------------------------------------------------------------------ #
    # Generación de cargos mensuales (renovación)                          #
    # ------------------------------------------------------------------ #

    async def get_active_missing_charge(
        self, period_month: int, period_year: int, user_id: int | None = None
    ) -> list[tuple[int, int, Decimal]]:
        """Suscripciones ACTIVE sin cargo para el período dado → (sub_id, turno_id, class_price)."""
        period_end = date(period_year, period_month, calendar.monthrange(period_year, period_month)[1])
        has_charge = (
            select(SubscriptionChargeORM.id)
            .where(
                SubscriptionChargeORM.subscription_id == SubscriptionORM.id,
                SubscriptionChargeORM.period_month == period_month,
                SubscriptionChargeORM.period_year == period_year,
            )
            .exists()
        )
        query = (
            select(SubscriptionORM.id, TurnoORM.id, TurnoORM.class_price)
            .join(TurnoORM, TurnoORM.id == SubscriptionORM.turno_id)
            .where(
                SubscriptionORM.status == SubscriptionStatus.ACTIVE,
                SubscriptionORM.ends_on.is_(None),  # baja programada → no generar más cargos
                SubscriptionORM.start_date <= period_end,  # no cobrar períodos previos al alta
                ~has_charge,
            )
        )
        if user_id is not None:
            query = query.where(SubscriptionORM.user_id == user_id)
        result = await self._session.execute(query)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def count_clases_in_period(self, turno_id: int, period_month: int, period_year: int) -> int:
        result = await self._session.execute(
            select(func.count(ClaseORM.id)).where(
                ClaseORM.turno_id == turno_id,
                ClaseORM.is_active == True,
                func.extract("month", ClaseORM.date) == period_month,
                func.extract("year", ClaseORM.date) == period_year,
            )
        )
        return result.scalar_one()

    async def add_charge(
        self, subscription_id: int, period_month: int, period_year: int, amount: Decimal, original_amount: Decimal, due_date: date
    ) -> None:
        # Consumir descuentos pendientes por clases canceladas
        discounts_result = await self._session.execute(
            select(DiscountORM).where(
                DiscountORM.subscription_id == subscription_id,
                DiscountORM.applied_to_charge_id.is_(None),
            )
        )
        pending_discounts = list(discounts_result.scalars())
        total_discount = sum(Decimal(d.amount) for d in pending_discounts)

        final_amount = max(Decimal("0.00"), amount - total_discount)

        charge = SubscriptionChargeORM(
            subscription_id=subscription_id,
            period_month=period_month,
            period_year=period_year,
            amount=final_amount,
            original_amount=original_amount,
            status=ChargeStatus.PENDING,
            due_date=due_date,
        )
        self._session.add(charge)
        await self._session.flush()

        for d in pending_discounts:
            d.applied_to_charge_id = charge.id

    async def get_overdue(self, min_unpaid: int) -> list[dict]:
        """Suscripciones ACTIVE con >= min_unpaid cargos impagos (pending/overdue)."""
        unpaid_count = (
            select(func.count(SubscriptionChargeORM.id))
            .where(
                SubscriptionChargeORM.subscription_id == SubscriptionORM.id,
                SubscriptionChargeORM.status.in_([ChargeStatus.PENDING, ChargeStatus.OVERDUE]),
            )
            .correlate(SubscriptionORM)
            .scalar_subquery()
        )
        result = await self._session.execute(
            select(
                SubscriptionORM.id,
                SubscriptionORM.user_id,
                TurnoORM.description,
                ActivityORM.name,
                unpaid_count.label("unpaid"),
            )
            .join(TurnoORM, TurnoORM.id == SubscriptionORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(SubscriptionORM.status == SubscriptionStatus.ACTIVE, unpaid_count >= min_unpaid)
            .order_by(unpaid_count.desc())
        )
        return [
            {
                "subscription_id": row[0],
                "user_id": row[1],
                "turno_description": row[2],
                "activity_name": row[3],
                "unpaid_count": row[4],
            }
            for row in result.all()
        ]

    async def admin_cancel(self, subscription_ids: list[int]) -> int:
        if not subscription_ids:
            return 0
        result = await self._session.execute(
            update(SubscriptionORM)
            .where(
                SubscriptionORM.id.in_(subscription_ids),
                SubscriptionORM.status == SubscriptionStatus.ACTIVE,
            )
            .values(status=SubscriptionStatus.CANCELLED, cancelled_at=datetime.now(timezone.utc))
        )
        return result.rowcount

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _first_charge_expired(sub: SubscriptionORM) -> bool:
        now = datetime.now(timezone.utc)
        return any(
            c.status == ChargeStatus.PENDING and c.expires_at is not None and c.expires_at <= now
            for c in sub.charges
        )

    @staticmethod
    def _sub_to_domain(orm: SubscriptionORM) -> Subscription:
        return Subscription(
            id=orm.id,
            user_id=orm.user_id,
            turno_id=orm.turno_id,
            status=orm.status,
            start_date=orm.start_date,
            cancelled_at=orm.cancelled_at,
            created_at=orm.created_at,
            ends_on=orm.ends_on,
        )

    @staticmethod
    def _charge_to_domain(orm: SubscriptionChargeORM, discount_deposit_single: Decimal | None = None) -> SubscriptionCharge:
        return SubscriptionCharge(
            id=orm.id,
            subscription_id=orm.subscription_id,
            period_month=orm.period_month,
            period_year=orm.period_year,
            amount=orm.amount,
            status=orm.status,
            due_date=orm.due_date,
            paid_at=orm.paid_at,
            payment_id=orm.payment_id,
            original_amount=orm.original_amount,
            created_at=orm.created_at,
            expires_at=orm.expires_at,
            discount_deposit_single=discount_deposit_single,
        )
