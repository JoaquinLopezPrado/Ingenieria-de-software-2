import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.subscription import MySubscription, SubscriptionCharge
from app.repositories.schedule_conflict import conflict_message
from app.repositories.subscription_repository import AbstractSubscriptionRepository

_DEPOSIT_RATIO = Decimal("0.30")
_ART = timezone(timedelta(hours=-3))


def _end_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


@dataclass
class _EnrollmentPlan:
    amount: Decimal
    original_amount: Decimal
    discount_deposit_single: Decimal
    discount_full_classes: Decimal
    period_month: int
    period_year: int
    start_date: date
    due_date: date
    class_price: Decimal
    clases_con_cupo: list[tuple[int, date]]
    clases_sin_cupo: list[tuple[int, date]]
    clases_ya_abonadas: list[tuple[int, date]]


class SubscriptionService:

    def __init__(self, subscription_repo: AbstractSubscriptionRepository):
        self._repo = subscription_repo

    async def _plan_enrollment(
        self, turno_id: int, user_id: int,
        min_month: "int | None" = None, min_year: "int | None" = None,
    ) -> _EnrollmentPlan:
        """Valida y calcula los parámetros de una suscripción sin persistir nada."""
        turno = await self._repo.lock_active_turno(turno_id)
        await self._repo.check_duplicate(turno_id, user_id)

        future_clases = await self._repo.get_future_clases(turno_id)
        if not future_clases:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El turno no tiene clases futuras disponibles.",
            )

        all_future_ids = [c.id for c in future_clases]

        conflicts = await self._repo.find_schedule_conflicts(user_id, all_future_ids)
        if conflicts:
            last_conflict = max(slot.date for slot in conflicts.values())
            future_clases = [c for c in future_clases if c.date > last_conflict]
            if not future_clases:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=conflict_message(next(iter(conflicts.values()))),
                )
            all_future_ids = [c.id for c in future_clases]

        user_confirmed, user_deposit = await self._repo.get_single_covered_clase_ids(user_id, all_future_ids)
        user_single_ids = user_confirmed | user_deposit

        period_month, period_year, period_clases = await self._first_available_period(
            turno, future_clases, user_single_ids, min_month=min_month, min_year=min_year
        )
        if period_clases is None:
            detail = (
                f"No hay lugares disponibles en el turno para {min_month}/{min_year}."
                if min_month and min_year
                else "No hay lugares disponibles en este turno."
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        clase_ids = [c.id for c in period_clases]
        full_clase_ids = await self._repo.get_full_clase_ids(clase_ids, turno.capacity)
        user_single_in_period = set(clase_ids) & user_single_ids
        truly_full_clase_ids = full_clase_ids - user_single_in_period

        billable_clase_ids = [cid for cid in clase_ids if cid not in truly_full_clase_ids]
        confirmed_covered = user_confirmed & set(billable_clase_ids)
        deposit_covered = user_deposit & set(billable_clase_ids)

        class_price = Decimal(turno.class_price)
        original_amount = class_price * len(clase_ids)
        discount_full_classes = class_price * len(truly_full_clase_ids)
        amount, _, discount_deposit_single = self._compute_amounts(
            class_price=class_price,
            period_clase_ids=billable_clase_ids,
            confirmed_covered=confirmed_covered,
            deposit_covered=deposit_covered,
        )

        start_date = period_clases[0].date
        due_date = _end_of_month(period_year, period_month)

        clases_sin_cupo = [(c.id, c.date) for c in period_clases if c.id in truly_full_clase_ids]
        clases_ya_abonadas = [(c.id, c.date) for c in period_clases if c.id in confirmed_covered]
        clases_con_cupo = [
            (c.id, c.date)
            for c in period_clases
            if c.id not in truly_full_clase_ids and c.id not in confirmed_covered
        ]

        return _EnrollmentPlan(
            amount=amount,
            original_amount=original_amount,
            discount_deposit_single=discount_deposit_single,
            discount_full_classes=discount_full_classes,
            period_month=period_month,
            period_year=period_year,
            start_date=start_date,
            due_date=due_date,
            class_price=class_price,
            clases_con_cupo=clases_con_cupo,
            clases_sin_cupo=clases_sin_cupo,
            clases_ya_abonadas=clases_ya_abonadas,
        )

    async def preview_subscription(
        self, turno_id: int, user_id: int,
        min_month: "int | None" = None, min_year: "int | None" = None,
    ) -> _EnrollmentPlan:
        """Devuelve el plan de suscripción (monto, período) sin escribir en la base de datos."""
        return await self._plan_enrollment(turno_id, user_id, min_month=min_month, min_year=min_year)

    async def create(self, turno_id: int, user_id: int, expires_at_override: "datetime | None" = None,
                     min_month: "int | None" = None, min_year: "int | None" = None) -> SubscriptionCharge:
        plan = await self._plan_enrollment(turno_id, user_id, min_month=min_month, min_year=min_year)
        expires_at = expires_at_override or datetime.now(timezone.utc) + timedelta(minutes=settings.enrollment_ttl_minutes)

        _, charge = await self._repo.create(
            turno_id=turno_id,
            user_id=user_id,
            start_date=plan.start_date,
            period_month=plan.period_month,
            period_year=plan.period_year,
            amount=plan.amount,
            original_amount=plan.original_amount,
            due_date=plan.due_date,
            expires_at=expires_at,
        )
        charge.discount_deposit_single = plan.discount_deposit_single
        charge.discount_full_classes = plan.discount_full_classes
        return charge

    async def _first_available_period(
        self, turno, future_clases, user_single_ids: set[int],
        min_month: "int | None" = None, min_year: "int | None" = None,
    ):
        """Primer (mes, año) con al menos una clase con cupo combinado disponible.

        Si se especifica min_month/min_year, solo evalúa ese mes exacto y devuelve
        (0, 0, None) si está lleno o no tiene clases (no avanza al mes siguiente).
        Sin restricción, busca el primer mes disponible desde hoy en adelante.

        Devuelve TODAS las clases del mes (no solo desde la primera con cupo): las
        que estén llenas se descuentan más adelante en _plan_enrollment
        (discount_full_classes), sin importar si la clase llena es la primera del
        mes o una del medio.
        """
        target = (min_year, min_month) if min_month and min_year else None
        for month, year, clases in self._periods(future_clases):
            if target:
                if (year, month) < target:
                    continue
                if (year, month) > target:
                    return 0, 0, None
            for clase in clases:
                combined = await self._repo.count_combined_on(turno.id, clase.id, clase.date)
                adjustment = 1 if clase.id in user_single_ids else 0
                if combined - adjustment < turno.capacity:
                    return month, year, clases
            if target:
                return 0, 0, None
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

    async def cancel(self, subscription_id: int, user_id: int) -> "int | None":
        """Cancela suscripción PENDING. Retorna turno_id liberado o None si no existía."""
        return await self._repo.cancel_pending(subscription_id=subscription_id, user_id=user_id)

    async def unsubscribe(self, subscription_id: int, user_id: int) -> "tuple[date, int]":
        """Baja voluntaria de un abonado activo: efectiva al fin del período pagado.
        Retorna (ends_on, turno_id)."""
        result = await self._repo.schedule_cancellation(subscription_id=subscription_id, user_id=user_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tenés una suscripción activa para dar de baja.",
            )
        return result

    async def effectivize_cancellations(self) -> list[int]:
        return await self._repo.effectivize_scheduled_cancellations()

    async def get_paid_charges(self, user_id: int) -> list[dict]:
        return await self._repo.get_paid_charges_by_user(user_id=user_id)

    async def get_overdue(self, min_unpaid: int = 2) -> list[dict]:
        return await self._repo.get_overdue(min_unpaid=min_unpaid)

    async def admin_cancel(self, subscription_ids: list[int]) -> list[int]:
        """Cancela suscripciones ACTIVE. Retorna turno_ids liberados."""
        return await self._repo.admin_cancel(subscription_ids=subscription_ids)

    async def admin_unsubscribe(self, subscription_id: int) -> "tuple[date, int]":
        """Baja programada iniciada por admin, sin verificar propiedad del usuario.
        Retorna (ends_on, turno_id)."""
        result = await self._repo.admin_schedule_cancellation(subscription_id=subscription_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una suscripción activa con ese ID.",
            )
        return result

    async def get_pending_charges(self) -> list[dict]:
        return await self._repo.get_pending_charges_admin()

    async def generate_charges_for_period(self, period_month: int, period_year: int) -> int:
        """Crea los cargos faltantes del período para TODAS las suscripciones activas (cron)."""
        return await self._ensure_current_charges(period_month=period_month, period_year=period_year)

    async def generate_charges_and_notify(
        self, period_month: int, period_year: int, email_service: "EmailService", payment_service: "PaymentService"
    ) -> int:
        """Genera cargos del período y envía mail de recordatorio a cada afectado,
        con un link de pago de Mercado Pago propio de cada cargo.
        Retorna la cantidad de cargos nuevos creados."""
        from app.services.email_service import EmailService  # evitar import circular

        due_date = _end_of_month(period_year, period_month)
        pending = await self._repo.get_active_missing_charge_full(period_month, period_year)
        created = 0
        notifications: list[tuple] = []
        for sub_id, turno_id, class_price, user_email, first_name, activity_name, turno_desc in pending:
            num_classes = await self._repo.count_clases_in_period(turno_id, period_month, period_year)
            if num_classes == 0:
                continue
            amount = Decimal(class_price) * num_classes
            charge_id = await self._repo.add_charge(
                subscription_id=sub_id,
                period_month=period_month,
                period_year=period_year,
                amount=amount,
                original_amount=amount,
                due_date=due_date,
            )
            notifications.append((charge_id, user_email, first_name, activity_name, turno_desc, amount))
            created += 1

        for charge_id, user_email, first_name, activity_name, turno_desc, amount in notifications:
            payment_url = await payment_service.create_subscription_charge_preference_for_notification(charge_id)
            email_service.send_subscription_charge_pending(
                to=user_email,
                first_name=first_name,
                activity_name=activity_name,
                turno_description=turno_desc,
                amount=amount,
                period_month=period_month,
                period_year=period_year,
                due_date=due_date,
                payment_url=payment_url,
            )
        return created

    async def _ensure_current_charges(
        self, user_id: int | None = None, period_month: int | None = None, period_year: int | None = None
    ) -> int:
        today = datetime.now(_ART).date()
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
