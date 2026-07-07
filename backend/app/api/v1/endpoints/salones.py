from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.repositories.salon_repository import SalonRepository
from app.schemas.salon import CreateSalonRequest, SalonResponse, UpdateSalonRequest
from app.services.salon_service import SalonService

router = APIRouter()


def get_salon_service(db: AsyncSession = Depends(get_db)) -> SalonService:
    return SalonService(salon_repo=SalonRepository(db))


@router.get(
    "",
    response_model=list[SalonResponse],
    status_code=status.HTTP_200_OK,
)
async def list_salones(
    _=require_roles("admin", "empleado"),
    service: SalonService = Depends(get_salon_service),
):
    return await service.list()


@router.get(
    "/all",
    response_model=list[SalonResponse],
    status_code=status.HTTP_200_OK,
)
async def list_all_salones(
    _=require_roles("admin"),
    service: SalonService = Depends(get_salon_service),
):
    return await service.list_all()


@router.post(
    "",
    response_model=SalonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_salon(
    body: CreateSalonRequest,
    _=require_roles("admin"),
    service: SalonService = Depends(get_salon_service),
):
    return await service.create(name=body.name, capacity=body.capacity)


@router.patch(
    "/{salon_id}",
    response_model=SalonResponse,
    status_code=status.HTTP_200_OK,
)
async def update_salon(
    salon_id: int,
    body: UpdateSalonRequest,
    _=require_roles("admin"),
    service: SalonService = Depends(get_salon_service),
):
    return await service.update(salon_id, name=body.name, capacity=body.capacity)
