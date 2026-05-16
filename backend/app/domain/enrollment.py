import enum
from datetime import datetime
from decimal import Decimal


class EnrollmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class EnrollmentType(str, enum.Enum):
    MONTHLY = "monthly"
    SINGLE = "single"


class Enrollment:
    def __init__(
        self,
        id: int,
        turno_id: int,
        user_id: int,
        enrollment_type: EnrollmentType,
        amount: Decimal,
        status: EnrollmentStatus,
        expires_at: datetime | None,
        payment_id: str | None,
        created_at: datetime,
        excluded_clase_ids: list[int] | None = None,
    ):
        self.id = id
        self.turno_id = turno_id
        self.user_id = user_id
        self.enrollment_type = enrollment_type
        self.amount = amount
        self.status = status
        self.expires_at = expires_at
        self.payment_id = payment_id
        self.created_at = created_at
        self.excluded_clase_ids = excluded_clase_ids or []
