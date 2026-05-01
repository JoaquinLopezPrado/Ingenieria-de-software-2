ME_RESPONSES = {
    200: {
        "description": "Datos del usuario autenticado.",
        "content": {
            "application/json": {
                "example": {"user_id": 1}
            }
        },
    },
    401: {
        "description": "No autenticado.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "No autenticado."}}
            }
        },
    },
}