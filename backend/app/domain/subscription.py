import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import List


class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"      # creada, primer cargo sin pagar; ocupa el asiento durante el TTL
    ACTIVE = "active"        # al menos un cargo pagado
    PAUSED = "paused"
    CANCELLED = "cancelled"


# Estados en los que la suscripción ocupa su asiento en el turno.
OCCUPYING_SUBSCRIPTION_STATUSES = (SubscriptionStatus.PENDING, SubscriptionStatus.ACTIVE)


class ChargeStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"


class Subscription:
    def __init__(
        self,
        id: int,
        user_id: int,
        turno_id: int,
        status: SubscriptionStatus,
        start_date: date,
        cancelled_at: datetime | None = None,
        created_at: datetime | None = None,
        ends_on: date | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.turno_id = turno_id
        self.status = status
        self.start_date = start_date
        self.cancelled_at = cancelled_at
        self.created_at = created_at
        # Si está seteada: baja programada. Sigue ocupando el lugar hasta esta fecha (fin del período pagado).
        self.ends_on = ends_on


class SubscriptionCharge:
    """Cobro de un período mensual de una suscripción.

    ``original_amount`` se persiste (precio del período sin descuentos). El descuento
    total es ``original_amount - amount``. ``discount_deposit_single`` es transitorio:
    se calcula para mostrar el desglose en el ticket pero no se guarda.
    """

    def __init__(
        self,
        id: int,
        subscription_id: int,
        period_month: int,
        period_year: int,
        amount: Decimal,
        status: ChargeStatus,
        due_date: date | None = None,
        paid_at: datetime | None = None,
        payment_id: str | None = None,
        original_amount: Decimal | None = None,
        created_at: datetime | None = None,
        expires_at: datetime | None = None,
        discount_deposit_single: Decimal | None = None,
    ):
        self.id = id
        self.subscription_id = subscription_id
        self.period_month = period_month
        self.period_year = period_year
        self.amount = amount
        self.status = status
        self.due_date = due_date
        self.paid_at = paid_at
        self.payment_id = payment_id
        self.original_amount = original_amount if original_amount is not None else amount
        self.created_at = created_at
        self.expires_at = expires_at
        self.discount_deposit_single = discount_deposit_single if discount_deposit_single is not None else Decimal(0)


class MySubscription:
    """Vista enriquecida de la suscripción de un cliente, con datos del turno."""

    def __init__(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
        start_date: date,
        turno_id: int,
        turno_description: str,
        start_time: time,
        end_time: time,
        instructor: str,
        activity_name: str,
        days: List[str],
        pending_charge: "SubscriptionCharge | None" = None,
        ends_on: date | None = None,
    ):
        self.subscription_id = subscription_id
        self.status = status
        self.start_date = start_date
        self.ends_on = ends_on
        self.turno_id = turno_id
        self.turno_description = turno_description
        self.start_time = start_time
        self.end_time = end_time
        self.instructor = instructor
        self.activity_name = activity_name
        self.days = days
        self.pending_charge = pending_charge
