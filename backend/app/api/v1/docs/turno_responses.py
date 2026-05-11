from typing import Any

_Responses = dict[int | str, dict[str, Any]]

CREATE_TURNO_RESPONSES: _Responses = {
    201: {
        "description": "Turno creado exitosamente.",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "activity_id": 1,
                    "name": "Grupo A",
                    "time": "09:00:00",
                    "capacity": 20,
                    "month": 5,
                    "year": 2026,
                    "is_active": True,
                    "days": ["lunes", "miercoles", "viernes"],
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
    404: {
        "description": "Actividad no encontrada.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Actividad no encontrada."}}
            }
        },
    },
    409: {
        "description": "Ya existe un turno con ese nombre para esa actividad en ese mes.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Ya existe un turno con ese nombre para esa actividad en ese mes."}}
            }
        },
    },
}
