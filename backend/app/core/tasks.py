import asyncio
import logging
from datetime import date

from app.core.database import AsyncSessionLocal
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


async def _cancel_expired_enrollments() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            sub_repo = SubscriptionRepository(session)
            single_cancelled = await SingleEnrollmentRepository(session).cancel_expired()
            sub_cancelled = await sub_repo.cancel_expired()
            scheduled = await sub_repo.effectivize_scheduled_cancellations()
            total = single_cancelled + sub_cancelled + scheduled
            if total:
                logger.info(
                    "Vencidas: %d sueltas, %d susc pendientes, %d bajas programadas efectivizadas",
                    single_cancelled, sub_cancelled, scheduled,
                )


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
