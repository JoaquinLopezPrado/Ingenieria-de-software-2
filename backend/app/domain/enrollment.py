import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import List


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


class MyMonthlyEnrollment:
    def __init__(
        self,
        enrollment_id: int,
        status: EnrollmentStatus,
        amount: Decimal,
        expires_at: datetime | None,
        created_at: datetime,
        turno_id: int,
        turno_description: str,
        month: int,
        year: int,
        start_time: time,
        end_time: time,
        instructor: str,
        activity_name: str,
        days: List[str],
    ):
        self.enrollment_id = enrollment_id
        self.status = status
        self.amount = amount
        self.expires_at = expires_at
        self.created_at = created_at
        self.turno_id = turno_id
        self.turno_description = turno_description
        self.month = month
        self.year = year
        self.start_time = start_time
        self.end_time = end_time
        self.instructor = instructor
        self.activity_name = activity_name
        self.days = days


class MySingleEnrollment:
    def __init__(
        self,
        enrollment_id: int,
        status: EnrollmentStatus,
        amount: Decimal,
        expires_at: datetime | None,
        created_at: datetime,
        clase_id: int,
        clase_date: date,
        start_time: time,
        end_time: time,
        turno_description: str,
        instructor: str,
        activity_name: str,
    ):
        self.enrollment_id = enrollment_id
        self.status = status
        self.amount = amount
        self.expires_at = expires_at
        self.created_at = created_at
        self.clase_id = clase_id
        self.clase_date = clase_date
        self.start_time = start_time
        self.end_time = end_time
        self.turno_description = turno_description
        self.instructor = instructor
        self.activity_name = activity_name
