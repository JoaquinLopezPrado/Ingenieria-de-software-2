from datetime import date, time

from pydantic import BaseModel, computed_field

from app.domain.attendance import AttendanceStatus


def _fmt_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


class AsistenciaResponse(BaseModel):
    """Shape esperado por el frontend (asistenciasService.ts)."""
    id: int
    actividad: str
    fecha: date
    horario: str
    estado: AttendanceStatus

    @classmethod
    def from_registro(cls, r) -> "AsistenciaResponse":
        return cls(
            id=r.id,
            actividad=r.activity_name,
            fecha=r.clase_date,
            horario=f"{_fmt_time(r.start_time)} – {_fmt_time(r.end_time)}",
            estado=r.status,
        )


class RosterEntryResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    source: str
    estado: AttendanceStatus | None = None

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_entry(cls, e) -> "RosterEntryResponse":
        return cls(
            user_id=e.user_id,
            first_name=e.first_name,
            last_name=e.last_name,
            source=e.source,
            estado=e.status,
        )


class MarkAttendanceRequest(BaseModel):
    user_id: int
    clase_id: int
    estado: AttendanceStatus


class DeleteAttendanceRequest(BaseModel):
    user_id: int
    clase_id: int
