from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.repositories.reports_repository import ReportsRepository
from app.schemas.reports import (
    AusenciasResponse,
    CancelacionesResponse,
    IngresosResponse,
    OcupacionResponse,
)
from app.services.reports_service import ReportsService

router = APIRouter()


def get_reports_service(db: AsyncSession = Depends(get_db)) -> ReportsService:
    return ReportsService(ReportsRepository(db))


@router.get("/ingresos", response_model=IngresosResponse)
async def get_ingresos(
    desde: date = Query(...),
    hasta: date = Query(...),
    _=require_roles("admin", "empleado"),
    service: ReportsService = Depends(get_reports_service),
):
    return await service.get_ingresos(desde, hasta)


@router.get("/ocupacion", response_model=OcupacionResponse)
async def get_ocupacion(
    desde: date = Query(...),
    hasta: date = Query(...),
    _=require_roles("admin", "empleado"),
    service: ReportsService = Depends(get_reports_service),
):
    return await service.get_ocupacion(desde, hasta)


@router.get("/ausencias", response_model=AusenciasResponse)
async def get_ausencias(
    desde: date = Query(...),
    hasta: date = Query(...),
    _=require_roles("admin", "empleado"),
    service: ReportsService = Depends(get_reports_service),
):
    return await service.get_ausencias(desde, hasta)


@router.get("/cancelaciones", response_model=CancelacionesResponse)
async def get_cancelaciones(
    desde: date = Query(...),
    hasta: date = Query(...),
    _=require_roles("admin", "empleado"),
    service: ReportsService = Depends(get_reports_service),
):
    return await service.get_cancelaciones(desde, hasta)
