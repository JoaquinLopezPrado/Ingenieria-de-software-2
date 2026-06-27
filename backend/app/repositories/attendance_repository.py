from abc import ABC, abstractmethod
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.attendance import AsistenciaRegistro, Attendance, AttendanceStatus, CheckinResult, MyAttendanceRecord
from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import OCCUPYING_SUBSCRIPTION_STATUSES
from app.repositories.capacity import subscription_covers
from app.models.activity import Activity as ActivityORM
from app.models.attendance import Attendance as AttendanceORM
from app.models.clase import Clase as ClaseORM
from app.models.profile import ClientProfile as ClientProfileORM
from app.models.single_enrollment import SingleEnrollment as SingleEnrollmentORM, SingleEnrollmentSlot as SingleSlotORM
from app.models.subscription import Subscription as SubscriptionORM
from app.models.turno import Turno as TurnoORM

_ACTIVE_SINGLE = [
    SingleEnrollmentStatus.PENDING,
    SingleEnrollmentStatus.CONFIRMED,
    SingleEnrollmentStatus.DEPOSIT_PAID,
]


class RosterEntry:
    def __init__(self, user_id: int, first_name: str, last_name: str, source: str, status: AttendanceStatus | None):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.source = source  # "subscription" | "single"
        self.status = status


class AbstractAttendanceRepository(ABC):

    @abstractmethod
    async def get_historial_by_user(self, user_id: int) -> list[AsistenciaRegistro]:
        raise NotImplementedError

    @abstractmethod
    async def mark(self, user_id: int, clase_id: int, status: AttendanceStatus) -> Attendance:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: int, clase_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_my_history(self, user_id: int, today: date) -> list[MyAttendanceRecord]:
        raise NotImplementedError

    @abstractmethod
    async def checkin(self, user_id: int, clase_id: int, today: date) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    async def checkin(self, user_id: int, clase_id: int, today: date) -> CheckinResult:
        raise NotImplementedError

    @abstractmethod
    async def get_roster(self, clase_id: int) -> list[RosterEntry]:
        raise NotImplementedError


class AttendanceRepository(AbstractAttendanceRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_historial_by_user(self, user_id: int) -> list[AsistenciaRegistro]:
        result = await self._session.execute(
            select(
                AttendanceORM.id,
                ActivityORM.name,
                ClaseORM.date,
                TurnoORM.start_time,
                TurnoORM.end_time,
                AttendanceORM.status,
            )
            .join(ClaseORM, ClaseORM.id == AttendanceORM.clase_id)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(AttendanceORM.user_id == user_id)
            .order_by(ClaseORM.date.desc())
        )
        return [
            AsistenciaRegistro(
                id=row[0],
                activity_name=row[1],
                clase_date=row[2],
                start_time=row[3],
                end_time=row[4],
                status=row[5],
            )
            for row in result.all()
        ]

    async def delete(self, user_id: int, clase_id: int) -> None:
        await self._session.execute(
            delete(AttendanceORM).where(
                AttendanceORM.user_id == user_id,
                AttendanceORM.clase_id == clase_id,
            )
        )

    async def mark(self, user_id: int, clase_id: int, status: AttendanceStatus) -> Attendance:
        clase = await self._session.get(ClaseORM, clase_id)
        if clase is None:
            raise HTTPException(status_code=404, detail="Clase no encontrada.")

        stmt = (
            pg_insert(AttendanceORM)
            .values(user_id=user_id, clase_id=clase_id, status=status)
            .on_conflict_do_update(
                index_elements=["user_id", "clase_id"],
                set_={"status": status},
            )
            .returning(AttendanceORM.id, AttendanceORM.marked_at)
        )
        row = (await self._session.execute(stmt)).one()
        return Attendance(id=row[0], user_id=user_id, clase_id=clase_id, status=status, marked_at=row[1])

    async def get_my_history(self, user_id: int, today: date) -> list[MyAttendanceRecord]:
        _COLS = (
            ClaseORM.id.label("clase_id"),
            ActivityORM.name.label("activity_name"),
            ClaseORM.date.label("clase_date"),
            TurnoORM.start_time,
            TurnoORM.end_time,
            AttendanceORM.status,
        )
        _ATT_JOIN = (
            AttendanceORM,
            (AttendanceORM.clase_id == ClaseORM.id) & (AttendanceORM.user_id == user_id),
        )

        sub_rows = (await self._session.execute(
            select(*_COLS)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .join(SubscriptionORM, SubscriptionORM.turno_id == TurnoORM.id)
            .outerjoin(*_ATT_JOIN)
            .where(
                SubscriptionORM.user_id == user_id,
                ClaseORM.date >= SubscriptionORM.start_date,
                or_(SubscriptionORM.ends_on.is_(None), ClaseORM.date <= SubscriptionORM.ends_on),
                ClaseORM.date <= today,
            )
            .distinct()
        )).all()

        single_rows = (await self._session.execute(
            select(*_COLS)
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .join(SingleSlotORM, SingleSlotORM.clase_id == ClaseORM.id)
            .join(SingleEnrollmentORM, SingleEnrollmentORM.id == SingleSlotORM.enrollment_id)
            .outerjoin(*_ATT_JOIN)
            .where(
                SingleEnrollmentORM.user_id == user_id,
                SingleEnrollmentORM.status.in_([
                    SingleEnrollmentStatus.CONFIRMED,
                    SingleEnrollmentStatus.DEPOSIT_PAID,
                ]),
                ClaseORM.date <= today,
            )
            .distinct()
        )).all()

        seen: dict[int, MyAttendanceRecord] = {}
        for clase_id, activity_name, clase_date, start_time, end_time, att_status in sub_rows:
            if clase_id not in seen:
                seen[clase_id] = MyAttendanceRecord(clase_id, activity_name, clase_date, start_time, end_time, att_status)
        for clase_id, activity_name, clase_date, start_time, end_time, att_status in single_rows:
            if clase_id not in seen:
                seen[clase_id] = MyAttendanceRecord(clase_id, activity_name, clase_date, start_time, end_time, att_status)

        return sorted(seen.values(), key=lambda r: r.clase_date, reverse=True)

    async def checkin(self, user_id: int, clase_id: int, today: date) -> CheckinResult:
        clase_row = (await self._session.execute(
            select(
                ClaseORM.date,
                ActivityORM.name,
                TurnoORM.start_time,
                TurnoORM.end_time,
            )
            .join(TurnoORM, TurnoORM.id == ClaseORM.turno_id)
            .join(ActivityORM, ActivityORM.id == TurnoORM.activity_id)
            .where(ClaseORM.id == clase_id)
        )).one_or_none()

        if clase_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada.")

        clase_date, activity_name, start_time, end_time = clase_row
        if clase_date != today:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La clase no corresponde al día de hoy.")

        profile_row = (await self._session.execute(
            select(ClientProfileORM.first_name, ClientProfileORM.last_name)
            .where(ClientProfileORM.user_id == user_id)
        )).one_or_none()

        if profile_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

        first_name, last_name = profile_row

        existing = (await self._session.execute(
            select(AttendanceORM.status)
            .where(AttendanceORM.user_id == user_id, AttendanceORM.clase_id == clase_id)
        )).scalar_one_or_none()

        already_present = existing == AttendanceStatus.PRESENTE

        if not already_present:
            stmt = (
                pg_insert(AttendanceORM)
                .values(user_id=user_id, clase_id=clase_id, status=AttendanceStatus.PRESENTE)
                .on_conflict_do_update(
                    index_elements=["user_id", "clase_id"],
                    set_={"status": AttendanceStatus.PRESENTE},
                )
            )
            await self._session.execute(stmt)

        horario = f"{start_time.hour:02d}:{start_time.minute:02d} – {end_time.hour:02d}:{end_time.minute:02d}"
        return CheckinResult(
            first_name=first_name,
            last_name=last_name,
            activity_name=activity_name,
            horario=horario,
            already_present=already_present,
        )

    async def get_roster(self, clase_id: int) -> list[RosterEntry]:
        clase = await self._session.get(ClaseORM, clase_id)
        if clase is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clase no encontrada.")

        # Asistencias ya marcadas para esta clase.
        marked = {
            row[0]: row[1]
            for row in (await self._session.execute(
                select(AttendanceORM.user_id, AttendanceORM.status).where(AttendanceORM.clase_id == clase_id)
            )).all()
        }

        # Abonados cuya suscripción cubre la fecha de esta clase.
        sub_rows = (await self._session.execute(
            select(SubscriptionORM.user_id, ClientProfileORM.first_name, ClientProfileORM.last_name)
            .join(ClientProfileORM, ClientProfileORM.user_id == SubscriptionORM.user_id)
            .where(
                SubscriptionORM.turno_id == clase.turno_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                *subscription_covers(clase.date),
            )
        )).all()

        # Inscriptos sueltos a esta clase.
        single_rows = (await self._session.execute(
            select(SingleEnrollmentORM.user_id, ClientProfileORM.first_name, ClientProfileORM.last_name)
            .join(SingleSlotORM, SingleSlotORM.enrollment_id == SingleEnrollmentORM.id)
            .join(ClientProfileORM, ClientProfileORM.user_id == SingleEnrollmentORM.user_id)
            .where(
                SingleSlotORM.clase_id == clase_id,
                SingleEnrollmentORM.status.in_(_ACTIVE_SINGLE),
            )
        )).all()

        roster: dict[int, RosterEntry] = {}
        for uid, fn, ln in sub_rows:
            roster[uid] = RosterEntry(uid, fn, ln, "subscription", marked.get(uid))
        for uid, fn, ln in single_rows:
            if uid not in roster:
                roster[uid] = RosterEntry(uid, fn, ln, "single", marked.get(uid))
        return list(roster.values())
