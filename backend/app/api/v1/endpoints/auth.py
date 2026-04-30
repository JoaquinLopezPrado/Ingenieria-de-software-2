from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterClientRequest
from app.services.auth_service import AuthService
from app.api.v1.docs.auth_responses import REGISTER_RESPONSES

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, responses=REGISTER_RESPONSES)
async def register(
    data: RegisterClientRequest,
    service: AuthService = Depends(get_auth_service),
):
    await service.register_client(data)
    return {"message": "Registro exitoso."}
