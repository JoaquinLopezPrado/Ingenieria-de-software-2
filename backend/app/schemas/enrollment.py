from datetime import date, datetime, time
from decimal import Decimal
from typing import List

from pydantic import BaseModel, field_serializer

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


def _fmt_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


class MyMonthlyEnrollmentResponse(BaseModel):
    enrollment_id: int
    status: EnrollmentStatus
    amount: Decimal
    expires_at: datetime | None
    created_at: datetime
    turno_id: int
    turno_description: str
    month: int
    year: int
    start_time: time
    end_time: time
    instructor: str
    activity_name: str
    days: List[str]

    model_config = {"from_attributes": True}

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _fmt_time(value)


class MySingleEnrollmentResponse(BaseModel):
    enrollment_id: int
    status: EnrollmentStatus
    amount: Decimal
    expires_at: datetime | None
    created_at: datetime
    clase_id: int
    clase_date: date
    start_time: time
    end_time: time
    turno_description: str
    instructor: str
    activity_name: str

    model_config = {"from_attributes": True}

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _fmt_time(value)
