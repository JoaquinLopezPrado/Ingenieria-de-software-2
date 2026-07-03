from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date
from typing import Optional

# Clase Base con los campos comunes (evita repetir código)
class ClientProfileBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    birth_date: date
    doc_type_id: int
    doc_number: str

# Esquema para CREAR el perfil (Acá van las validaciones estrictas)
class ClientProfileCreate(ClientProfileBase):

    @field_validator('birth_date')
    @classmethod
    def check_age(cls, v: date):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))

        if age < 18:
            raise ValueError('El cliente debe ser mayor de 18 años para registrarse.')
        return v

    @field_validator('phone')
    @classmethod
    def check_phone(cls, v: str):
        if not v.isdigit():
            raise ValueError('El teléfono debe contener solo números.')
        return v

# Esquema para DEVOLVER el perfil (Acá habilitamos la lectura desde SQLAlchemy)
class ClientProfileResponse(ClientProfileBase):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Lo mismo para Empleados ---
class EmployeeProfileBase(BaseModel):
    first_name: str
    last_name: str
    internal_file_number: Optional[str] = None

class EmployeeProfileCreate(EmployeeProfileBase):
    pass

class EmployeeProfileResponse(EmployeeProfileBase):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)