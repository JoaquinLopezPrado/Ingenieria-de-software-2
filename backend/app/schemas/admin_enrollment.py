from datetime import date
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class AdminSubscriptionPreviewRequest(BaseModel):
    turno_id: int
    user_id: int


class ClasePreviewItem(BaseModel):
    clase_id: int
    fecha: date


class AdminSubscriptionPreviewResponse(BaseModel):
    turno_id: int
    user_id: int
    precio_por_clase: Decimal
    clases_con_cupo: List[ClasePreviewItem]
    clases_sin_cupo: List[ClasePreviewItem]
    clases_ya_abonadas: List[ClasePreviewItem]
    total: Decimal
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


class AdminWaitlistEntry(BaseModel):
    entry_id: int
    turno_id: int


class AdminWaitlistRequest(BaseModel):
    turno_id: int
    user_id: int


class AdminWaitlistResponse(BaseModel):
    entry_id: int
    turno_id: int
    user_id: int
