from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.domain.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Confirm2FARequest, Disable2FARequest, Setup2FAResponse, Token, Verify2FARequest
from app.services.two_factor_service import TwoFactorService
from app.utils.security import decode_pre_auth_token, create_access_token, create_refresh_token
from app.utils.security import hash_token
from datetime import datetime, timedelta, timezone
from app.core.config import settings

router = APIRouter()


def get_2fa_service(db: AsyncSession = Depends(get_db)) -> TwoFactorService:
    return TwoFactorService(user_repo=UserRepository(db))


@router.post("/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    user: User = Depends(get_current_user),
    service: TwoFactorService = Depends(get_2fa_service),
):
    """Genera un secreto TOTP y el QR para escanear. No activa el 2FA todavía."""
    if user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El 2FA ya está habilitado en tu cuenta.",
        )
    return service.generate_setup(user.email)


@router.post("/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_2fa(
    data: Confirm2FARequest,
    user: User = Depends(get_current_user),
    service: TwoFactorService = Depends(get_2fa_service),
):
    """Verifica el código e imprime el secreto en la cuenta. Activa el 2FA."""
    if user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El 2FA ya está habilitado en tu cuenta.",
        )
    await service.confirm_setup(user.id, data.secret, data.code)


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_2fa(
    data: Disable2FARequest,
    user: User = Depends(get_current_user),
    service: TwoFactorService = Depends(get_2fa_service),
):
    """Verifica el código TOTP y desactiva el 2FA."""
    if not user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El 2FA no está habilitado en tu cuenta.",
        )
    await service.disable(user.id, data.code)


@router.post("/verify", response_model=Token)
async def verify_2fa(
    data: Verify2FARequest,
    db: AsyncSession = Depends(get_db),
):
    """Recibe el pre_auth_token + código TOTP y emite los tokens definitivos."""
    try:
        user_id = decode_pre_auth_token(data.pre_auth_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido o expirado.",
        )

    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)

    service = TwoFactorService(user_repo=user_repo)
    if not await service.verify_code(user_id, data.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El código ingresado no es válido.",
        )

    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo.",
        )

    access_token = create_access_token(user.id, user.token_version)
    refresh_token = create_refresh_token(user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await token_repo.save(user.id, hash_token(refresh_token), expires_at)

    return Token(access_token=access_token, refresh_token=refresh_token)
