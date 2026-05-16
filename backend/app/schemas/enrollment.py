from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domain.enrollment import EnrollmentStatus, EnrollmentType


class CreateMonthlyEnrollmentRequest(BaseModel):
    turno_id: int


class CreateSingleEnrollmentRequest(BaseModel):
    clase_id: int


class EnrollmentResponse(BaseModel):
    id: int
    turno_id: int
    enrollment_type: EnrollmentType
    amount: Decimal
    status: EnrollmentStatus
    expires_at: datetime | None
    excluded_clase_ids: list[int]

    model_config = {"from_attributes": True}
