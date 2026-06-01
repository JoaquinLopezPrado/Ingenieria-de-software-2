from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.enrollment import EnrollmentStatus


@dataclass
class EnrollmentPaymentDetails:
    enrollment_id: int
    user_id: int
    status: EnrollmentStatus
    activity_name: str
    turno_description: str
    price: Decimal
    expires_at: Optional[datetime]
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    activity_id: int
    month: int
    year: int
    enrollment_type: str
    original_amount: Decimal = Decimal(0)
    discount_full_classes: Decimal = Decimal(0)


@dataclass
class Payment:
    id: int
    enrollment_id: int
    amount: Decimal
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    payment_provider_id: str
    confirmed_at: datetime
    activity_id: Optional[int]
    activity_name_snapshot: str
    month_snapshot: int
    year_snapshot: int
    enrollment_type_snapshot: str
