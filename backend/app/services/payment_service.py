import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import partial

import mercadopago
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.enrollment import EnrollmentStatus, EnrollmentType
from app.repositories.enrollment_repository import AbstractEnrollmentRepository, _DEPOSIT_RATIO, _REFUND_WINDOW_HOURS
from app.repositories.payment_repository import AbstractPaymentRepository
from app.repositories.user_repository import AbstractUserRepository
from app.services.email_service import EmailService


_ART = timezone(timedelta(hours=-3))
_logger = logging.getLogger(__name__)


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

    # ------------------------------------------------------------------ #
    # Preferencias de pago                                                 #
    # ------------------------------------------------------------------ #

    async def create_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)

        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")

        if details.status != EnrollmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La inscripción no está en estado pendiente.",
            )

        return await self._build_preference(
            enrollment_id=enrollment_id,
            title=f"Inscripción a {details.activity_name} — {details.turno_description}",
            amount=float(details.price),
            external_reference=str(enrollment_id),
            expires_at=details.expires_at,
        )

    async def create_deposit_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)

        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")

        if details.status != EnrollmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La inscripción no está en estado pendiente.",
            )

        deposit_amount = (details.price * _DEPOSIT_RATIO).quantize(Decimal("0.01"))

        return await self._build_preference(
            enrollment_id=enrollment_id,
            title=f"Seña — {details.activity_name} — {details.turno_description}",
            amount=float(deposit_amount),
            external_reference=f"{enrollment_id}:deposit",
            expires_at=details.expires_at,
        )

    async def create_balance_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)

        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")

        if details.status != EnrollmentStatus.DEPOSIT_PAID:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La inscripción no tiene una seña confirmada.",
            )

        balance_amount = (details.price * (1 - _DEPOSIT_RATIO)).quantize(Decimal("0.01"))

        return await self._build_preference(
            enrollment_id=enrollment_id,
            title=f"Saldo — {details.activity_name} — {details.turno_description}",
            amount=float(balance_amount),
            external_reference=f"{enrollment_id}:balance",
            expires_at=details.expires_at,
        )

    async def _build_preference(
        self,
        enrollment_id: int,
        title: str,
        amount: float,
        external_reference: str,
        expires_at,
    ) -> str:
        preference_data = {
            "items": [{
                "title": title,
                "quantity": 1,
                "unit_price": amount,
                "currency_id": "ARS",
            }],
            "back_urls": {
                "success": f"{settings.mp_frontend_url}/payment/success?enrollment_id={enrollment_id}",
                "failure": f"{settings.mp_frontend_url}/payment/failure?enrollment_id={enrollment_id}",
                "pending": f"{settings.mp_frontend_url}/payment/pending?enrollment_id={enrollment_id}",
            },
            "external_reference": external_reference,
            **({"auto_return": "approved"} if settings.mp_frontend_url.startswith("https://") else {}),
            **({"date_of_expiration": _mp_isoformat(expires_at)} if expires_at else {}),
        }
        if settings.mp_notification_url:
            preference_data["notification_url"] = settings.mp_notification_url

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._sdk.preference().create, preference_data)
        )

        if response["status"] not in (200, 201):
            _logger.error("MP preference error: %s", response)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"MP error {response['status']}: {response.get('response')}",
            )

        return response["response"].get("init_point")

    # ------------------------------------------------------------------ #
    # Webhook                                                              #
    # ------------------------------------------------------------------ #

    async def handle_webhook(self, payment_id: str) -> None:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._sdk.payment().get, payment_id)
        )

        if response["status"] != 200:
            return

        payment = response["response"]
        mp_status = payment.get("status")
        external_reference = payment.get("external_reference") or ""

        parts = external_reference.split(":")
        if not parts[0].isdigit():
            return

        enrollment_id = int(parts[0])
        payment_type = parts[1] if len(parts) > 1 else "full"

        if mp_status == "approved":
            if payment_type == "deposit":
                await self._handle_deposit_approved(enrollment_id, payment_id)
            elif payment_type == "balance":
                await self._handle_balance_approved(enrollment_id, payment_id)
            else:
                await self._handle_full_payment_approved(enrollment_id, payment_id)
        elif mp_status in ("rejected", "cancelled"):
            if payment_type == "full":
                await self._enrollment_repo.update_payment(
                    enrollment_id=enrollment_id,
                    new_status=EnrollmentStatus.CANCELLED,
                    payment_id=payment_id,
                )

    async def _handle_deposit_approved(self, enrollment_id: int, payment_id: str) -> None:
        details = await self._enrollment_repo.get_payment_details(enrollment_id)
        deposit_amount = (details.price * _DEPOSIT_RATIO).quantize(Decimal("0.01"))
        await self._enrollment_repo.confirm_deposit(
            enrollment_id=enrollment_id,
            deposit_payment_id=payment_id,
            deposit_amount=deposit_amount,
        )

    async def _handle_balance_approved(self, enrollment_id: int, payment_id: str) -> None:
        updated = await self._enrollment_repo.confirm_balance(
            enrollment_id=enrollment_id,
            payment_id=payment_id,
        )
        if updated:
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

    async def _handle_full_payment_approved(self, enrollment_id: int, payment_id: str) -> None:
        updated = await self._enrollment_repo.update_payment(
            enrollment_id=enrollment_id,
            new_status=EnrollmentStatus.CONFIRMED,
            payment_id=payment_id,
        )
        if updated:
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

    # ------------------------------------------------------------------ #
    # Cancelación con reintegro de seña                                    #
    # ------------------------------------------------------------------ #

    async def cancel_deposit_enrollment(self, enrollment_id: int, user_id: int) -> dict:
        info = await self._enrollment_repo.get_deposit_info(enrollment_id, user_id)
        if info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inscripción con seña no encontrada.",
            )

        now = datetime.now(_ART)
        refund_deadline = info.clase_start - timedelta(hours=_REFUND_WINDOW_HOURS)
        eligible_for_refund = now < refund_deadline

        if eligible_for_refund:
            refund_id = await self._process_mp_refund(info.deposit_payment_id, info.deposit_amount)
            await self._enrollment_repo.cancel_deposit_with_refund(
                enrollment_id=enrollment_id,
                user_id=user_id,
                refund_id=refund_id,
            )
            return {"refund": True, "refund_id": refund_id}
        else:
            await self._enrollment_repo.cancel_deposit_no_refund(
                enrollment_id=enrollment_id,
                user_id=user_id,
            )
            return {"refund": False}

    async def _process_mp_refund(self, payment_id: str, amount: Decimal) -> str:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._sdk.refund().create, payment_id, {"amount": float(amount)}),
        )
        if response["status"] not in (200, 201):
            _logger.error("MP refund error: %s", response)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No se pudo procesar el reintegro con Mercado Pago.",
            )
        return str(response["response"].get("id", ""))

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

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
        await self._send_payment_email(enrollment_id, "free")

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
        first_name = user.client_profile.first_name
        if details.enrollment_type == EnrollmentType.SUBSCRIPTION:
            self._email_service.send_subscription_confirmed(
                to=user.email,
                first_name=first_name,
                activity_name=details.activity_name,
                turno_description=details.turno_description,
                amount=details.price,
                original_amount=details.original_amount,
                discount_full_classes=details.discount_full_classes,
                payment_id=payment_id,
            )
        else:
            self._email_service.send_single_confirmed(
                to=user.email,
                first_name=first_name,
                activity_name=details.activity_name,
                turno_description=details.turno_description,
                num_classes=details.num_classes_snapshot,
                class_price=details.class_price_snapshot,
                amount=details.price,
                payment_id=payment_id,
            )
