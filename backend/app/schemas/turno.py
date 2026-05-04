from datetime import time
from typing import List

from pydantic import BaseModel, Field, field_serializer, field_validator

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
    name: str = Field(min_length=1, max_length=100)
    time: time
    capacity: int = Field(gt=0)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2024)
    days: List[DiaSemana] = Field(min_length=1)

    @field_validator("time", mode="before")
    @classmethod
    def parse_time(cls, v: object) -> time:
        return _parse_time(v)

    @field_validator("days")
    @classmethod
    def no_duplicate_days(cls, v: List[DiaSemana]) -> List[DiaSemana]:
        if len(v) != len(set(v)):
            raise ValueError("No puede haber días repetidos.")
        return v


class TurnoResponse(BaseModel):
    id: int
    activity_id: int
    name: str
    time: time
    capacity: int
    month: int
    year: int
    is_active: bool
    days: List[DiaSemana]

    @field_serializer("time")
    def serialize_time(self, value: time) -> str:
        return _format_time(value)
