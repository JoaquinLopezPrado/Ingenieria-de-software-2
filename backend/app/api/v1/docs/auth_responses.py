LOGIN_RESPONSES = {
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
                "example": {"errors": {"email": "value is not a valid email address"}}
            }
        },
    },
}

REGISTER_RESPONSES = {
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
