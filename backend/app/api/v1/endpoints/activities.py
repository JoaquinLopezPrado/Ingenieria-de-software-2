from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.activity_responses import CREATE_ACTIVITY_RESPONSES, LIST_ACTIVITIES_RESPONSES
from app.core.dependencies import get_db, require_roles
from app.repositories.activity_repository import ActivityRepository
from app.repositories.clase_repository import ClaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.turno_repository import TurnoRepository
from app.schemas.activity import ActivityResponse, ClaseDiaResponse, CreateActivityRequest
from app.services.activity_service import ActivityService
from app.services.turno_service import TurnoService

router = APIRouter()


def get_activity_service(db: AsyncSession = Depends(get_db)) -> ActivityService:
    return ActivityService(activity_repo=ActivityRepository(db))


def get_turno_service(db: AsyncSession = Depends(get_db)) -> TurnoService:
    return TurnoService(
        turno_repo=TurnoRepository(db),
        clase_repo=ClaseRepository(db),
        activity_repo=ActivityRepository(db),
        config_repo=ConfigRepository(db),
    )


@router.get(
    "",
    response_model=list[ActivityResponse],
    status_code=status.HTTP_200_OK,
    responses=LIST_ACTIVITIES_RESPONSES,
)
async def list_activities(
    _=require_roles("admin", "empleado", "cliente"),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.list()


@router.get(
    "/all",
    response_model=list[ActivityResponse],
    status_code=status.HTTP_200_OK,
)
async def list_all_activities(
    _=require_roles("admin"),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.list_all()


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_ACTIVITY_RESPONSES,
)
async def create_activity(
    body: CreateActivityRequest,
    _=require_roles("admin"),
    service: ActivityService = Depends(get_activity_service),
):
    return await service.create(name=body.name, description=body.description)


@router.get(
    "/{activity_id}/clases",
    response_model=list[ClaseDiaResponse],
    status_code=status.HTTP_200_OK,
)
async def list_clases_by_activity(
    activity_id: int,
    _=require_roles("admin", "empleado", "cliente"),
    service: TurnoService = Depends(get_turno_service),
):
    return await service.list_clases_by_activity(activity_id)
