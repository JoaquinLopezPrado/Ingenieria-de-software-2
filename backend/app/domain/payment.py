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


@dataclass
class Payment:
    id: int
    enrollment_id: int
    amount: Decimal
    class_price_snapshot: Decimal
    num_classes_snapshot: int
    payment_provider_id: str
    confirmed_at: datetime
