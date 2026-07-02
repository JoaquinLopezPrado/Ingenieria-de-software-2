from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.user_responses import ME_RESPONSES
from app.core.dependencies import get_current_user_id, get_db, require_roles
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waitlist_repository import WaitlistRepository
from app.schemas.attendance import AsistenciaResponse
from app.schemas.user import ClienteListItem, ClientesPaginadosResponse, UserMeResponse, UpdateClientPhoneRequest
from app.services.attendance_service import AttendanceService
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
        subscription_repo=SubscriptionRepository(db),
        single_enrollment_repo=SingleEnrollmentRepository(db),
        waitlist_repo=WaitlistRepository(db),
    )


def get_attendance_service(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    return AttendanceService(attendance_repo=AttendanceRepository(db))


@router.get("/me", response_model=UserMeResponse, responses=ME_RESPONSES)
async def me(
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.get_me(user_id)


@router.patch("/me/phone", response_model=UserMeResponse)
async def update_my_phone(
    data: UpdateClientPhoneRequest,
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.update_my_phone(user_id=user_id, data=data)


@router.get("", response_model=ClientesPaginadosResponse)
async def list_clients(
    q: Optional[str] = Query(default=None, description="Buscar por nombre, apellido o documento"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _=require_roles("admin", "empleado"),
    service: UserService = Depends(get_user_service),
):
    return await service.list_clients(q=q or None, page=page, page_size=page_size)


@router.get("/{user_id}/asistencias", response_model=list[AsistenciaResponse])
async def get_user_asistencias(
    user_id: int,
    _=require_roles("admin", "empleado"),
    service: AttendanceService = Depends(get_attendance_service),
):
    registros = await service.get_historial(user_id=user_id)
    return [AsistenciaResponse.from_registro(r) for r in registros]


@router.patch("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_client(
    user_id: int,
    _=require_roles("admin"),
    service: UserService = Depends(get_user_service),
):
    await service.deactivate_client(user_id)


@router.patch("/{user_id}/reactivate", status_code=status.HTTP_204_NO_CONTENT)
async def reactivate_client(
    user_id: int,
    _=require_roles("admin"),
    service: UserService = Depends(get_user_service),
):
    await service.reactivate_client(user_id)


@router.get("/{user_id}", response_model=ClienteListItem)
async def get_client(
    user_id: int,
    _=require_roles("admin", "empleado"),
    service: UserService = Depends(get_user_service),
):
    return await service.get_client_by_id(user_id)
