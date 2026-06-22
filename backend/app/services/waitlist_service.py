import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.config import settings
from app.domain.waitlist import MyWaitlistEntry, WaitlistEntry
from app.repositories.waitlist_repository import AbstractWaitlistRepository
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class WaitlistService:

    def __init__(
        self,
        waitlist_repo: AbstractWaitlistRepository,
        subscription_service: SubscriptionService,
        email_service: EmailService,
    ):
        self._repo = waitlist_repo
        self._sub_service = subscription_service
        self._email_service = email_service

    async def join(self, turno_id: int, user_id: int) -> WaitlistEntry:
        return await self._repo.join(turno_id=turno_id, user_id=user_id)

    async def leave(self, entry_id: int, user_id: int) -> None:
        await self._repo.leave(entry_id=entry_id, user_id=user_id)

    async def get_by_user(self, user_id: int) -> list[MyWaitlistEntry]:
        return await self._repo.get_by_user(user_id=user_id)

    async def promote_next(self, turno_id: int) -> bool:
        """Intenta promover al siguiente en la lista de espera del turno.

        Retorna True si alguien fue promovido. Si no hay lista o no hay cupo disponible
        devuelve False sin lanzar excepción.
        """
        entry = await self._repo.get_next_waiting(turno_id)
        if entry is None:
            return False

        waitlist_expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.waitlist_ttl_hours)
        try:
            charge = await self._sub_service.create(
                turno_id=turno_id,
                user_id=entry.user_id,
                expires_at_override=waitlist_expires_at,
            )
        except HTTPException as exc:
            # Sin cupo disponible u otro conflicto: no promover, dejar en lista.
            logger.info(
                "No se pudo promover waitlist entry %d para turno %d: %s",
                entry.id, turno_id, exc.detail,
            )
            return False

        await self._repo.mark_promoted(entry.id)

        email, first_name = await self._repo.get_user_contact(entry.user_id)
        activity_name, turno_description = await self._repo.get_turno_info(turno_id)

        ticket_url = f"{settings.frontend_url}/ticket?charge_id={charge.id}"
        if email:
            self._email_service.send_waitlist_promoted(
                to=email,
                first_name=first_name or "cliente",
                activity_name=activity_name,
                turno_description=turno_description,
                amount=charge.amount,
                ticket_url=ticket_url,
                ttl_hours=settings.waitlist_ttl_hours,
            )

        logger.info(
            "Waitlist: usuario %d promovido para turno %d (charge_id=%d)",
            entry.user_id, turno_id, charge.id,
        )
        return True
