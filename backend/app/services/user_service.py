from fastapi import HTTPException, status

from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.user_repository import AbstractUserRepository
from app.schemas.user import (
    ClientProfileMeResponse,
    DocumentTypeResponse,
    EmployeeProfileMeResponse,
    UserMeResponse,
)


class UserService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        profile_repo: AbstractProfileRepository,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo

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
            client_profile=client_profile,
            employee_profile=employee_profile,
        )