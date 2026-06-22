import asyncio
import logging
from datetime import date

from app.core.database import AsyncSessionLocal
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.waitlist_repository import WaitlistRepository
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService
from app.services.waitlist_service import WaitlistService

logger = logging.getLogger(__name__)


async def _cancel_expired_enrollments() -> None:
    freed_turno_ids: list[int] = []
    async with AsyncSessionLocal() as session:
        async with session.begin():
            sub_repo = SubscriptionRepository(session)
            await SingleEnrollmentRepository(session).cancel_expired()
            freed_from_expired = await sub_repo.cancel_expired()
            freed_from_scheduled = await sub_repo.effectivize_scheduled_cancellations()
            freed_turno_ids = freed_from_expired + freed_from_scheduled
            total = len(freed_from_expired) + len(freed_from_scheduled)
            if total:
                logger.info(
                    "Vencidas: %d susc pendientes, %d bajas programadas efectivizadas",
                    len(freed_from_expired), len(freed_from_scheduled),
                )

    await promote_freed_turnos(freed_turno_ids)


async def promote_freed_turnos(turno_ids: list[int]) -> None:
    """Intenta promover la lista de espera para cada turno que liberó un cupo."""
    for turno_id in set(turno_ids):
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    sub_service = SubscriptionService(SubscriptionRepository(session))
                    waitlist_service = WaitlistService(
                        waitlist_repo=WaitlistRepository(session),
                        subscription_service=sub_service,
                        email_service=EmailService(),
                    )
                    promoted = await waitlist_service.promote_next(turno_id)
                    if promoted:
                        logger.info("Waitlist: cupo liberado en turno %d → siguiente promovido", turno_id)
        except Exception:
            logger.exception("Error al promover lista de espera para turno %d", turno_id)


async def enrollment_expiry_loop(interval_seconds: int) -> None:
    while True:
        try:
            await _cancel_expired_enrollments()
        except Exception:
            logger.exception("Error al cancelar inscripciones vencidas")
        await asyncio.sleep(interval_seconds)


async def _generate_monthly_charges() -> None:
    today = date.today()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            service = SubscriptionService(SubscriptionRepository(session))
            created = await service.generate_charges_for_period(today.month, today.year)
            if created:
                logger.info("Cargos mensuales generados: %d", created)


async def monthly_charges_loop(interval_seconds: int) -> None:
    """Cron de respaldo: genera los cargos del mes vigente para abonados activos."""
    while True:
        try:
            await _generate_monthly_charges()
        except Exception:
            logger.exception("Error al generar cargos mensuales")
        await asyncio.sleep(interval_seconds)
