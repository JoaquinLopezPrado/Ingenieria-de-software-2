from datetime import date, time


class Clase:
    def __init__(self, id: int, turno_id: int, date: date, capacity: int, is_active: bool):
        self.id = id
        self.turno_id = turno_id
        self.date = date
        self.capacity = capacity
        self.is_active = is_active


class ClaseDetalle:
    def __init__(
        self,
        id: int,
        turno_id: int,
        date: date,
        start_time: time,
        end_time: time,
        capacity: int,
        enrolled: int,
        is_active: bool,
    ):
        self.id = id
        self.turno_id = turno_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.capacity = capacity
        self.enrolled = enrolled
        self.is_active = is_active
