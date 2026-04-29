from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

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
