from typing import Any

_Responses = dict[int | str, dict[str, Any]]

LIST_ACTIVITIES_RESPONSES: _Responses = {
    200: {
        "description": "Listado de actividades activas.",
        "content": {
            "application/json": {
                "example": [
                    {"id": 1, "name": "yoga", "instructor": "Ana García", "is_active": True},
                    {"id": 2, "name": "pilates", "instructor": "Carlos López", "is_active": True},
                ]
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

CREATE_ACTIVITY_RESPONSES: _Responses = {
    201: {
        "description": "Actividad creada exitosamente.",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "name": "yoga",
                    "instructor": "Ana García",
                    "is_active": True,
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
    403: {
        "description": "Sin permisos de administrador.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "No tenés permisos para realizar esta acción."}}
            }
        },
    },
    409: {
        "description": "Ya existe una actividad activa con ese nombre.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Ya existe una actividad activa con ese nombre."}}
            }
        },
    },
}
