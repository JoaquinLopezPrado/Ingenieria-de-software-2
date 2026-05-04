from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.turno_responses import CREATE_TURNO_RESPONSES
from app.core.dependencies import get_db, require_admin
from app.domain.user import User
from app.repositories.activity_repository import ActivityRepository
from app.repositories.clase_repository import ClaseRepository
from app.repositories.turno_repository import TurnoRepository
from app.schemas.turno import CreateTurnoRequest, TurnoResponse
from app.services.turno_service import TurnoService

router = APIRouter()


def get_turno_service(db: AsyncSession = Depends(get_db)) -> TurnoService:
    return TurnoService(
        turno_repo=TurnoRepository(db),
        clase_repo=ClaseRepository(db),
        activity_repo=ActivityRepository(db),
    )


@router.post(
    "",
    response_model=TurnoResponse,
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_TURNO_RESPONSES,
)
async def create_turno(
    body: CreateTurnoRequest,
    _: User = Depends(require_admin),
    service: TurnoService = Depends(get_turno_service),
):
    return await service.create(
        activity_id=body.activity_id,
        name=body.name,
        time=body.time,
        capacity=body.capacity,
        month=body.month,
        year=body.year,
        days=body.days,
    )
