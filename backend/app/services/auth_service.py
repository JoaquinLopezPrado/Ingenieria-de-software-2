from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.user import AuthProvider, User
from app.models.auth import User as UserORM
from app.models.profile import ClientProfile as ClientProfileORM
from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.token_repository import AbstractTokenRepository
from app.repositories.user_repository import AbstractUserRepository
from app.schemas.auth import GoogleCompleteRequest, LoginCredentials, RefreshTokenRequest, RegisterClientRequest
from app.services.email_service import EmailService
from app.utils.security import (
    create_access_token,
    create_google_pending_token,
    create_google_state_token,
    create_pre_auth_token,
    create_refresh_token,
    decode_google_pending_token,
    decode_google_state_token,
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

    async def login(self, data: LoginCredentials) -> dict:
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
        if user.is_2fa_enabled:
            return {"requires_2fa": True, "pre_auth_token": create_pre_auth_token(user.id)}
        access_token, refresh_token = await self._issue_tokens(user)
        return {"requires_2fa": False, "access_token": access_token, "refresh_token": refresh_token}

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
        return await self._issue_tokens(user)

    async def logout(self, user_id: int, refresh_token: str) -> None:
        await self._token_repo.delete_by_hash(hash_token(refresh_token))
        await self._user_repo.increment_token_version(user_id)

    # ------------------------------------------------------------------ #
    # Google OAuth                                                         #
    # ------------------------------------------------------------------ #

    def _build_google_url(self, state: str) -> str:
        params = urlencode({
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        })
        return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

    def get_google_oauth_url(self, mode: str = "login") -> str:
        return self._build_google_url(create_google_state_token(mode))

    def get_google_link_url(self, user_id: int) -> str:
        return self._build_google_url(create_google_state_token(mode="link", user_id=user_id))

    async def handle_google_callback(self, code: str, state: str) -> dict:
        state_data = decode_google_state_token(state)
        if state_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Estado OAuth inválido o expirado.",
            )
        mode = state_data["mode"]

        userinfo = await self._exchange_code_for_userinfo(code)
        google_id = userinfo["id"]
        email = userinfo.get("email", "")
        first_name = userinfo.get("given_name", "")
        last_name = userinfo.get("family_name", "")

        if mode == "link":
            return await self._link_google_account(state_data["user_id"], google_id)

        user = await self._user_repo.get_by_google_id(google_id)

        if user is None:
            existing = await self._user_repo.get_by_email(email)
            if existing is not None and existing.auth_provider == AuthProvider.LOCAL:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El email ya está registrado con una cuenta local. Ingresá con email y contraseña.",
                )

        if user is not None:
            if mode == "register":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="GOOGLE_ALREADY_LINKED",
                )
            access_token, refresh_token = await self._issue_tokens(user)
            return {"type": "login", "access_token": access_token, "refresh_token": refresh_token}

        pending_token = create_google_pending_token(google_id, email, first_name, last_name)
        return {
            "type": "new_user",
            "mode": mode,
            "pending_token": pending_token,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

    async def _link_google_account(self, user_id: int, google_id: str) -> dict:
        existing = await self._user_repo.get_by_google_id(google_id)
        if existing is not None and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta cuenta de Google ya está vinculada a otro usuario.",
            )

        current_user = await self._user_repo.get_by_id(user_id)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )
        if current_user.google_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tu cuenta ya tiene una cuenta de Google vinculada.",
            )

        await self._user_repo.link_google(user_id, google_id)
        return {"type": "linked"}

    async def unlink_google_account(self, user_id: int) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
        if user.google_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No tenés una cuenta de Google vinculada.")
        if user.hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No podés desvincular Google porque es tu único método de acceso a la cuenta.",
            )
        await self._user_repo.unlink_google(user_id)

    async def google_complete_registration(self, data: GoogleCompleteRequest) -> tuple[str, str]:
        try:
            google_data = decode_google_pending_token(data.pending_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de registro pendiente inválido o expirado.",
            )

        await self._ensure_email_is_unique(google_data["email"])
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
            email=google_data["email"],
            role_id=client_role.id,
            auth_provider=AuthProvider.GOOGLE,
            google_id=google_data["google_id"],
            is_active=True,
            is_2fa_enabled=False,
        )
        user = await self._user_repo.save(user_orm)

        profile_orm = ClientProfileORM(
            user_id=user.id,
            first_name=google_data["first_name"],
            last_name=google_data["last_name"],
            phone=data.phone,
            birth_date=data.birth_date,
            doc_type_id=document_type.id,
            doc_number=data.doc_number,
            gender=data.gender,
        )
        await self._profile_repo.save_client(profile_orm)

        self._email_service.send_welcome(user.email, google_data["first_name"])

        return await self._issue_tokens(user)

    async def _issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(user.id, user.token_version)
        refresh_token = create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self._token_repo.save(user.id, hash_token(refresh_token), expires_at)
        return access_token, refresh_token

    async def _exchange_code_for_userinfo(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error al intercambiar el código de autorización con Google.",
                )
            google_access_token = token_resp.json().get("access_token")

            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"},
            )
            if userinfo_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error al obtener la información del usuario de Google.",
                )
            return userinfo_resp.json()

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
