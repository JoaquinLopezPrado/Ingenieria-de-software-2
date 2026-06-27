from datetime import date, time

from pydantic import BaseModel, computed_field

from app.domain.attendance import AttendanceStatus, CheckinResult, MyAttendanceRecord


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


class MyAttendanceResponse(BaseModel):
    clase_id: int
    activity_name: str
    clase_date: date
    horario: str
    estado: AttendanceStatus | None = None

    @classmethod
    def from_record(cls, r: MyAttendanceRecord) -> "MyAttendanceResponse":
        return cls(
            clase_id=r.clase_id,
            activity_name=r.activity_name,
            clase_date=r.clase_date,
            horario=f"{r.start_time.hour:02d}:{r.start_time.minute:02d} – {r.end_time.hour:02d}:{r.end_time.minute:02d}",
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


class CheckinRequest(BaseModel):
    user_id: int
    clase_id: int


class CheckinResponse(BaseModel):
    ok: bool
    first_name: str
    last_name: str
    activity_name: str
    horario: str

    @classmethod
    def from_result(cls, r: CheckinResult) -> "CheckinResponse":
        return cls(
            ok=True,
            first_name=r.first_name,
            last_name=r.last_name,
            activity_name=r.activity_name,
            horario=r.horario,
        )


class MarkAttendanceRequest(BaseModel):
    user_id: int
    clase_id: int
    estado: AttendanceStatus


class DeleteAttendanceRequest(BaseModel):
    user_id: int
    clase_id: int
