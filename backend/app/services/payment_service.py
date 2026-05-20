import asyncio
from functools import partial

import mercadopago
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.enrollment import EnrollmentStatus
from app.repositories.enrollment_repository import AbstractEnrollmentRepository

_MP_STATUS_MAP = {
    "approved": EnrollmentStatus.CONFIRMED,
    "rejected": EnrollmentStatus.CANCELLED,
    "cancelled": EnrollmentStatus.CANCELLED,
}


class PaymentService:

    def __init__(self, enrollment_repo: AbstractEnrollmentRepository):
        self._enrollment_repo = enrollment_repo
        self._sdk = mercadopago.SDK(settings.mp_access_token)

    async def create_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)

        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")

        if details.status != EnrollmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La inscripción no está en estado pendiente.",
            )

        preference_data = {
            "items": [{
                "title": f"Inscripción a {details.activity_name} — {details.turno_description}",
                "quantity": 1,
                "unit_price": float(details.price),
                "currency_id": "ARS",
            }],
            "back_urls": {
                "success": f"{settings.mp_frontend_url}/payment/success?enrollment_id={enrollment_id}",
                "failure": f"{settings.mp_frontend_url}/payment/failure?enrollment_id={enrollment_id}",
                "pending": f"{settings.mp_frontend_url}/payment/pending?enrollment_id={enrollment_id}",
            },
            "external_reference": str(enrollment_id),
            # auto_return requiere URL pública; se activa solo en producción
            **({"auto_return": "approved"} if not settings.debug else {}),
            **({"expiration_date_to": details.expires_at.isoformat()} if details.expires_at else {}),
        }
        if settings.mp_notification_url:
            preference_data["notification_url"] = settings.mp_notification_url

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._sdk.preference().create, preference_data)
        )

        if response["status"] not in (200, 201):
            import logging
            logging.getLogger(__name__).error("MP preference error: %s", response)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"MP error {response['status']}: {response.get('response')}",
            )

        init_point = response["response"].get("init_point")
        return init_point

    async def handle_webhook(self, payment_id: str) -> None:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._sdk.payment().get, payment_id)
        )

        if response["status"] != 200:
            return

        payment = response["response"]
        mp_status = payment.get("status")
        external_reference = payment.get("external_reference")

        if not external_reference or not external_reference.isdigit():
            return

        enrollment_id = int(external_reference)
        new_status = _MP_STATUS_MAP.get(mp_status)

        if new_status is None:
            return

        await self._enrollment_repo.update_payment(
            enrollment_id=enrollment_id,
            new_status=new_status,
            payment_id=payment_id,
        )
