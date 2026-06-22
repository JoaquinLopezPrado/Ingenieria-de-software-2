import enum
from datetime import datetime, time
from typing import List


class WaitlistStatus(str, enum.Enum):
    WAITING = "waiting"
    PROMOTED = "promoted"
    CANCELLED = "cancelled"


class WaitlistEntry:
    def __init__(
        self,
        id: int,
        user_id: int,
        turno_id: int,
        status: WaitlistStatus,
        joined_at: datetime,
        promoted_at: datetime | None = None,
        cancelled_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.turno_id = turno_id
        self.status = status
        self.joined_at = joined_at
        self.promoted_at = promoted_at
        self.cancelled_at = cancelled_at


class MyWaitlistEntry:
    """Vista enriquecida de la entrada en lista de espera con datos del turno."""

    def __init__(
        self,
        entry_id: int,
        turno_id: int,
        turno_description: str,
        activity_name: str,
        instructor: str,
        start_time: time,
        end_time: time,
        days: List[str],
        joined_at: datetime,
        status: WaitlistStatus,
    ):
        self.entry_id = entry_id
        self.turno_id = turno_id
        self.turno_description = turno_description
        self.activity_name = activity_name
        self.instructor = instructor
        self.start_time = start_time
        self.end_time = end_time
        self.days = days
        self.joined_at = joined_at
        self.status = status
