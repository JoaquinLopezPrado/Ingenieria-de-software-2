from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import ChargeStatus


@dataclass
class SubscriptionChargeDetails:
    """Datos necesarios para cobrar y confirmar un cargo mensual de suscripción."""
    charge_id: int
    subscription_id: int
    user_id: int
    status: ChargeStatus
    amount: Decimal
    activity_name: str
    turno_description: str
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    activity_id: int
    period_month: int
    period_year: int
    expires_at: Optional[datetime] = None
    original_amount: Decimal = Decimal(0)


@dataclass
class SingleDetails:
    """Datos necesarios para cobrar y confirmar una inscripción a clase suelta."""
    enrollment_id: int
    user_id: int
    status: SingleEnrollmentStatus
    amount: Decimal
    activity_name: str
    turno_description: str
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    activity_id: int
    expires_at: Optional[datetime] = None
    clase_dates: list[date] = field(default_factory=list)
    clase_start: Optional[datetime] = None


@dataclass
class Payment:
    id: int
    amount: Decimal
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    payment_provider_id: str
    confirmed_at: datetime
    activity_id: Optional[int]
    activity_name_snapshot: str
    month_snapshot: int
    year_snapshot: int
    source_type_snapshot: str
    subscription_charge_id: Optional[int] = None
    single_enrollment_id: Optional[int] = None
