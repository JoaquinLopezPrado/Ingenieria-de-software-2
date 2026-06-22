from abc import ABC, abstractmethod
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.waitlist import MyWaitlistEntry, WaitlistEntry, WaitlistStatus
from app.models.auth import User as UserORM
from app.models.profile import ClientProfile as ClientProfileORM
from app.models.turno import Turno as TurnoORM
from app.models.waitlist import SubscriptionWaitlist as WaitlistORM
from app.domain.subscription import OCCUPYING_SUBSCRIPTION_STATUSES
from app.models.subscription import Subscription as SubscriptionORM


class AbstractWaitlistRepository(ABC):

    @abstractmethod
    async def join(self, turno_id: int, user_id: int) -> WaitlistEntry:
        raise NotImplementedError

    @abstractmethod
    async def leave(self, entry_id: int, user_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user(self, user_id: int) -> list[MyWaitlistEntry]:
        raise NotImplementedError

    @abstractmethod
    async def get_next_waiting(self, turno_id: int) -> WaitlistEntry | None:
        raise NotImplementedError

    @abstractmethod
    async def mark_promoted(self, entry_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_user_contact(self, user_id: int) -> tuple[str, str]:
        """Retorna (email, first_name) del usuario."""
        raise NotImplementedError

    @abstractmethod
    async def get_turno_info(self, turno_id: int) -> tuple[str, str]:
        """Retorna (activity_name, turno_description) del turno."""
        raise NotImplementedError


class WaitlistRepository(AbstractWaitlistRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def join(self, turno_id: int, user_id: int) -> WaitlistEntry:
        # Verificar que no tenga ya una suscripción activa.
        existing_sub = (await self._session.execute(
            select(SubscriptionORM).where(
                SubscriptionORM.turno_id == turno_id,
                SubscriptionORM.user_id == user_id,
                SubscriptionORM.status.in_(OCCUPYING_SUBSCRIPTION_STATUSES),
                SubscriptionORM.ends_on.is_(None),
            )
        )).scalar_one_or_none()
        if existing_sub is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya tenés una suscripción activa para este turno.",
            )

        # Verificar que no esté ya en la lista de espera.
        existing = (await self._session.execute(
            select(WaitlistORM).where(
                WaitlistORM.turno_id == turno_id,
                WaitlistORM.user_id == user_id,
                WaitlistORM.status == WaitlistStatus.WAITING,
            )
        )).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya estás en la lista de espera para este turno.",
            )

        now = datetime.now(timezone.utc)
        entry = WaitlistORM(
            user_id=user_id,
            turno_id=turno_id,
            status=WaitlistStatus.WAITING,
            joined_at=now,
        )
        self._session.add(entry)
        await self._session.flush()
        return self._to_domain(entry)

    async def leave(self, entry_id: int, user_id: int) -> None:
        result = await self._session.execute(
            update(WaitlistORM)
            .where(
                WaitlistORM.id == entry_id,
                WaitlistORM.user_id == user_id,
                WaitlistORM.status == WaitlistStatus.WAITING,
            )
            .values(status=WaitlistStatus.CANCELLED, cancelled_at=datetime.now(timezone.utc))
        )
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entrada en lista de espera no encontrada.",
            )

    async def get_by_user(self, user_id: int) -> list[MyWaitlistEntry]:
        result = await self._session.execute(
            select(WaitlistORM)
            .options(
                selectinload(WaitlistORM.turno).selectinload(TurnoORM.activity),
                selectinload(WaitlistORM.turno).selectinload(TurnoORM.days),
            )
            .where(
                WaitlistORM.user_id == user_id,
                WaitlistORM.status == WaitlistStatus.WAITING,
            )
            .order_by(WaitlistORM.joined_at.desc())
        )
        return [self._to_my_entry(e) for e in result.scalars()]

    async def get_next_waiting(self, turno_id: int) -> WaitlistEntry | None:
        result = await self._session.execute(
            select(WaitlistORM)
            .where(
                WaitlistORM.turno_id == turno_id,
                WaitlistORM.status == WaitlistStatus.WAITING,
            )
            .order_by(WaitlistORM.joined_at.asc())
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def mark_promoted(self, entry_id: int) -> None:
        await self._session.execute(
            update(WaitlistORM)
            .where(WaitlistORM.id == entry_id)
            .values(status=WaitlistStatus.PROMOTED, promoted_at=datetime.now(timezone.utc))
        )

    async def get_user_contact(self, user_id: int) -> tuple[str, str]:
        row = (await self._session.execute(
            select(UserORM.email, ClientProfileORM.first_name)
            .join(ClientProfileORM, ClientProfileORM.user_id == UserORM.id)
            .where(UserORM.id == user_id)
        )).one_or_none()
        if row is None:
            return ("", "")
        return (row[0], row[1])

    async def get_turno_info(self, turno_id: int) -> tuple[str, str]:
        from app.models.activity import Activity as ActivityORM
        row = (await self._session.execute(
            select(ActivityORM.name, TurnoORM.description)
            .join(TurnoORM, TurnoORM.activity_id == ActivityORM.id)
            .where(TurnoORM.id == turno_id)
        )).one_or_none()
        if row is None:
            return ("", "")
        return (row[0], row[1])

    @staticmethod
    def _to_domain(orm: WaitlistORM) -> WaitlistEntry:
        return WaitlistEntry(
            id=orm.id,
            user_id=orm.user_id,
            turno_id=orm.turno_id,
            status=orm.status,
            joined_at=orm.joined_at,
            promoted_at=orm.promoted_at,
            cancelled_at=orm.cancelled_at,
        )

    @staticmethod
    def _to_my_entry(orm: WaitlistORM) -> MyWaitlistEntry:
        return MyWaitlistEntry(
            entry_id=orm.id,
            turno_id=orm.turno.id,
            turno_description=orm.turno.description,
            activity_name=orm.turno.activity.name,
            instructor=orm.turno.instructor,
            start_time=orm.turno.start_time,
            end_time=orm.turno.end_time,
            days=[d.dia for d in orm.turno.days],
            joined_at=orm.joined_at,
            status=orm.status,
        )
