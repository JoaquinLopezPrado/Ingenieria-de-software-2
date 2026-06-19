import enum
from datetime import date, datetime, time
from decimal import Decimal


class SingleEnrollmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DEPOSIT_PAID = "deposit_paid"
    DEPOSIT_FORFEITED = "deposit_forfeited"
    REFUNDED = "refunded"


class SingleEnrollment:
    """Reserva de una o más clases sueltas (drop-in). Admite seña (depósito 30%)."""

    def __init__(
        self,
        id: int,
        turno_id: int,
        user_id: int,
        amount: Decimal,
        status: SingleEnrollmentStatus,
        expires_at: datetime | None,
        payment_id: str | None,
        created_at: datetime,
        deposit_amount: Decimal | None = None,
        deposit_payment_id: str | None = None,
        refund_id: str | None = None,
    ):
        self.id = id
        self.turno_id = turno_id
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.expires_at = expires_at
        self.payment_id = payment_id
        self.created_at = created_at
        self.deposit_amount = deposit_amount
        self.deposit_payment_id = deposit_payment_id
        self.refund_id = refund_id


class MySingleEnrollment:
    def __init__(
        self,
        enrollment_id: int,
        status: SingleEnrollmentStatus,
        amount: Decimal,
        expires_at: datetime | None,
        created_at: datetime,
        turno_id: int,
        clase_id: int,
        clase_date: date,
        start_time: time,
        end_time: time,
        turno_description: str,
        instructor: str,
        activity_name: str,
        deposit_amount: Decimal | None = None,
        deposit_payment_id: str | None = None,
    ):
        self.enrollment_id = enrollment_id
        self.status = status
        self.amount = amount
        self.expires_at = expires_at
        self.created_at = created_at
        self.turno_id = turno_id
        self.clase_id = clase_id
        self.clase_date = clase_date
        self.start_time = start_time
        self.end_time = end_time
        self.turno_description = turno_description
        self.instructor = instructor
        self.activity_name = activity_name
        self.deposit_amount = deposit_amount
        self.deposit_payment_id = deposit_payment_id
