import asyncio
import logging
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from app.core.config import settings
from app.services.email_templates import enrollment_confirmed, payment_confirmed, welcome

logger = logging.getLogger(__name__)


class EmailService:

    def send_welcome(self, to: str, first_name: str) -> None:
        asyncio.create_task(
            self._send(to, "¡Bienvenido/a a Centro de Actividades!", welcome(first_name))
        )

    def send_enrollment_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        amount: Decimal,
        payment_id: str,
    ) -> None:
        html = enrollment_confirmed(first_name, activity_name, turno_description, amount, payment_id)
        asyncio.create_task(
            self._send(to, f"Inscripción confirmada — {activity_name}", html)
        )

    def send_payment_confirmed(
        self,
        to: str,
        first_name: str,
        activity_name: str,
        turno_description: str,
        price: Decimal,
        payment_id: str,
    ) -> None:
        html = payment_confirmed(first_name, activity_name, turno_description, price, payment_id)
        asyncio.create_task(
            self._send(to, f"Pago confirmado — Centro de Actividades", html)
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
                f"{settings.mailpit_api_url.rstrip('/')}/api/v1/send-message",
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
