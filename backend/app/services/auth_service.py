from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.user import AuthProvider, User
from app.models.auth import User as UserORM
from app.models.profile import ClientProfile as ClientProfileORM
from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.token_repository import AbstractTokenRepository
from app.repositories.user_repository import AbstractUserRepository
from app.schemas.auth import LoginCredentials, RefreshTokenRequest, RegisterClientRequest
from app.services.email_service import EmailService
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)


class AuthService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        profile_repo: AbstractProfileRepository,
        token_repo: AbstractTokenRepository,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo
        self._token_repo = token_repo
        self._email_service = EmailService()

    async def register_client(self, data: RegisterClientRequest) -> User:
        await self._ensure_email_is_unique(data.email)
        await self._ensure_doc_number_is_unique(data.doc_number)

        document_type = await self._profile_repo.get_document_type_by_name(data.doc_type_name)
        if not document_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tipo de documento '{data.doc_type_name}' no encontrado en el sistema.",
            )

        client_role = await self._user_repo.get_role_by_name("cliente")
        if not client_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El rol 'cliente' no está configurado en el sistema.",
            )

        user_orm = UserORM(
            email=data.email,
            role_id=client_role.id,
            auth_provider=AuthProvider.LOCAL,
            hashed_password=hash_password(data.password),
            is_active=True,
            is_2fa_enabled=False,
        )
        user = await self._user_repo.save(user_orm)

        profile_orm = ClientProfileORM(
            user_id=user.id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            birth_date=data.birth_date,
            doc_type_id=document_type.id,
            doc_number=data.doc_number,
            gender=data.gender,
        )
        await self._profile_repo.save_client(profile_orm)

        self._email_service.send_welcome(user.email, data.first_name)

        return user

    async def login(self, data: LoginCredentials) -> tuple[User, str, str]:
        user = await self._user_repo.get_by_email(data.email)
        if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El email o la contraseña ingresados son incorrectos.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El email o la contraseña ingresados son incorrectos.",
            )
        access_token = create_access_token(user.id, user.token_version)
        refresh_token = create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self._token_repo.save(user.id, hash_token(refresh_token), expires_at)
        return user, access_token, refresh_token

    async def refresh(self, data: RefreshTokenRequest) -> tuple[str, str]:
        try:
            user_id = decode_refresh_token(data.refresh_token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco inválido o expirado.",
            )
        deleted = await self._token_repo.delete_by_hash(hash_token(data.refresh_token))
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco inválido o expirado.",
            )
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de refresco inválido o expirado.",
            )
        new_access = create_access_token(user.id, user.token_version)
        new_refresh = create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self._token_repo.save(user.id, hash_token(new_refresh), expires_at)
        return new_access, new_refresh

    async def logout(self, user_id: int, refresh_token: str) -> None:
        await self._token_repo.delete_by_hash(hash_token(refresh_token))
        await self._user_repo.increment_token_version(user_id)

    async def _ensure_email_is_unique(self, email: str) -> None:
        if await self._user_repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ingresado ya se encuentra registrado.",
            )

    async def _ensure_doc_number_is_unique(self, doc_number: str) -> None:
        if await self._profile_repo.get_client_by_doc_number(doc_number):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El documento ingresado ya se encuentra registrado.",
            )
