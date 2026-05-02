from typing import Any

_Responses = dict[int | str, dict[str, Any]]

REFRESH_RESPONSES: _Responses = {
    200: {
        "description": "Tokens renovados exitosamente.",
        "content": {
            "application/json": {
                "example": {
                    "access_token": "<jwt>",
                    "refresh_token": "<jwt>",
                    "token_type": "bearer",
                }
            }
        },
    },
    401: {
        "description": "Refresh token inválido o expirado.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Token de refresco inválido o expirado."}}
            }
        },
    },
}

LOGIN_RESPONSES: _Responses = {
    200: {
        "description": "Inicio de sesión exitoso.",
        "content": {
            "application/json": {
                "example": {
                    "access_token": "<jwt>",
                    "refresh_token": "<jwt>",
                    "token_type": "bearer",
                }
            }
        },
    },
    401: {
        "description": "Credenciales incorrectas.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "El email o la contraseña ingresados son incorrectos."}}
            }
        },
    },
    422: {
        "description": "Error de validación.",
        "content": {
            "application/json": {
                "example": {"errors": {"email": "el formato del email es inválido."}}
            }
        },
    },
}

LOGOUT_RESPONSES: _Responses = {
    200: {
        "description": "Sesión cerrada exitosamente.",
        "content": {
            "application/json": {
                "example": {"message": "Sesión cerrada exitosamente."}
            }
        },
    },
    401: {
        "description": "No autenticado o token inválido.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "No autenticado."}}
            }
        },
    },
}

REGISTER_RESPONSES: _Responses = {
    201: {
        "description": "Cliente registrado exitosamente.",
        "content": {
            "application/json": {
                "example": {"message": "Registro exitoso."}
            }
        },
    },
    409: {
        "description": "Email o documento ya registrado.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "El email ingresado ya se encuentra registrado."}}
            }
        },
    },
    422: {
        "description": "Error de validación.",
        "content": {
            "application/json": {
                "example": {
                    "errors": {
                        "password": "La contraseña no cumple con los requisitos mínimos de seguridad.",
                        "birth_date": "Debe ser mayor de edad para registrarse.",
                    }
                }
            }
        },
    },
}
