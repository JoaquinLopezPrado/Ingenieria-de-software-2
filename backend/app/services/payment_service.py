import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial

import mercadopago
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.enrollment import EnrollmentStatus
from app.repositories.enrollment_repository import AbstractEnrollmentRepository
from app.repositories.payment_repository import AbstractPaymentRepository
from app.repositories.user_repository import AbstractUserRepository
from app.services.email_service import EmailService


_ART = timezone(timedelta(hours=-3))


def _mp_isoformat(dt) -> str:
    """Formatea datetime al formato que espera MP: 'YYYY-MM-DDTHH:MM:SS.000-03:00'.
    Si asyncpg devuelve naive (sin tzinfo) asumimos UTC antes de convertir a ART."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_ART).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")


_MP_STATUS_MAP = {
    "approved": EnrollmentStatus.CONFIRMED,
    "rejected": EnrollmentStatus.CANCELLED,
    "cancelled": EnrollmentStatus.CANCELLED,
}


class PaymentService:

    def __init__(
        self,
        enrollment_repo: AbstractEnrollmentRepository,
        user_repo: AbstractUserRepository,
        payment_repo: AbstractPaymentRepository,
    ):
        self._enrollment_repo = enrollment_repo
        self._user_repo = user_repo
        self._payment_repo = payment_repo
        self._email_service = EmailService()
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
            # auto_return requiere back_url con HTTPS público (ngrok o producción)
            **({"auto_return": "approved"} if settings.mp_frontend_url.startswith("https://") else {}),
            **({"date_of_expiration": _mp_isoformat(details.expires_at)} if details.expires_at else {}),
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

        updated = await self._enrollment_repo.update_payment(
            enrollment_id=enrollment_id,
            new_status=new_status,
            payment_id=payment_id,
        )

        if updated and new_status == EnrollmentStatus.CONFIRMED:
            details = await self._enrollment_repo.get_payment_details(enrollment_id)
            await self._payment_repo.create(
                enrollment_id=enrollment_id,
                amount=details.price,
                class_price_snapshot=details.class_price_snapshot,
                num_classes_snapshot=details.num_classes_snapshot,
                payment_provider_id=payment_id,
                confirmed_at=datetime.now(timezone.utc),
                activity_id=details.activity_id,
                activity_name_snapshot=details.activity_name,
                month_snapshot=details.month,
                year_snapshot=details.year,
                enrollment_type_snapshot=details.enrollment_type,
            )
            await self._send_payment_email(enrollment_id, payment_id)

    async def free_confirm(self, enrollment_id: int, user_id: int) -> None:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)

        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")

        if details.status != EnrollmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La inscripción no está en estado pendiente.",
            )

        if details.price != 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta inscripción requiere pago a través de Mercado Pago.",
            )

        await self._enrollment_repo.update_payment(
            enrollment_id=enrollment_id,
            new_status=EnrollmentStatus.CONFIRMED,
            payment_id="free",
        )

    async def get_mp_status_detail(self, payment_id: str) -> str | None:
        if not payment_id or payment_id == "0":
            return None
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._sdk.payment().get, payment_id)
        )
        if response["status"] != 200:
            return None
        return response["response"].get("status_detail")

    async def _send_payment_email(self, enrollment_id: int, payment_id: str) -> None:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)
        user = await self._user_repo.get_by_id(details.user_id)
        if not user or not user.client_profile:
            return
        self._email_service.send_enrollment_confirmed(
            to=user.email,
            first_name=user.client_profile.first_name,
            activity_name=details.activity_name,
            turno_description=details.turno_description,
            amount=details.price,
            payment_id=payment_id,
        )
