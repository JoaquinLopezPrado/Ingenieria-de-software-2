from datetime import date, datetime, time
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, field_serializer

from app.domain.single_enrollment import SingleEnrollmentStatus


def _fmt_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


class CreateSingleEnrollmentRequest(BaseModel):
    clase_ids: list[int] = Field(min_length=1)


class SingleEnrollmentResponse(BaseModel):
    id: int
    turno_id: int
    amount: Decimal
    status: SingleEnrollmentStatus
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class MySingleEnrollmentResponse(BaseModel):
    enrollment_id: int
    status: SingleEnrollmentStatus
    amount: Decimal
    expires_at: datetime | None
    created_at: datetime
    turno_id: int
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
