from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.profile import ClientProfileResponse, EmployeeProfileResponse


class UserBase(BaseModel):
    email: EmailStr
    role_id: int


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_2fa_enabled: bool

    client_profile: Optional[ClientProfileResponse] = None
    employee_profile: Optional[EmployeeProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentTypeResponse(BaseModel):
    id: int
    name: str


class ClientProfileMeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    birth_date: date
    document_type: DocumentTypeResponse
    doc_number: str
    gender: str


class EmployeeProfileMeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    internal_file_number: Optional[str] = None


class UserMeResponse(BaseModel):
    id: int
    email: str
    role: str
    has_google_linked: bool = False
    client_profile: Optional[ClientProfileMeResponse] = None
    employee_profile: Optional[EmployeeProfileMeResponse] = None
