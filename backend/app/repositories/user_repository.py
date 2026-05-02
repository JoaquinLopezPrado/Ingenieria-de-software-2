from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.user import AuthProvider, Role, User
from app.models.auth import Role as RoleORM, User as UserORM


class AbstractUserRepository(ABC):

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
    async def increment_token_version(self, user_id: int) -> None:
        raise NotImplementedError


class UserRepository(AbstractUserRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(selectinload(UserORM.role))
            .where(UserORM.id == user_id)
        )
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM)
            .options(selectinload(UserORM.role))
            .where(UserORM.email == email)
        )
        orm_user = result.scalar_one_or_none()
        return self._to_domain(orm_user) if orm_user else None

    async def save(self, user: UserORM) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user, ["role"])
        return self._to_domain(user)

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        result = await self._session.execute(
            select(RoleORM).where(RoleORM.name == name)
        )
        orm_role = result.scalar_one_or_none()
        return self._role_to_domain(orm_role) if orm_role else None

    async def increment_token_version(self, user_id: int) -> None:
        await self._session.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(token_version=UserORM.token_version + 1)
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
        )

    def _role_to_domain(self, orm_role: RoleORM) -> Role:
        return Role(
            id=orm_role.id,
            name=orm_role.name,
            description=orm_role.description,
        )
