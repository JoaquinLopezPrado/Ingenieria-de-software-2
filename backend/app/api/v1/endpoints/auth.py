from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.auth_responses import LOGIN_RESPONSES, LOGOUT_RESPONSES, REFRESH_RESPONSES, REGISTER_RESPONSES
from app.core.dependencies import get_current_user_id, get_db
from app.repositories.profile_repository import ProfileRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginCredentials, LogoutRequest, RefreshTokenRequest, RegisterClientRequest, Token
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        profile_repo=ProfileRepository(db),
        token_repo=TokenRepository(db),
    )


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, responses=REGISTER_RESPONSES
)
async def register(
    data: RegisterClientRequest,
    service: AuthService = Depends(get_auth_service),
):
    await service.register_client(data)
    return {"message": "Registro exitoso."}


@router.post("/login", response_model=Token, responses=LOGIN_RESPONSES)
async def login(
    data: LoginCredentials,
    service: AuthService = Depends(get_auth_service),
):
    _, access_token, refresh_token = await service.login(data)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, responses=REFRESH_RESPONSES)
async def refresh(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    access_token, refresh_token = await service.refresh(data)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK, responses=LOGOUT_RESPONSES)
async def logout(
    data: LogoutRequest,
    user_id: int = Depends(get_current_user_id),
    service: AuthService = Depends(get_auth_service),
):
    await service.logout(user_id, data.refresh_token)
    return {"message": "Sesión cerrada exitosamente."}
