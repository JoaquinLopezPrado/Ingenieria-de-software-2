import base64
import io

import pyotp
import qrcode
from fastapi import HTTPException, status

from app.repositories.user_repository import AbstractUserRepository


class TwoFactorService:

    def __init__(self, user_repo: AbstractUserRepository):
        self._user_repo = user_repo

    def generate_setup(self, email: str) -> dict:
        secret = pyotp.random_base32()
        uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name="Centro Deportivo")
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        return {"secret": secret, "qr": f"data:image/png;base64,{qr_b64}"}

    async def confirm_setup(self, user_id: int, secret: str, code: str) -> None:
        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código ingresado no es válido. Intentá de nuevo.",
            )
        await self._user_repo.update_totp(user_id, secret)

    async def verify_code(self, user_id: int, code: str) -> bool:
        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.totp_secret:
            return False
        return pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)

    async def disable(self, user_id: int, code: str) -> None:
        if not await self.verify_code(user_id, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código ingresado no es válido. Intentá de nuevo.",
            )
        await self._user_repo.disable_2fa(user_id)
