import enum
from datetime import time
from typing import List


class DiaSemana(str, enum.Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"


class Turno:
    def __init__(
        self,
        id: int,
        activity_id: int,
        name: str,
        time: time,
        capacity: int,
        month: int,
        year: int,
        is_active: bool,
        days: List[DiaSemana],
    ):
        self.id = id
        self.activity_id = activity_id
        self.name = name
        self.time = time
        self.capacity = capacity
        self.month = month
        self.year = year
        self.is_active = is_active
        self.days = days
