from fastapi import HTTPException, status

from app.domain.user import AuthProvider, User
from app.models.auth import User as UserORM
from app.models.profile import ClientProfile as ClientProfileORM
from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.user_repository import AbstractUserRepository
from app.schemas.auth import LoginCredentials, RegisterClientRequest
from app.utils.security import hash_password, verify_password


class AuthService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        profile_repo: AbstractProfileRepository,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo

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

        return user

    async def login(self, data: LoginCredentials) -> User:
        user = await self._user_repo.get_by_email(data.email)
        if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El email o la contraseña ingresados son incorrectos.",
            )
        return user

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
