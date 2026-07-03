from pydantic import BaseModel, EmailStr, field_validator


class EmployeeListItem(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CreateEmployeeRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not v.isdigit():
            raise ValueError("El teléfono debe contener solo números.")
        return v


class UpdateEmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not v.isdigit():
            raise ValueError("El teléfono debe contener solo números.")
        return v
