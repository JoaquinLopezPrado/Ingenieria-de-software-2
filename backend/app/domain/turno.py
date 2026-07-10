import enum
from datetime import time
from decimal import Decimal
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
        description: str,
        instructor: str,
        start_time: time,
        end_time: time,
        capacity: int,
        class_price: Decimal,
        is_active: bool,
        days: List[DiaSemana],
        salon_id: "int | None" = None,
        salon_name: "str | None" = None,
        enrolled: int = 0,
        has_remaining_classes: bool = True,
        has_future_classes: bool = True,
    ):
        self.id = id
        self.activity_id = activity_id
        self.salon_id = salon_id
        self.salon_name = salon_name
        self.description = description
        self.instructor = instructor
        self.start_time = start_time
        self.end_time = end_time
        self.capacity = capacity
        self.class_price = class_price
        self.is_active = is_active
        self.days = days
        self.enrolled = enrolled
        self.has_remaining_classes = has_remaining_classes
        self.has_future_classes = has_future_classes
