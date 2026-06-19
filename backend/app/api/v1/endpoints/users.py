from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.user_responses import ME_RESPONSES
from app.core.dependencies import get_current_user_id, get_db, require_roles
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.attendance import AsistenciaResponse
from app.schemas.user import UserMeResponse
from app.services.attendance_service import AttendanceService
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
    )


def get_attendance_service(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    return AttendanceService(attendance_repo=AttendanceRepository(db))


@router.get("/me", response_model=UserMeResponse, responses=ME_RESPONSES)
async def me(
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.get_me(user_id)


@router.get("/{user_id}/asistencias", response_model=list[AsistenciaResponse])
async def get_user_asistencias(
    user_id: int,
    _=require_roles("admin", "empleado"),
    service: AttendanceService = Depends(get_attendance_service),
):
    registros = await service.get_historial(user_id=user_id)
    return [AsistenciaResponse.from_registro(r) for r in registros]