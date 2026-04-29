from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.profile import ClientProfile, DocumentType, EmployeeProfile
from app.models.profile import ClientProfile as ClientProfileORM
from app.models.profile import DocumentType as DocumentTypeORM
from app.models.profile import EmployeeProfile as EmployeeProfileORM


class AbstractProfileRepository(ABC):

    @abstractmethod
    async def get_client_by_user_id(self, user_id: int) -> Optional[ClientProfile]:
        raise NotImplementedError

    @abstractmethod
    async def get_employee_by_user_id(self, user_id: int) -> Optional[EmployeeProfile]:
        raise NotImplementedError

    @abstractmethod
    async def get_document_type_by_id(self, doc_type_id: int) -> Optional[DocumentType]:
        raise NotImplementedError

    @abstractmethod
    async def save_client(self, profile: ClientProfileORM) -> ClientProfile:
        raise NotImplementedError

    @abstractmethod
    async def save_employee(self, profile: EmployeeProfileORM) -> EmployeeProfile:
        raise NotImplementedError


class ProfileRepository(AbstractProfileRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_client_by_user_id(self, user_id: int) -> Optional[ClientProfile]:
        result = await self._session.execute(
            select(ClientProfileORM)
            .options(selectinload(ClientProfileORM.document_type))
            .where(ClientProfileORM.user_id == user_id)
        )
        orm_profile = result.scalar_one_or_none()
        return self._client_to_domain(orm_profile) if orm_profile else None

    async def get_employee_by_user_id(self, user_id: int) -> Optional[EmployeeProfile]:
        result = await self._session.execute(
            select(EmployeeProfileORM).where(EmployeeProfileORM.user_id == user_id)
        )
        orm_profile = result.scalar_one_or_none()
        return self._employee_to_domain(orm_profile) if orm_profile else None

    async def get_document_type_by_id(self, doc_type_id: int) -> Optional[DocumentType]:
        result = await self._session.execute(
            select(DocumentTypeORM).where(DocumentTypeORM.id == doc_type_id)
        )
        orm_doc_type = result.scalar_one_or_none()
        return self._document_type_to_domain(orm_doc_type) if orm_doc_type else None

    async def save_client(self, profile: ClientProfileORM) -> ClientProfile:
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile, ["document_type"])
        return self._client_to_domain(profile)

    async def save_employee(self, profile: EmployeeProfileORM) -> EmployeeProfile:
        self._session.add(profile)
        await self._session.flush()
        return self._employee_to_domain(profile)

    def _client_to_domain(self, orm_profile: ClientProfileORM) -> ClientProfile:
        return ClientProfile(
            id=orm_profile.id,
            user_id=orm_profile.user_id,
            first_name=orm_profile.first_name,
            last_name=orm_profile.last_name,
            phone=orm_profile.phone,
            birth_date=orm_profile.birth_date,
            document_type=self._document_type_to_domain(orm_profile.document_type),
            doc_number=orm_profile.doc_number,
        )

    def _employee_to_domain(self, orm_profile: EmployeeProfileORM) -> EmployeeProfile:
        return EmployeeProfile(
            id=orm_profile.id,
            user_id=orm_profile.user_id,
            first_name=orm_profile.first_name,
            last_name=orm_profile.last_name,
            internal_file_number=orm_profile.internal_file_number,
        )

    def _document_type_to_domain(self, orm_doc_type: DocumentTypeORM) -> DocumentType:
        return DocumentType(
            id=orm_doc_type.id,
            name=orm_doc_type.name,
        )
