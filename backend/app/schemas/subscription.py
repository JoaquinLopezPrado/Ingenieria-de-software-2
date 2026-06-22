from datetime import date, datetime, time
from decimal import Decimal
from typing import List

from pydantic import BaseModel, field_serializer

from app.domain.subscription import ChargeStatus, SubscriptionStatus
from app.domain.waitlist import WaitlistStatus


def _fmt_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


class CreateSubscriptionRequest(BaseModel):
    turno_id: int


class SubscriptionChargeResponse(BaseModel):
    """Respuesta al crear una suscripción: el cargo del primer período (para el ticket)."""
    charge_id: int
    subscription_id: int
    period_month: int
    period_year: int
    amount: Decimal
    original_amount: Decimal
    discount_deposit_single: Decimal
    discount_full_classes: Decimal
    status: ChargeStatus
    expires_at: datetime | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_charge(cls, charge) -> "SubscriptionChargeResponse":
        return cls(
            charge_id=charge.id,
            subscription_id=charge.subscription_id,
            period_month=charge.period_month,
            period_year=charge.period_year,
            amount=charge.amount,
            original_amount=charge.original_amount,
            discount_deposit_single=charge.discount_deposit_single,
            discount_full_classes=charge.discount_full_classes,
            status=charge.status,
            expires_at=charge.expires_at,
        )


class PendingChargeResponse(BaseModel):
    charge_id: int
    period_month: int
    period_year: int
    amount: Decimal
    original_amount: Decimal
    status: ChargeStatus
    due_date: date | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class PaidChargeResponse(BaseModel):
    charge_id: int
    period_month: int
    period_year: int
    amount: Decimal
    paid_at: datetime | None
    activity_name: str
    turno_description: str
    instructor: str


class OverdueSubscriptionResponse(BaseModel):
    subscription_id: int
    user_id: int
    turno_description: str
    activity_name: str
    unpaid_count: int


class CancelSubscriptionsRequest(BaseModel):
    subscription_ids: List[int]


class MySubscriptionResponse(BaseModel):
    subscription_id: int
    status: SubscriptionStatus
    start_date: date
    ends_on: date | None = None
    turno_id: int
    turno_description: str
    start_time: time
    end_time: time
    instructor: str
    activity_name: str
    days: List[str]
    pending_charge: PendingChargeResponse | None = None

    model_config = {"from_attributes": True}

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _fmt_time(value)


class JoinWaitlistRequest(BaseModel):
    turno_id: int


class WaitlistEntryResponse(BaseModel):
    entry_id: int
    turno_id: int
    turno_description: str
    activity_name: str
    instructor: str
    start_time: time
    end_time: time
    days: List[str]
    joined_at: datetime
    status: WaitlistStatus

    model_config = {"from_attributes": True}

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _fmt_time(value)
