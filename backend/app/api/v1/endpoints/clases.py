from fastapi import APIRouter, Depends, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.domain.user import User
from app.schemas.clases import CancelClaseRequest, CancelPreviewResponse
from app.services.clase_cancellation_service import ClaseCancellationService

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> ClaseCancellationService:
    return ClaseCancellationService(db)


@router.get("/{clase_id}/cancel-preview", response_model=CancelPreviewResponse)
async def cancel_preview(
    clase_id: int,
    current_user: User = require_roles("admin"),
    service: ClaseCancellationService = Depends(_get_service),
) -> CancelPreviewResponse:
    return await service.get_preview(clase_id)


@router.post("/{clase_id}/cancel", status_code=http_status.HTTP_200_OK)
async def cancel_clase(
    clase_id: int,
    req: CancelClaseRequest,
    current_user: User = require_roles("admin"),
    service: ClaseCancellationService = Depends(_get_service),
) -> dict:
    await service.cancel(clase_id, req, current_user.id)
    return {"message": "Clase cancelada exitosamente."}
