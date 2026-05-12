from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.activity_responses import CREATE_ACTIVITY_RESPONSES
from app.core.dependencies import get_db, require_roles
from app.repositories.activity_repository import ActivityRepository
from app.schemas.activity import ActivityResponse, CreateActivityRequest
from app.services.activity_service import ActivityService

router = APIRouter()


def get_activity_service(db: AsyncSession = Depends(get_db)) -> ActivityService:
    return ActivityService(activity_repo=ActivityRepository(db))


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
    return await service.create(name=body.name, instructor=body.instructor)
