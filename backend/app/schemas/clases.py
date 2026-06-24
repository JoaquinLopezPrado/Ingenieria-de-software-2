from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel


class CancelClaseRequest(BaseModel):
    reason: str


class CancelPreviewAlumno(BaseModel):
    user_id: int
    full_name: str
    email: str
    # suscripcion = abono con el período pagado (recibe crédito);
    # suscripcion_impago = abono cuyo período no está pagado (se avisa, sin crédito).
    tipo: Literal["suscripcion", "suscripcion_impago", "individual_completo", "individual_senia"]
    amount: Decimal


class CancelPreviewResponse(BaseModel):
    clase_id: int
    clase_date: str
    turno_description: str
    afectados: List[CancelPreviewAlumno]
    total_afectados: int


class CreditInfo(BaseModel):
    id: int
    amount: Decimal
    expires_at: datetime
    source_clase_date: Optional[date] = None
