import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import partial

import mercadopago
from fastapi import HTTPException, status

from app.core.config import settings
from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import ChargeStatus
from app.repositories.config_repository import AbstractConfigRepository
from app.repositories.payment_repository import AbstractPaymentRepository
from app.repositories.single_enrollment_repository import (
    AbstractSingleEnrollmentRepository,
    DepositInfo,
    _DEPOSIT_DEADLINE_HOURS,
    _DEPOSIT_RATIO,
)
from app.repositories.subscription_repository import AbstractSubscriptionRepository
from app.repositories.user_repository import AbstractUserRepository
from app.services.email_service import EmailService


_ART = timezone(timedelta(hours=-3))
_logger = logging.getLogger(__name__)


def _mp_isoformat(dt) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_ART).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")


class PaymentService:

    def __init__(
        self,
        subscription_repo: AbstractSubscriptionRepository,
        single_repo: AbstractSingleEnrollmentRepository,
        user_repo: AbstractUserRepository,
        payment_repo: AbstractPaymentRepository,
        config_repo: AbstractConfigRepository,
    ):
        self._subscription_repo = subscription_repo
        self._single_repo = single_repo
        self._user_repo = user_repo
        self._payment_repo = payment_repo
        self._config_repo = config_repo
        self._email_service = EmailService()
        self._sdk = mercadopago.SDK(settings.mp_access_token)

    # ------------------------------------------------------------------ #
    # Preferencias — suscripción (cargo mensual)                          #
    # ------------------------------------------------------------------ #

    async def create_subscription_charge_preference(self, charge_id: int, user_id: int) -> str:
        details = await self._subscription_repo.get_charge_details(charge_id)
        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")
        if details.status not in (ChargeStatus.PENDING, ChargeStatus.OVERDUE):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El cargo no está pendiente de pago.")

        return await self._build_preference(
            ref_id=charge_id,
            title=f"Suscripción a {details.activity_name} — {details.turno_description}",
            amount=float(details.amount),
            external_reference=f"sub:{charge_id}",
            expires_at=details.expires_at,
        )

    async def free_confirm_subscription(self, charge_id: int, user_id: int) -> None:
        details = await self._subscription_repo.get_charge_details(charge_id)
        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")
        if details.status not in (ChargeStatus.PENDING, ChargeStatus.OVERDUE):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El cargo no está pendiente de pago.")
        if details.amount != 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este cargo requiere pago a través de Mercado Pago.",
            )
        await self._confirm_subscription_charge(charge_id, "free")

    # ------------------------------------------------------------------ #
    # Preferencias — clase suelta                                         #
    # ------------------------------------------------------------------ #

    async def create_single_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._single_repo.get_single_details(enrollment_id)
        self._assert_single_pending(details, user_id)
        return await self._build_preference(
            ref_id=enrollment_id,
            title=f"Inscripción a {details.activity_name} — {details.turno_description}",
            amount=float(details.amount),
            external_reference=f"single:{enrollment_id}",
            expires_at=details.expires_at,
        )

    async def create_single_deposit_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._single_repo.get_single_details(enrollment_id)
        self._assert_single_pending(details, user_id)
        if details.clase_start:
            deadline = details.clase_start - timedelta(hours=_DEPOSIT_DEADLINE_HOURS)
            if datetime.now(timezone.utc) >= deadline:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya no es posible pagar la seña. La clase comienza en menos de 1 hora.",
                )
        deposit_amount = (details.amount * _DEPOSIT_RATIO).quantize(Decimal("0.01"))
        return await self._build_preference(
            ref_id=enrollment_id,
            title=f"Seña — {details.activity_name} — {details.turno_description}",
            amount=float(deposit_amount),
            external_reference=f"single:{enrollment_id}:deposit",
            expires_at=details.expires_at,
        )

    async def create_single_balance_preference(self, enrollment_id: int, user_id: int) -> str:
        details = await self._single_repo.get_single_details(enrollment_id)
        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")
        if details.status != SingleEnrollmentStatus.DEPOSIT_PAID:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La inscripción no tiene una seña confirmada.")
        if details.expires_at and details.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El plazo para completar el pago ha vencido.")
        balance_amount = (details.amount * (1 - _DEPOSIT_RATIO)).quantize(Decimal("0.01"))
        return await self._build_preference(
            ref_id=enrollment_id,
            title=f"Saldo — {details.activity_name} — {details.turno_description}",
            amount=float(balance_amount),
            external_reference=f"single:{enrollment_id}:balance",
            expires_at=details.expires_at,
        )

    def _assert_single_pending(self, details, user_id: int) -> None:
        if details.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin permisos.")
        if details.status != SingleEnrollmentStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La inscripción no está en estado pendiente.")

    # ------------------------------------------------------------------ #
    # Construcción de preferencia MP                                       #
    # ------------------------------------------------------------------ #

    async def _build_preference(self, ref_id: int, title: str, amount: float, external_reference: str, expires_at) -> str:
        preference_data = {
            "items": [{"title": title, "quantity": 1, "unit_price": amount, "currency_id": "ARS"}],
            "back_urls": {
                "success": f"{settings.mp_frontend_url}/payment/success?ref={external_reference}",
                "failure": f"{settings.mp_frontend_url}/payment/failure?ref={external_reference}",
                "pending": f"{settings.mp_frontend_url}/payment/pending?ref={external_reference}",
            },
            "external_reference": external_reference,
            **({"auto_return": "approved"} if settings.mp_frontend_url.startswith("https://") else {}),
            **({"date_of_expiration": _mp_isoformat(expires_at)} if expires_at else {}),
        }
        if settings.mp_notification_url:
            preference_data["notification_url"] = settings.mp_notification_url

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(self._sdk.preference().create, preference_data))
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
        response = await loop.run_in_executor(None, partial(self._sdk.payment().get, payment_id))
        if response["status"] != 200:
            return

        payment = response["response"]
        mp_status = payment.get("status")
        external_reference = payment.get("external_reference") or ""
        parts = external_reference.split(":")
        if len(parts) < 2 or not parts[1].isdigit():
            return

        source, ref_id = parts[0], int(parts[1])

        if source == "sub":
            if mp_status == "approved":
                await self._confirm_subscription_charge(ref_id, payment_id)
            return

        if source == "single":
            kind = parts[2] if len(parts) > 2 else "full"
            if mp_status == "approved":
                if kind == "deposit":
                    await self._handle_single_deposit_approved(ref_id, payment_id)
                elif kind == "balance":
                    await self._handle_single_balance_approved(ref_id, payment_id)
                else:
                    await self._handle_single_full_approved(ref_id, payment_id)
            elif mp_status in ("rejected", "cancelled") and kind == "full":
                await self._single_repo.update_payment(
                    enrollment_id=ref_id,
                    new_status=SingleEnrollmentStatus.CANCELLED,
                    payment_id=payment_id,
                )

    async def _confirm_subscription_charge(self, charge_id: int, payment_id: str) -> None:
        confirmed = await self._subscription_repo.mark_charge_paid(charge_id, payment_id)
        if not confirmed:
            return
        details = await self._subscription_repo.get_charge_details(charge_id)
        await self._payment_repo.create(
            amount=details.amount,
            class_price_snapshot=details.class_price_snapshot,
            num_classes_snapshot=details.num_classes_snapshot,
            payment_provider_id=payment_id,
            confirmed_at=datetime.now(timezone.utc),
            activity_id=details.activity_id,
            activity_name_snapshot=details.activity_name,
            month_snapshot=details.period_month,
            year_snapshot=details.period_year,
            source_type_snapshot="subscription",
            subscription_charge_id=charge_id,
        )
        await self._send_subscription_email(details, payment_id)

    async def _handle_single_full_approved(self, enrollment_id: int, payment_id: str) -> None:
        updated = await self._single_repo.update_payment(
            enrollment_id=enrollment_id,
            new_status=SingleEnrollmentStatus.CONFIRMED,
            payment_id=payment_id,
        )
        if updated:
            details = await self._single_repo.get_single_details(enrollment_id)
            await self._create_single_payment(details, payment_id)
            await self._send_single_email(details, payment_id)

    async def _handle_single_deposit_approved(self, enrollment_id: int, payment_id: str) -> None:
        details = await self._single_repo.get_single_details(enrollment_id)
        deposit_amount = (details.amount * _DEPOSIT_RATIO).quantize(Decimal("0.01"))
        confirmed = await self._single_repo.confirm_deposit(
            enrollment_id=enrollment_id,
            deposit_payment_id=payment_id,
            deposit_amount=deposit_amount,
        )
        if confirmed:
            await self._send_deposit_email(details, payment_id, deposit_amount)

    async def _handle_single_balance_approved(self, enrollment_id: int, payment_id: str) -> None:
        updated = await self._single_repo.confirm_balance(enrollment_id=enrollment_id, payment_id=payment_id)
        if updated:
            details = await self._single_repo.get_single_details(enrollment_id)
            await self._create_single_payment(details, payment_id)
            await self._send_balance_email(details, payment_id)

    async def _create_single_payment(self, details, payment_id: str) -> None:
        today = datetime.now(_ART).date()
        await self._payment_repo.create(
            amount=details.amount,
            class_price_snapshot=details.class_price_snapshot,
            num_classes_snapshot=details.num_classes_snapshot,
            payment_provider_id=payment_id,
            confirmed_at=datetime.now(timezone.utc),
            activity_id=details.activity_id,
            activity_name_snapshot=details.activity_name,
            month_snapshot=today.month,
            year_snapshot=today.year,
            source_type_snapshot="single",
            single_enrollment_id=details.enrollment_id,
        )

    # ------------------------------------------------------------------ #
    # Cancelación con reintegro de seña (clase suelta)                     #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Pago en efectivo (admin / empleado)                                  #
    # ------------------------------------------------------------------ #

    async def cash_confirm_subscription_charge(self, charge_id: int) -> None:
        await self._confirm_subscription_charge(charge_id, "CASH")

    async def cash_confirm_single_enrollment(self, enrollment_id: int) -> None:
        await self._handle_single_full_approved(enrollment_id, "CASH")

    # ------------------------------------------------------------------ #
    # Cancelación con reintegro de seña (clase suelta)                     #
    # ------------------------------------------------------------------ #

    async def cancel_deposit_enrollment(self, enrollment_id: int, user_id: int) -> dict:
        info = await self._single_repo.get_deposit_info(enrollment_id, user_id)
        if info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción con seña no encontrada.")

        refund_window_hours = await self._config_repo.get_int("refund_window_hours", 24)
        now = datetime.now(_ART)
        eligible_for_refund = now < info.clase_start - timedelta(hours=refund_window_hours)

        if eligible_for_refund:
            await self._single_repo.cancel_deposit_with_refund(enrollment_id=enrollment_id, user_id=user_id, refund_id="manual")
            await self._send_refund_email(enrollment_id, user_id, info)
            return {"refund": True}
        await self._single_repo.cancel_deposit_no_refund(enrollment_id=enrollment_id, user_id=user_id)
        return {"refund": False}

    # ------------------------------------------------------------------ #
    # Utilidades                                                           #
    # ------------------------------------------------------------------ #

    async def get_mp_status_detail(self, payment_id: str) -> str | None:
        if not payment_id or payment_id == "0":
            return None
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(self._sdk.payment().get, payment_id))
        if response["status"] != 200:
            return None
        return response["response"].get("status_detail")

    # ------------------------------------------------------------------ #
    # Emails                                                               #
    # ------------------------------------------------------------------ #

    async def _send_subscription_email(self, details, payment_id: str) -> None:
        user = await self._user_repo.get_by_id(details.user_id)
        if not user or not user.client_profile:
            return
        self._email_service.send_subscription_confirmed(
            to=user.email,
            first_name=user.client_profile.first_name,
            activity_name=details.activity_name,
            turno_description=details.turno_description,
            amount=details.amount,
            original_amount=details.original_amount,
            payment_id=payment_id,
        )

    async def _send_single_email(self, details, payment_id: str) -> None:
        user = await self._user_repo.get_by_id(details.user_id)
        if not user or not user.client_profile:
            return
        self._email_service.send_single_confirmed(
            to=user.email,
            first_name=user.client_profile.first_name,
            activity_name=details.activity_name,
            turno_description=details.turno_description,
            num_classes=details.num_classes_snapshot,
            class_price=details.class_price_snapshot,
            amount=details.amount,
            payment_id=payment_id,
            clase_dates=details.clase_dates,
        )

    async def _send_deposit_email(self, details, payment_id: str, deposit_amount: Decimal) -> None:
        user = await self._user_repo.get_by_id(details.user_id)
        if not user or not user.client_profile:
            return
        balance_amount = (details.amount * (1 - _DEPOSIT_RATIO)).quantize(Decimal("0.01"))
        self._email_service.send_deposit_confirmed(
            to=user.email,
            first_name=user.client_profile.first_name,
            activity_name=details.activity_name,
            turno_description=details.turno_description,
            clase_dates=details.clase_dates,
            deposit_amount=deposit_amount,
            balance_amount=balance_amount,
            payment_id=payment_id,
        )

    async def _send_balance_email(self, details, payment_id: str) -> None:
        user = await self._user_repo.get_by_id(details.user_id)
        if not user or not user.client_profile:
            return
        deposit_amount = (details.amount * _DEPOSIT_RATIO).quantize(Decimal("0.01"))
        balance_amount = (details.amount * (1 - _DEPOSIT_RATIO)).quantize(Decimal("0.01"))
        self._email_service.send_balance_confirmed(
            to=user.email,
            first_name=user.client_profile.first_name,
            activity_name=details.activity_name,
            turno_description=details.turno_description,
            clase_dates=details.clase_dates,
            class_price=details.class_price_snapshot,
            deposit_amount=deposit_amount,
            balance_amount=balance_amount,
            payment_id=payment_id,
        )

    async def _send_refund_email(self, enrollment_id: int, user_id: int, info: "DepositInfo") -> None:
        try:
            user = await self._user_repo.get_by_id(user_id)
            details = await self._single_repo.get_single_details(enrollment_id)
            if user and user.client_profile:
                self._email_service.send_deposit_refunded(
                    to=user.email,
                    first_name=user.client_profile.first_name,
                    activity_name=details.activity_name,
                    turno_description=details.turno_description,
                    clase_start=info.clase_start,
                    deposit_amount=info.deposit_amount,
                )
        except Exception:
            _logger.exception("Error al enviar email de reembolso para enrollment %s", enrollment_id)
