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
                            "month": 5,
                            "year": 2026,
                            "is_active": True,
                            "days": ["lunes", "miercoles", "viernes"],
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
        "description": "Ya existe un turno con esa descripción para esa actividad en ese mes.",
        "content": {
            "application/json": {
                "example": {"errors": {"general": "Ya existe un turno con esa descripción para esa actividad en ese mes."}}
            }
        },
    },
}
