from dataclasses import dataclass
from decimal import Decimal

from app.domain.enrollment import EnrollmentStatus


@dataclass
class EnrollmentPaymentDetails:
    enrollment_id: int
    user_id: int
    status: EnrollmentStatus
    activity_name: str
    turno_description: str
    price: Decimal
