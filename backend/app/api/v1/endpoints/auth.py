from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.docs.auth_responses import LOGIN_RESPONSES, LOGOUT_RESPONSES, REFRESH_RESPONSES, REGISTER_RESPONSES
from app.core.config import settings
from app.core.dependencies import get_current_user_id, get_db
from app.repositories.profile_repository import ProfileRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import GoogleCompleteRequest, LoginCredentials, LogoutRequest, RefreshTokenRequest, RegisterClientRequest, Token
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


@router.get("/google", include_in_schema=True)
async def google_oauth_start(service: AuthService = Depends(get_auth_service)):
    """Redirige al usuario a la pantalla de login de Google."""
    url = service.get_google_oauth_url()
    return RedirectResponse(url=url)


@router.get("/google/callback", include_in_schema=False)
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    service: AuthService = Depends(get_auth_service),
):
    """Recibe el callback de Google, emite tokens o redirige al formulario de completar registro."""
    result = await service.handle_google_callback(code, state)
    frontend = settings.mp_frontend_url.rstrip("/")

    if result["type"] == "login":
        params = urlencode({
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        })
        return RedirectResponse(url=f"{frontend}/auth/callback?{params}")

    params = urlencode({
        "pending_token": result["pending_token"],
        "email": result["email"],
        "first_name": result["first_name"],
        "last_name": result["last_name"],
    })
    return RedirectResponse(url=f"{frontend}/auth/google-complete?{params}")


@router.post("/google/complete", response_model=Token, status_code=status.HTTP_201_CREATED)
async def google_complete_registration(
    data: GoogleCompleteRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Completa el registro de un usuario nuevo de Google con los datos faltantes."""
    access_token, refresh_token = await service.google_complete_registration(data)
    return Token(access_token=access_token, refresh_token=refresh_token)
