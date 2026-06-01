from typing import Any

_Responses = dict[int | str, dict[str, Any]]

LIST_TURNOS_RESPONSES: _Responses = {
    200: {
        "description": "Lista paginada de turnos.",
        "content": {
            "application/json": {
                "example": {
                    "items": [
                        {
                            "id": 1,
                            "activity_id": 1,
                            "description": "Turno mañana avanzado",
                            "start_time": "9:00",
                            "end_time": "10:30",
                            "capacity": 20,
                            "class_price": "3500.00",
                            "is_active": True,
                            "days": ["lunes", "miercoles", "viernes"],
                            "enrolled": 5,
                            "has_remaining_classes": True,
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "page_size": 20,
                    "pages": 1,
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

CREATE_TURNO_RESPONSES: _Responses = {
    201: {
        "description": "Turno creado exitosamente.",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "activity_id": 1,
                    "description": "Turno mañana avanzado",
                    "start_time": "9:00",
                    "end_time": "10:30",
                    "capacity": 20,
                    "class_price": "3500.00",
                    "is_active": True,
                    "days": ["lunes", "miercoles", "viernes"],
                    "enrolled": 0,
                    "has_remaining_classes": True,
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
        "description": "Ya existe un turno activo con esa actividad, descripción y horario.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Ya existe un turno activo con esa actividad, descripción y horario."}}
            }
        },
    },
}
