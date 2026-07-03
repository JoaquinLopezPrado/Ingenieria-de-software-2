from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.user import AuthProvider, ClientProfile, Role, User
from app.models.auth import Role as RoleORM, User as UserORM
from app.models.profile import ClientProfile as ClientProfileORM, DocumentType as DocumentTypeORM, EmployeeProfile as EmployeeProfileORM


@dataclass
class ClienteRow:
    id: int          # user_id
    email: str
    first_name: str
    last_name: str
    phone: str
    doc_type_name: str
    doc_number: str
    is_active: bool


@dataclass
class EmpleadoRow:
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None
    is_active: bool


class AbstractUserRepository(ABC):

    @abstractmethod
    async def list_clients(
        self, q: Optional[str], page: int, page_size: int
    ) -> Tuple[List[ClientProfile], int]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: UserORM) -> User:
        raise NotImplementedError

    @abstractmethod
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def link_google(self, user_id: int, google_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unlink_google(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def increment_token_version(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_totp(self, user_id: int, secret: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disable_2fa(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_password(self, user_id: int, hashed_password: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_employees(self) -> list["EmpleadoRow"]:
        raise NotImplementedError

    @abstractmethod
    async def create_employee(
        self, email: str, hashed_password: str, first_name: str, last_name: str, phone: str | None
    ) -> "EmpleadoRow":
        raise NotImplementedError

    @abstractmethod
    async def update_employee(
        self, employee_id: int, first_name: str, last_name: str, phone: str | None
    ) -> "EmpleadoRow":
        raise NotImplementedError

    @abstractmethod
    async def deactivate_employee(self, employee_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reactivate_employee(self, employee_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate_client(self, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reactivate_client(self, user_id: int) -> None:
        raise NotImplementedError


class UserRepository(AbstractUserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_clients(
        self, q: Optional[str], page: int, page_size: int
    ) -> Tuple[List[ClienteRow], int]:
        base_query = (
            select(UserORM, ClientProfileORM, DocumentTypeORM)
            .join(ClientProfileORM, ClientProfileORM.user_id == UserORM.id)
            .join(DocumentTypeORM, DocumentTypeORM.id == ClientProfileORM.doc_type_id)
        )
        if q:
            term = f"%{q.lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(ClientProfileORM.first_name).like(term),
                    func.lower(ClientProfileORM.last_name).like(term),
                    func.lower(ClientProfileORM.doc_number).like(term),
                )
            )

        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        rows_result = await self._session.execute(
            base_query
            .order_by(ClientProfileORM.last_name, ClientProfileORM.first_name)
            .offset(offset)
            .limit(page_size)
        )
        rows = rows_result.all()
        items = [
            ClienteRow(
                id=user.id,
                email=user.email,
                first_name=profile.first_name,
                last_name=profile.last_name,
                phone=profile.phone,
                doc_type_name=doc_type.name,
                doc_number=profile.doc_number,
                is_active=user.is_active,
            )
            for user, profile, doc_type in rows
        ]
        return items, total

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(selectinload(UserORM.role), selectinload(UserORM.client_profile))
            .where(UserORM.id == user_id)
        )
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(selectinload(UserORM.role), selectinload(UserORM.client_profile))
            .where(UserORM.email == email)
        )
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user else None

    async def save(self, user: UserORM) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user, ["role", "client_profile"])
        return self._to_domain(user)

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(selectinload(UserORM.role), selectinload(UserORM.client_profile))
            .where(UserORM.google_id == google_id)
        )
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user else None

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        result = await self._session.execute(
            select(RoleORM).where(RoleORM.name == name)
        )
        orm_role = result.scalar_one_or_none()
        return self._role_to_domain(orm_role) if orm_role else None

    async def link_google(self, user_id: int, google_id: str) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(google_id=google_id)
        )

    async def unlink_google(self, user_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(google_id=None)
        )

    async def increment_token_version(self, user_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(token_version=UserORM.token_version + 1)
        )

    async def update_totp(self, user_id: int, secret: str) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(totp_secret=secret, is_2fa_enabled=True)
        )

    async def disable_2fa(self, user_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(totp_secret=None, is_2fa_enabled=False)
        )

    async def update_password(self, user_id: int, hashed_password: str) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(hashed_password=hashed_password)
        )

    def _to_domain(self, orm_user: UserORM) -> User:
        return User(
            id=orm_user.id,
            email=orm_user.email,
            role=self._role_to_domain(orm_user.role),
            auth_provider=AuthProvider(orm_user.auth_provider),
            is_active=orm_user.is_active,
            is_2fa_enabled=orm_user.is_2fa_enabled,
            token_version=orm_user.token_version,
            hashed_password=orm_user.hashed_password,
            google_id=orm_user.google_id,
            totp_secret=orm_user.totp_secret,
            client_profile=self._profile_to_domain(orm_user.client_profile),
        )

    def _profile_to_domain(self, orm_profile: Optional[ClientProfileORM]) -> Optional[ClientProfile]:
        if orm_profile is None:
            return None
        return ClientProfile(
            first_name=orm_profile.first_name,
            last_name=orm_profile.last_name,
            phone=orm_profile.phone,
        )

    async def list_employees(self) -> list[EmpleadoRow]:
        empleado_role = await self._session.execute(
            select(RoleORM.id).where(RoleORM.name == "empleado")
        )
        role_id = empleado_role.scalar_one_or_none()
        if role_id is None:
            return []
        rows = (await self._session.execute(
            select(UserORM, EmployeeProfileORM)
            .outerjoin(EmployeeProfileORM, EmployeeProfileORM.user_id == UserORM.id)
            .where(UserORM.role_id == role_id)
            .order_by(EmployeeProfileORM.last_name, EmployeeProfileORM.first_name)
        )).all()
        return [
            EmpleadoRow(
                id=user.id,
                email=user.email,
                first_name=profile.first_name if profile else "",
                last_name=profile.last_name if profile else "",
                phone=profile.phone if profile else None,
                is_active=user.is_active,
            )
            for user, profile in rows
        ]

    async def create_employee(
        self, email: str, hashed_password: str, first_name: str, last_name: str, phone: str | None
    ) -> EmpleadoRow:
        empleado_role = await self._session.execute(
            select(RoleORM).where(RoleORM.name == "empleado")
        )
        role = empleado_role.scalar_one()
        user_orm = UserORM(
            email=email,
            role_id=role.id,
            auth_provider=AuthProvider.LOCAL,
            hashed_password=hashed_password,
            is_active=True,
            is_2fa_enabled=False,
        )
        self._session.add(user_orm)
        await self._session.flush()
        profile_orm = EmployeeProfileORM(
            user_id=user_orm.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        self._session.add(profile_orm)
        await self._session.flush()
        return EmpleadoRow(
            id=user_orm.id,
            email=user_orm.email,
            first_name=profile_orm.first_name,
            last_name=profile_orm.last_name,
            phone=profile_orm.phone,
            is_active=user_orm.is_active,
        )

    async def update_employee(
        self, employee_id: int, first_name: str, last_name: str, phone: str | None
    ) -> EmpleadoRow:
        await self._session.execute(
            update(EmployeeProfileORM)
            .where(EmployeeProfileORM.user_id == employee_id)
            .values(first_name=first_name, last_name=last_name, phone=phone)
        )
        user = (await self._session.execute(
            select(UserORM).where(UserORM.id == employee_id)
        )).scalar_one()
        profile = (await self._session.execute(
            select(EmployeeProfileORM).where(EmployeeProfileORM.user_id == employee_id)
        )).scalar_one()
        return EmpleadoRow(
            id=user.id,
            email=user.email,
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone=profile.phone,
            is_active=user.is_active,
        )

    async def deactivate_employee(self, employee_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == employee_id)
            .values(is_active=False)
        )

    async def reactivate_employee(self, employee_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == employee_id)
            .values(is_active=True)
        )

    async def deactivate_client(self, user_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(is_active=False, token_version=UserORM.token_version + 1)
        )

    async def reactivate_client(self, user_id: int) -> None:
        result = await self._session.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        orm_user = result.scalar_one_or_none()
        if orm_user:
            orm_user.is_active = True

    def _role_to_domain(self, orm_role: RoleORM) -> Role:
        return Role(
            id=orm_role.id,
            name=orm_role.name,
            description=orm_role.description,
        )
