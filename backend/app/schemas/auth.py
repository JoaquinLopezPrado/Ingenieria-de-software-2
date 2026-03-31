from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginCredentials(BaseModel):
    email: str
    password: str

class TokenPayload(BaseModel):
    sub: int = None # El ID del usuario
    exp: int = None # Expiración

class Verify2FARequest(BaseModel):
    temp_token: str
    code: str