from app.domain.attendance import AsistenciaRegistro, Attendance, AttendanceStatus
from app.repositories.attendance_repository import AbstractAttendanceRepository, RosterEntry


class AttendanceService:

    def __init__(self, attendance_repo: AbstractAttendanceRepository):
        self._repo = attendance_repo

    async def get_historial(self, user_id: int) -> list[AsistenciaRegistro]:
        return await self._repo.get_historial_by_user(user_id=user_id)

    async def get_roster(self, clase_id: int) -> list[RosterEntry]:
        return await self._repo.get_roster(clase_id=clase_id)

    async def mark(self, user_id: int, clase_id: int, status: AttendanceStatus) -> Attendance:
        return await self._repo.mark(user_id=user_id, clase_id=clase_id, status=status)

    async def delete(self, user_id: int, clase_id: int) -> None:
        await self._repo.delete(user_id=user_id, clase_id=clase_id)
