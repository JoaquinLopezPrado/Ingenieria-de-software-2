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
