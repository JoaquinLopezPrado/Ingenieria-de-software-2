import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.turno_responses import CREATE_TURNO_RESPONSES, LIST_TURNOS_RESPONSES
from app.core.dependencies import get_db, require_roles
from app.repositories.activity_repository import ActivityRepository
from app.repositories.clase_repository import ClaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.turno_repository import TurnoRepository
from app.schemas.turno import CreateTurnoRequest, TurnoPageResponse, TurnoResponse
from app.services.turno_service import TurnoService

router = APIRouter()


def get_turno_service(db: AsyncSession = Depends(get_db)) -> TurnoService:
    return TurnoService(
        turno_repo=TurnoRepository(db),
        clase_repo=ClaseRepository(db),
        activity_repo=ActivityRepository(db),
        config_repo=ConfigRepository(db),
    )


@router.get(
    "",
    response_model=TurnoPageResponse,
    status_code=status.HTTP_200_OK,
    responses=LIST_TURNOS_RESPONSES,
)
async def list_turnos(
    activity_id: Optional[int] = Query(None),
    has_availability: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    _=require_roles("admin", "empleado", "cliente"),
    service: TurnoService = Depends(get_turno_service),
):
    items, total, page_size = await service.list(activity_id, has_availability, page)
    return TurnoPageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 1,
    )


@router.post(
    "",
    response_model=TurnoResponse,
    status_code=status.HTTP_201_CREATED,
    responses=CREATE_TURNO_RESPONSES,
)
async def create_turno(
    body: CreateTurnoRequest,
    _=require_roles("admin"),
    service: TurnoService = Depends(get_turno_service),
):
    return await service.create(
        activity_id=body.activity_id,
        description=body.description,
        instructor=body.instructor,
        start_time=body.start_time,
        end_time=body.end_time,
        capacity=body.capacity,
        price=body.price,
        month=body.month,
        year=body.year,
        days=body.days,
    )
