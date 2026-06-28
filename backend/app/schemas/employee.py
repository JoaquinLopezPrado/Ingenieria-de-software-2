from pydantic import BaseModel, EmailStr


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


class UpdateEmployeeRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str | None = None
