from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class AdminSubscriptionPreviewRequest(BaseModel):
    turno_id: int
    user_id: int


class AdminSubscriptionPreviewResponse(BaseModel):
    amount: Decimal
    period_month: int
    period_year: int


class AdminSubscriptionEnrollRequest(BaseModel):
    turno_id: int
    user_id: int


class AdminSubscriptionEnrollResponse(BaseModel):
    subscription_id: int
    charge_id: int
    amount: Decimal
    period_month: int
    period_year: int


class AdminSingleEnrollRequest(BaseModel):
    clase_ids: List[int] = Field(min_length=1)
    user_id: int


class AdminSingleEnrollResponse(BaseModel):
    enrollment_id: int
    amount: Decimal
