from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel


class CancelClaseRequest(BaseModel):
    reason: str


class CancelPreviewAlumno(BaseModel):
    user_id: int
    full_name: str
    email: str
    tipo: Literal["suscripcion", "individual_completo", "individual_senia"]
    amount: Decimal


class CancelPreviewResponse(BaseModel):
    clase_id: int
    clase_date: str
    turno_description: str
    afectados: List[CancelPreviewAlumno]
    total_afectados: int
