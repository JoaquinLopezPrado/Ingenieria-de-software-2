from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from app.domain.turno import DiaSemana


def _parse_time(value: object) -> time:
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        parts = value.split(":")
        try:
            return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            raise ValueError("Formato de hora inválido. Use HH:MM (ej: 9:30, 17:00).")
    raise ValueError("Tipo inválido para el campo hora.")


def _format_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


class CreateTurnoRequest(BaseModel):
    activity_id: int
    description: str = Field(min_length=1, max_length=200)
    instructor: str = Field(min_length=1, max_length=200)
    start_time: time
    end_time: time
    capacity: int = Field(gt=0)
    class_price: Decimal = Field(gt=0)
    days: List[DiaSemana] = Field(min_length=1)
    start_date: date
    is_active: bool = False

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_time_fields(cls, v: object) -> time:
        return _parse_time(v)

    @field_validator("days")
    @classmethod
    def no_duplicate_days(cls, v: List[DiaSemana]) -> List[DiaSemana]:
        if len(v) != len(set(v)):
            raise ValueError("No puede haber días repetidos.")
        return v

    @model_validator(mode="after")
    def end_time_after_start_time(self) -> "CreateTurnoRequest":
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio.")
        return self


class UpdateTurnoRequest(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    instructor: str = Field(min_length=1, max_length=200)
    start_time: time
    end_time: time
    capacity: int = Field(gt=0)
    class_price: Decimal = Field(gt=0)
    days: List[DiaSemana] = Field(min_length=1)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def parse_time_fields(cls, v: object) -> time:
        return _parse_time(v)

    @field_validator("days")
    @classmethod
    def no_duplicate_days(cls, v: List[DiaSemana]) -> List[DiaSemana]:
        if len(v) != len(set(v)):
            raise ValueError("No puede haber días repetidos.")
        return v

    @model_validator(mode="after")
    def end_time_after_start_time(self) -> "UpdateTurnoRequest":
        if self.end_time <= self.start_time:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio.")
        return self


class UpdateTurnoPreviewResponse(BaseModel):
    horario_cambia: bool
    dias_agregados: List[DiaSemana]
    dias_quitados: List[DiaSemana]
    clases_a_cancelar: int
    clientes_afectados: int
    creditos_a_generar: int
    clases_a_generar: int
    usuarios_a_notificar: int


class SetTurnoActiveRequest(BaseModel):
    is_active: bool


class DeactivationImpactResponse(BaseModel):
    clases_a_cancelar: int
    creditos_a_generar: int
    clientes_afectados: int
    suscripciones_a_baja: int
    usuarios_a_notificar: int


class ClaseDetalleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turno_id: int
    date: date
    start_time: time
    end_time: time
    capacity: int
    enrolled: int
    presentes_count: int
    is_active: bool
    cancelled_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _format_time(value)


class GenerateClassesResponse(BaseModel):
    generated: int


class TurnoPageResponse(BaseModel):
    items: List["TurnoResponse"]
    total: int
    page: int
    page_size: int
    pages: int


class TurnoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_id: int
    description: str
    instructor: str
    start_time: time
    end_time: time
    capacity: int
    class_price: Decimal
    is_active: bool
    days: List[DiaSemana]
    enrolled: int
    has_remaining_classes: bool
    has_future_classes: bool

    @field_serializer("start_time", "end_time")
    def serialize_time(self, value: time) -> str:
        return _format_time(value)
