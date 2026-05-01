from typing import Any

_Responses = dict[int | str, dict[str, Any]]

ME_RESPONSES: _Responses = {
    200: {
        "description": "Perfil del usuario autenticado.",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "email": "pedro@mail.com",
                    "role": "cliente",
                    "client_profile": {
                        "id": 1,
                        "first_name": "Pedro",
                        "last_name": "García",
                        "phone": "1123456789",
                        "birth_date": "1990-05-15",
                        "document_type": {"id": 1, "name": "DNI"},
                        "doc_number": "12345678",
                        "gender": "masculino",
                    },
                    "employee_profile": None,
                }
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