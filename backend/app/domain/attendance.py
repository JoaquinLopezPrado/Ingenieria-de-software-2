import enum
from datetime import date, datetime, time


class AttendanceStatus(str, enum.Enum):
    PRESENTE = "presente"
    AUSENTE = "ausente"


class Attendance:
    def __init__(
        self,
        id: int,
        user_id: int,
        clase_id: int,
        status: AttendanceStatus,
        marked_at: datetime,
    ):
        self.id = id
        self.user_id = user_id
        self.clase_id = clase_id
        self.status = status
        self.marked_at = marked_at


class MyAttendanceRecord:
    def __init__(
        self,
        clase_id: int,
        activity_name: str,
        clase_date: date,
        start_time: time,
        end_time: time,
        status: "AttendanceStatus | None",
    ):
        self.clase_id = clase_id
        self.activity_name = activity_name
        self.clase_date = clase_date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status


class CheckinResult:
    def __init__(
        self,
        first_name: str,
        last_name: str,
        activity_name: str,
        horario: str,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.activity_name = activity_name
        self.horario = horario


class AsistenciaRegistro:
    """Vista de un registro de asistencia para el historial de un cliente.

    Coincide con el shape que espera el frontend (asistenciasService.ts):
    actividad, fecha, horario y estado.
    """

    def __init__(
        self,
        id: int,
        activity_name: str,
        clase_date: date,
        start_time: time,
        end_time: time,
        status: AttendanceStatus,
    ):
        self.id = id
        self.activity_name = activity_name
        self.clase_date = clase_date
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
