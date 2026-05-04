from datetime import date


class Clase:
    def __init__(self, id: int, turno_id: int, date: date, capacity: int, is_active: bool):
        self.id = id
        self.turno_id = turno_id
        self.date = date
        self.capacity = capacity
        self.is_active = is_active
