from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

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
    has_local_password: bool = False
    is_2fa_enabled: bool = False
    client_profile: Optional[ClientProfileMeResponse] = None
    employee_profile: Optional[EmployeeProfileMeResponse] = None


class ClienteListItem(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str
    doc_type_name: str
    doc_number: str
    is_active: bool = True


class PagoItem(BaseModel):
    tipo: Literal["suscripcion", "clase_individual"]
    fecha: Optional[date]
    actividad: str
    monto: float
    estado: str
    periodo: Optional[str] = None


class UpdateClientPhoneRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("El teléfono debe contener solo números.")
        return v


class ClientesPaginadosResponse(BaseModel):
    items: List[ClienteListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
