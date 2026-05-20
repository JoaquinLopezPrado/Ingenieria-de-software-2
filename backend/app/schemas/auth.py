import re
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.domain.profile import Gender
from app.domain.user import AuthProvider


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    sub: int = None
    exp: int = None


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class RegisterClientRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    birth_date: date
    gender: Gender
    doc_type_name: str
    doc_number: str

    @field_validator("doc_type_name")
    @classmethod
    def validate_doc_type_name(cls, v: str) -> str:
        if v not in ("DNI", "PASAPORTE"):
            raise ValueError("El tipo de documento debe ser 'DNI' o 'PASAPORTE'.")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_age(cls, v: date) -> date:
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Debe ser mayor de edad para registrarse.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña no cumple con los requisitos mínimos de seguridad.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña no cumple con los requisitos mínimos de seguridad.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña no cumple con los requisitos mínimos de seguridad.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña no cumple con los requisitos mínimos de seguridad.")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("La contraseña no cumple con los requisitos mínimos de seguridad.")
        return v

    @model_validator(mode="after")
    def validate_document_number(self) -> "RegisterClientRequest":
        if self.doc_type_name == "DNI":
            if not self.doc_number.isdigit():
                raise ValueError("El número de DNI ingresado no es válido.")
        elif self.doc_type_name == "PASAPORTE":
            if not re.search(r"[A-Za-z]", self.doc_number) or not self.doc_number.isalnum():
                raise ValueError("El número de PASAPORTE ingresado no es válido.")
        return self


class GoogleCompleteRequest(BaseModel):
    """Completa el registro de un usuario que inició con Google y aún le faltan datos."""
    pending_token: str
    phone: str
    birth_date: date
    gender: Gender
    doc_type_name: str
    doc_number: str

    @field_validator("doc_type_name")
    @classmethod
    def validate_doc_type_name(cls, v: str) -> str:
        if v not in ("DNI", "PASAPORTE"):
            raise ValueError("El tipo de documento debe ser 'DNI' o 'PASAPORTE'.")
        return v

    @field_validator("birth_date")
    @classmethod
    def validate_age(cls, v: date) -> date:
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Debe ser mayor de edad para registrarse.")
        return v

    @model_validator(mode="after")
    def validate_document_number(self) -> "GoogleCompleteRequest":
        if self.doc_type_name == "DNI":
            if not self.doc_number.isdigit():
                raise ValueError("El número de DNI ingresado no es válido.")
        elif self.doc_type_name == "PASAPORTE":
            if not re.search(r"[A-Za-z]", self.doc_number) or not self.doc_number.isalnum():
                raise ValueError("El número de PASAPORTE ingresado no es válido.")
        return self
