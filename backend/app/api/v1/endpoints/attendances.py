from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import DeleteAttendanceRequest, MarkAttendanceRequest, RosterEntryResponse
from app.services.attendance_service import AttendanceService

router = APIRouter()


def get_attendance_service(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    return AttendanceService(attendance_repo=AttendanceRepository(db))


@router.get("/roster/{clase_id}", response_model=list[RosterEntryResponse], status_code=status.HTTP_200_OK)
async def get_clase_roster(
    clase_id: int,
    _=require_roles("admin", "empleado"),
    service: AttendanceService = Depends(get_attendance_service),
):
    entries = await service.get_roster(clase_id=clase_id)
    return [RosterEntryResponse.from_entry(e) for e in entries]


@router.post("", status_code=status.HTTP_200_OK)
async def mark_attendance(
    body: MarkAttendanceRequest,
    _=require_roles("admin", "empleado"),
    service: AttendanceService = Depends(get_attendance_service),
):
    await service.mark(user_id=body.user_id, clase_id=body.clase_id, status=body.estado)
    return {"ok": True}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    body: DeleteAttendanceRequest,
    _=require_roles("admin", "empleado"),
    service: AttendanceService = Depends(get_attendance_service),
):
    await service.delete(user_id=body.user_id, clase_id=body.clase_id)
