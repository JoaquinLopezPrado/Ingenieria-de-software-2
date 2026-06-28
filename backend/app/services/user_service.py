import math

from fastapi import HTTPException, status

from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.user_repository import AbstractUserRepository
from app.schemas.user import (
    ClienteListItem,
    ClientesPaginadosResponse,
    ClientProfileMeResponse,
    DocumentTypeResponse,
    EmployeeProfileMeResponse,
    UserMeResponse,
    UpdateClientPhoneRequest,
)


class UserService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        profile_repo: AbstractProfileRepository,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo

    async def list_clients(
        self,
        q: str | None,
        page: int,
        page_size: int,
    ) -> ClientesPaginadosResponse:
        items, total = await self._user_repo.list_clients(q=q, page=page, page_size=page_size)
        total_pages = max(1, math.ceil(total / page_size))
        return ClientesPaginadosResponse(
            items=[
                ClienteListItem(
                    id=row.id,
                    email=row.email,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    phone=row.phone,
                    doc_type_name=row.doc_type_name,
                    doc_number=row.doc_number,
                )
                for row in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_client_by_id(self, user_id: int) -> ClienteListItem:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado.")
        client = await self._profile_repo.get_client_by_user_id(user_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado.")
        return ClienteListItem(
            id=user.id,
            email=user.email,
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            doc_type_name=client.document_type.name,
            doc_number=client.doc_number,
        )

    async def update_my_phone(
        self,
        user_id: int,
        data: UpdateClientPhoneRequest,
    ) -> UserMeResponse:
        new_phone = data.phone.strip()

        if not new_phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El teléfono es obligatorio.",
            )

        client = await self._profile_repo.get_client_by_user_id(user_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de cliente no encontrado.",
            )

        await self._profile_repo.update_client_phone(user_id=user_id, phone=new_phone)

        return await self.get_me(user_id)

    async def get_me(self, user_id: int) -> UserMeResponse:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        client_profile = None
        employee_profile = None

        client = await self._profile_repo.get_client_by_user_id(user_id)
        if client:
            client_profile = ClientProfileMeResponse(
                id=client.id,
                first_name=client.first_name,
                last_name=client.last_name,
                phone=client.phone,
                birth_date=client.birth_date,
                document_type=DocumentTypeResponse(
                    id=client.document_type.id,
                    name=client.document_type.name,
                ),
                doc_number=client.doc_number,
                gender=client.gender.value,
            )
        else:
            employee = await self._profile_repo.get_employee_by_user_id(user_id)
            if employee:
                employee_profile = EmployeeProfileMeResponse(
                    id=employee.id,
                    first_name=employee.first_name,
                    last_name=employee.last_name,
                    internal_file_number=employee.internal_file_number,
                )

        return UserMeResponse(
            id=user.id,
            email=user.email,
            role=user.role.name,
            has_google_linked=user.google_id is not None,
            has_local_password=user.hashed_password is not None,
            is_2fa_enabled=user.is_2fa_enabled,
            client_profile=client_profile,
            employee_profile=employee_profile,
        )