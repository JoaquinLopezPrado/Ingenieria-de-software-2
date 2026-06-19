import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.subscription import MySubscription, SubscriptionCharge
from app.repositories.subscription_repository import AbstractSubscriptionRepository

_DEPOSIT_RATIO = Decimal("0.30")


def _end_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


class SubscriptionService:

    def __init__(self, subscription_repo: AbstractSubscriptionRepository):
        self._repo = subscription_repo

    async def create(self, turno_id: int, user_id: int) -> SubscriptionCharge:
        turno = await self._repo.lock_active_turno(turno_id)
        await self._repo.check_duplicate(turno_id, user_id)

        future_clases = await self._repo.get_future_clases(turno_id)
        if not future_clases:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El turno no tiene clases futuras disponibles.",
            )

        # Elige el primer período (mes) con cupo disponible. Capacidad por período:
        # un abonado saliente ocupa su período pagado y libera el siguiente.
        period_month, period_year, period_clases = await self._first_available_period(turno, future_clases)
        if period_clases is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay lugares disponibles en este turno.",
            )

        clase_ids = [c.id for c in period_clases]
        confirmed_covered, deposit_covered = await self._repo.get_single_covered_clase_ids(user_id, clase_ids)

        class_price = Decimal(turno.class_price)
        amount, original_amount, discount_deposit_single = self._compute_amounts(
            class_price=class_price,
            period_clase_ids=clase_ids,
            confirmed_covered=confirmed_covered,
            deposit_covered=deposit_covered,
        )

        # start_date gate: si el período elegido es futuro, la suscripción arranca el 1°
        # de ese mes para no ocupar (ni cobrar) meses ya llenos.
        today = date.today()
        period_start = date(period_year, period_month, 1)
        start_date = today if (period_month, period_year) == (today.month, today.year) else period_start

        due_date = _end_of_month(period_year, period_month)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes)

        _, charge = await self._repo.create(
            turno_id=turno_id,
            user_id=user_id,
            start_date=start_date,
            period_month=period_month,
            period_year=period_year,
            amount=amount,
            original_amount=original_amount,
            due_date=due_date,
            expires_at=expires_at,
        )
        charge.discount_deposit_single = discount_deposit_single
        return charge

    async def _first_available_period(self, turno, future_clases):
        """Primer (mes, año) con cupo, recorriendo los períodos de las clases futuras.

        Devuelve (month, year, clases_del_período) o (_, _, None) si están todos llenos.
        """
        for month, year, clases in self._periods(future_clases):
            occupied = await self._repo.count_occupying_on(turno.id, clases[0].date)
            if occupied < turno.capacity:
                return month, year, clases
        return 0, 0, None

    @staticmethod
    def _periods(future_clases):
        """Agrupa las clases futuras por (mes, año) preservando el orden cronológico."""
        groups: list[tuple[int, int, list]] = []
        index: dict[tuple[int, int], list] = {}
        for c in future_clases:
            key = (c.date.month, c.date.year)
            if key not in index:
                index[key] = []
                groups.append((key[0], key[1], index[key]))
            index[key].append(c)
        return groups

    async def get_subscriptions_by_user(self, user_id: int) -> list[MySubscription]:
        # Generación lazy: asegura el cargo del mes vigente para las suscripciones
        # activas del usuario antes de listarlas (así aparece el botón "pagar mes").
        await self._ensure_current_charges(user_id=user_id)
        return await self._repo.get_subscriptions_by_user(user_id=user_id)

    async def cancel(self, subscription_id: int, user_id: int) -> None:
        await self._repo.cancel_pending(subscription_id=subscription_id, user_id=user_id)

    async def unsubscribe(self, subscription_id: int, user_id: int) -> date:
        """Baja voluntaria de un abonado activo: efectiva al fin del período pagado."""
        ends_on = await self._repo.schedule_cancellation(subscription_id=subscription_id, user_id=user_id)
        if ends_on is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tenés una suscripción activa para dar de baja.",
            )
        return ends_on

    async def effectivize_cancellations(self) -> int:
        return await self._repo.effectivize_scheduled_cancellations()

    async def get_paid_charges(self, user_id: int) -> list[dict]:
        return await self._repo.get_paid_charges_by_user(user_id=user_id)

    async def get_overdue(self, min_unpaid: int = 2) -> list[dict]:
        return await self._repo.get_overdue(min_unpaid=min_unpaid)

    async def admin_cancel(self, subscription_ids: list[int]) -> int:
        return await self._repo.admin_cancel(subscription_ids=subscription_ids)

    async def generate_charges_for_period(self, period_month: int, period_year: int) -> int:
        """Crea los cargos faltantes del período para TODAS las suscripciones activas (cron)."""
        return await self._ensure_current_charges(period_month=period_month, period_year=period_year)

    async def _ensure_current_charges(
        self, user_id: int | None = None, period_month: int | None = None, period_year: int | None = None
    ) -> int:
        today = date.today()
        month = period_month or today.month
        year = period_year or today.year
        pending = await self._repo.get_active_missing_charge(month, year, user_id=user_id)
        created = 0
        for subscription_id, turno_id, class_price in pending:
            num_classes = await self._repo.count_clases_in_period(turno_id, month, year)
            if num_classes == 0:
                continue
            amount = Decimal(class_price) * num_classes
            await self._repo.add_charge(
                subscription_id=subscription_id,
                period_month=month,
                period_year=year,
                amount=amount,
                original_amount=amount,
                due_date=_end_of_month(year, month),
            )
            created += 1
        return created

    # ------------------------------------------------------------------ #
    # Lógica de precio (pura, testeable)                                   #
    # ------------------------------------------------------------------ #

    @classmethod
    def _compute_amounts(
        cls,
        class_price: Decimal,
        period_clase_ids: list[int],
        confirmed_covered: set[int],
        deposit_covered: set[int],
    ) -> tuple[Decimal, Decimal, Decimal]:
        """Calcula (amount, original_amount, discount_deposit_single).

        Las clases que el cliente ya pagó como sueltas (confirmadas) no se cobran.
        Las que tienen seña pagan solo el saldo (70%); el 30% ya abonado se descuenta.
        El resto paga precio completo.
        """
        original_amount = class_price * len(period_clase_ids)
        deposit_per_class = (class_price * _DEPOSIT_RATIO).quantize(Decimal("0.01"))
        balance_per_class = class_price - deposit_per_class

        not_covered = [cid for cid in period_clase_ids if cid not in confirmed_covered and cid not in deposit_covered]
        deposit_in_period = [cid for cid in period_clase_ids if cid in deposit_covered]

        amount = class_price * len(not_covered) + balance_per_class * len(deposit_in_period)
        discount_deposit_single = deposit_per_class * len(deposit_in_period)
        return amount, original_amount, discount_deposit_single
