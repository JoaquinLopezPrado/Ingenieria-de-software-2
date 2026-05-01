from typing import Any

_Responses = dict[int | str, dict[str, Any]]

ME_RESPONSES: _Responses = {
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