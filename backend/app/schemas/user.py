from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
import re

# Importamos las respuestas de los perfiles para anidarlas
from app.schemas.profile import ClientProfileResponse, EmployeeProfileResponse

class UserBase(BaseModel):
    email: EmailStr
    role_id: int

class UserCreate(UserBase):
    password: Optional[str] = None # Opcional por si entra con Google
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]):
        if v is None:
            return v
            
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula.')
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula.')
        if not re.search(r"[0-9]", v):
            raise ValueError('La contraseña debe contener al menos un número.')
            
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_2fa_enabled: bool
    
    # Anidamos los perfiles de forma opcional. 
    # SQLAlchemy y Pydantic se encargan de unirlos automáticamente.
    client_profile: Optional[ClientProfileResponse] = None
    employee_profile: Optional[EmployeeProfileResponse] = None
    
    model_config = ConfigDict(from_attributes=True)