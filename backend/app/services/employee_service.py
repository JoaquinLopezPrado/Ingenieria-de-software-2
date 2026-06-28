import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.repositories.password_reset_repository import AbstractPasswordResetRepository
from app.repositories.user_repository import AbstractUserRepository, EmpleadoRow
from app.services.email_service import EmailService
from app.utils.security import hash_password, hash_token

_WELCOME_TOKEN_TTL_HOURS = 24


class EmployeeService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        reset_repo: AbstractPasswordResetRepository,
    ):
        self._repo = user_repo
        self._reset_repo = reset_repo
        self._email_service = EmailService()

    async def list_employees(self) -> list[EmpleadoRow]:
        return await self._repo.list_employees()

    async def create_employee(
        self, email: str, first_name: str, last_name: str, phone: str | None
    ) -> EmpleadoRow:
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese email.",
            )

        placeholder_pw = hash_password(secrets.token_hex(32))
        employee = await self._repo.create_employee(
            email=email,
            hashed_password=placeholder_pw,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )

        await self._reset_repo.delete_by_user_id(employee.id)
        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=_WELCOME_TOKEN_TTL_HOURS)
        await self._reset_repo.save(employee.id, hash_token(raw_token), expires_at)

        set_password_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"
        self._email_service.send_employee_welcome(email, first_name, set_password_url)

        return employee

    async def update_employee(
        self, employee_id: int, first_name: str, last_name: str, phone: str | None
    ) -> EmpleadoRow:
        return await self._repo.update_employee(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )

    async def deactivate_employee(self, employee_id: int) -> None:
        await self._repo.deactivate_employee(employee_id)
