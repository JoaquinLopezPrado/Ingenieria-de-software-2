from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.turno import _parse_time


class CancelClaseRequest(BaseModel):
    reason: str


class UpdateClaseHorarioRequest(BaseModel):
    """Modifica el horario/fecha/cupo de una clase individual, sin afectar al resto
    del turno. La fecha se valida contra hoy en el repositorio."""
    date: date
    start_time: time
    end_time: time
    capacity: int = Field(gt=0)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_time_fields(cls, v: object) -> time:
        return _parse_time(v)

    @model_validator(mode="after")
    def end_time_after_start_time(self) -> "UpdateClaseHorarioRequest":
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio.")
        return self


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


class ClaseHoyResponse(BaseModel):
    clase_id: int
    activity_name: str
    instructor: str
    start_time: str
    end_time: str
    capacity: int
    is_active: bool

    @classmethod
    def from_clase(cls, c) -> "ClaseHoyResponse":
        return cls(
            clase_id=c.clase_id,
            activity_name=c.activity_name,
            instructor=c.instructor,
            start_time=f"{c.start_time.hour:02d}:{c.start_time.minute:02d}",
            end_time=f"{c.end_time.hour:02d}:{c.end_time.minute:02d}",
            capacity=c.capacity,
            is_active=c.is_active,
        )
