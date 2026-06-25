import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from app.core.config import settings
from app.services.email_templates import (
    balance_confirmed,
    cambio_horario_clase,
    cambio_horario_turno,
    clase_cancelada_individual_completo,
    clase_cancelada_individual_senia,
    clase_cancelada_suscripcion,
    deposit_confirmed,
    deposit_refunded,
    password_reset,
    single_payment_confirmed,
    subscription_payment_confirmed,
    turno_baja,
    waitlist_promoted,
    welcome,
)

logger = logging.getLogger(__name__)


class EmailService:

    def send_welcome(self, to: str, first_name: str) -> None:
        asyncio.create_task(
            self._send(to, "¡Bienvenido/a a Centro de Actividades!", welcome(first_name))
        )

    def send_password_reset(self, to: str, reset_url: str) -> None:
        asyncio.create_task(
            self._send(to, "Recuperá tu contraseña — Centro de Actividades", password_reset(reset_url))
        )

    def send_subscription_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        amount: Decimal,
        payment_id: str,
        original_amount: Decimal = Decimal(0),
        discount_full_classes: Decimal = Decimal(0),
    ) -> None:
        html = subscription_payment_confirmed(
            first_name, activity_name, turno_description, amount, payment_id,
            original_amount=original_amount, discount_full_classes=discount_full_classes,
        )
        subject = "Sin costo" if payment_id == "free" else f"$ {amount:,.2f}"
        asyncio.create_task(
            self._send(to, f"Suscripción confirmada — {activity_name} ({subject})", html)
        )

    def send_single_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        num_classes: int,
        class_price: Decimal,
        amount: Decimal,
        payment_id: str,
        clase_dates: list[date] | None = None,
    ) -> None:
        html = single_payment_confirmed(
            first_name, activity_name, turno_description, num_classes, class_price, amount, payment_id,
            clase_dates=clase_dates,
        )
        clases = "clase" if num_classes == 1 else "clases"
        asyncio.create_task(
            self._send(to, f"Inscripción confirmada — {num_classes} {clases} de {activity_name}", html)
        )

    def send_deposit_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_dates: list[date],
        deposit_amount: Decimal,
        balance_amount: Decimal,
        payment_id: str,
    ) -> None:
        html = deposit_confirmed(
            first_name, activity_name, turno_description, clase_dates,
            deposit_amount, balance_amount, payment_id,
        )
        asyncio.create_task(
            self._send(to, f"Seña confirmada — {activity_name}", html)
        )

    def send_deposit_refunded(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_start: datetime,
        deposit_amount: Decimal,
    ) -> None:
        html = deposit_refunded(first_name, activity_name, turno_description, clase_start, deposit_amount)
        asyncio.create_task(
            self._send(to, f"Reembolso de seña — {activity_name}", html)
        )

    def send_balance_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_dates: list[date],
        class_price: Decimal,
        deposit_amount: Decimal,
        balance_amount: Decimal,
        payment_id: str,
    ) -> None:
        html = balance_confirmed(
            first_name, activity_name, turno_description, clase_dates,
            class_price, deposit_amount, balance_amount, payment_id,
        )
        asyncio.create_task(
            self._send(to, f"Pago completado — {activity_name}", html)
        )

    def send_clase_cancelada_suscripcion(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_date: date,
        expires_days: int,
        reason: str,
    ) -> None:
        html = clase_cancelada_suscripcion(first_name, activity_name, turno_description, clase_date, expires_days, reason)
        asyncio.create_task(
            self._send(to, f"Clase cancelada — {activity_name}", html)
        )

    def send_clase_cancelada_individual_completo(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_date: date,
        expires_days: int,
        reason: str,
    ) -> None:
        html = clase_cancelada_individual_completo(
            first_name, activity_name, turno_description, clase_date, expires_days, reason
        )
        asyncio.create_task(
            self._send(to, f"Clase cancelada — {activity_name}", html)
        )

    def send_clase_cancelada_individual_senia(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_date: date,
        senia: Decimal,
        reason: str,
    ) -> None:
        html = clase_cancelada_individual_senia(
            first_name, activity_name, turno_description, clase_date, senia, reason
        )
        asyncio.create_task(
            self._send(to, f"Clase cancelada — {activity_name}", html)
        )

    def send_cambio_horario_turno(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        dias_str: str,
        horario_str: str,
    ) -> None:
        html = cambio_horario_turno(first_name, activity_name, turno_description, dias_str, horario_str)
        asyncio.create_task(
            self._send(to, f"Tu turno cambió — {activity_name}", html)
        )

    def send_cambio_horario_clase(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clase_date: date,
        horario_str: str,
    ) -> None:
        html = cambio_horario_clase(first_name, activity_name, turno_description, clase_date, horario_str)
        asyncio.create_task(
            self._send(to, f"Cambió el horario de tu clase — {activity_name}", html)
        )

    def send_turno_baja(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        clases_canceladas: int,
        creditos: int,
        senia: Decimal,
        expires_days: int,
        reason: str,
    ) -> None:
        html = turno_baja(
            first_name, activity_name, turno_description,
            clases_canceladas, creditos, senia, expires_days, reason,
        )
        asyncio.create_task(
            self._send(to, f"Se dio de baja un turno — {activity_name}", html)
        )

    def send_waitlist_promoted(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        amount: Decimal,
        ttl_minutes: int = 1440,
    ) -> None:
        html = waitlist_promoted(first_name, activity_name, turno_description, float(amount), ttl_minutes)
        asyncio.create_task(
            self._send(to, f"¡Tenés un lugar en {activity_name}! — Centro de Actividades", html)
        )

    async def _send(self, to: str, subject: str, html: str) -> None:
        try:
            if settings.mailpit_api_url:
                await self._send_via_mailpit(to, subject, html)
            elif settings.resend_api_key:
                await self._send_via_resend(to, subject, html)
            else:
                await self._send_via_smtp(to, subject, html)
        except Exception:
            logger.exception("Error al enviar email a %s (asunto: %s)", to, subject)

    async def _send_via_mailpit(self, to: str, subject: str, html: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.mailpit_api_url.rstrip('/')}/api/v1/send",
                json={
                    "From": {"Email": settings.smtp_from},
                    "To": [{"Email": to}],
                    "Subject": subject,
                    "HTML": html,
                },
                timeout=10,
            )
            response.raise_for_status()

    async def _send_via_resend(self, to: str, subject: str, html: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.smtp_from,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10,
            )
            response.raise_for_status()

    async def _send_via_smtp(self, to: str, subject: str, html: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_from
        message["To"] = to
        message.attach(MIMEText(html, "html"))
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_use_tls,
            start_tls=False,
        )
