from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.user_responses import ME_RESPONSES
from app.core.dependencies import get_current_user_id, get_db
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserMeResponse
from app.services.user_service import UserService

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
    )


@router.get("/me", response_model=UserMeResponse, responses=ME_RESPONSES)
async def me(
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.get_me(user_id)