import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.repositories.enrollment_repository import EnrollmentRepository

logger = logging.getLogger(__name__)


async def _cancel_expired_enrollments() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            repo = EnrollmentRepository(session)
            cancelled = await repo.cancel_expired()
            if cancelled:
                logger.info("Inscripciones vencidas canceladas: %d", cancelled)


async def enrollment_expiry_loop(interval_seconds: int) -> None:
    while True:
        try:
            await _cancel_expired_enrollments()
        except Exception:
            logger.exception("Error al cancelar inscripciones vencidas")
        await asyncio.sleep(interval_seconds)
