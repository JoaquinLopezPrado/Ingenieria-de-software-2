import math
from datetime import date

from fastapi import HTTPException, status

from app.repositories.profile_repository import AbstractProfileRepository
from app.repositories.single_enrollment_repository import AbstractSingleEnrollmentRepository
from app.repositories.subscription_repository import AbstractSubscriptionRepository
from app.repositories.user_repository import AbstractUserRepository
from app.repositories.waitlist_repository import AbstractWaitlistRepository
from app.schemas.user import (
    ClienteListItem,
    ClientesPaginadosResponse,
    ClientProfileMeResponse,
    DocumentTypeResponse,
    EmployeeProfileMeResponse,
    PagoItem,
    UserMeResponse,
    UpdateClientPhoneRequest,
)
from app.services.email_service import EmailService


class UserService:

    def __init__(
        self,
        user_repo: AbstractUserRepository,
        profile_repo: AbstractProfileRepository,
        subscription_repo: AbstractSubscriptionRepository | None = None,
        single_enrollment_repo: AbstractSingleEnrollmentRepository | None = None,
        waitlist_repo: AbstractWaitlistRepository | None = None,
    ):
        self._user_repo = user_repo
        self._profile_repo = profile_repo
        self._subscription_repo = subscription_repo
        self._single_enrollment_repo = single_enrollment_repo
        self._waitlist_repo = waitlist_repo

    async def list_clients(
        self,
        q: str | None,
        page: int,
        page_size: int,
    ) -> ClientesPaginadosResponse:
        items, total = await self._user_repo.list_clients(q=q, page=page, page_size=page_size)
        total_pages = max(1, math.ceil(total / page_size))
        return ClientesPaginadosResponse(
            items=[
                ClienteListItem(
                    id=row.id,
                    email=row.email,
                    first_name=row.first_name,
                    last_name=row.last_name,
                    phone=row.phone,
                    doc_type_name=row.doc_type_name,
                    doc_number=row.doc_number,
                    is_active=row.is_active,
                )
                for row in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_client_by_id(self, user_id: int) -> ClienteListItem:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado.")
        client = await self._profile_repo.get_client_by_user_id(user_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado.")
        return ClienteListItem(
            id=user.id,
            email=user.email,
            first_name=client.first_name,
            last_name=client.last_name,
            phone=client.phone,
            doc_type_name=client.document_type.name,
            doc_number=client.doc_number,
            is_active=user.is_active,
        )

    async def update_my_phone(
        self,
        user_id: int,
        data: UpdateClientPhoneRequest,
    ) -> UserMeResponse:
        new_phone = data.phone.strip()

        if not new_phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El teléfono es obligatorio.",
            )

        client = await self._profile_repo.get_client_by_user_id(user_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de cliente no encontrado.",
            )

        await self._profile_repo.update_client_phone(user_id=user_id, phone=new_phone)

        return await self.get_me(user_id)

    async def get_me(self, user_id: int) -> UserMeResponse:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado.",
            )

        client_profile = None
        employee_profile = None

        client = await self._profile_repo.get_client_by_user_id(user_id)
        if client:
            client_profile = ClientProfileMeResponse(
                id=client.id,
                first_name=client.first_name,
                last_name=client.last_name,
                phone=client.phone,
                birth_date=client.birth_date,
                document_type=DocumentTypeResponse(
                    id=client.document_type.id,
                    name=client.document_type.name,
                ),
                doc_number=client.doc_number,
                gender=client.gender.value,
            )
        else:
            employee = await self._profile_repo.get_employee_by_user_id(user_id)
            if employee:
                employee_profile = EmployeeProfileMeResponse(
                    id=employee.id,
                    first_name=employee.first_name,
                    last_name=employee.last_name,
                    internal_file_number=employee.internal_file_number,
                )

        return UserMeResponse(
            id=user.id,
            email=user.email,
            role=user.role.name,
            has_google_linked=user.google_id is not None,
            has_local_password=user.hashed_password is not None,
            is_2fa_enabled=user.is_2fa_enabled,
            client_profile=client_profile,
            employee_profile=employee_profile,
        )

    async def deactivate_client(self, user_id: int) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
        if user.role.name != "cliente":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario no es un cliente.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El cliente ya está desactivado.")

        client = await self._profile_repo.get_client_by_user_id(user_id)
        first_name = client.first_name if client else "Cliente"

        await self._subscription_repo.cancel_all_for_user(user_id)
        await self._single_enrollment_repo.cancel_all_future_for_user(user_id)
        await self._waitlist_repo.cancel_all_for_user(user_id)
        await self._user_repo.deactivate_client(user_id)

        EmailService().send_client_deactivated(to=user.email, first_name=first_name)

    async def reactivate_client(self, user_id: int) -> None:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
        if user.role.name != "cliente":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario no es un cliente.")
        if user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El cliente ya está activo.")

        await self._user_repo.reactivate_client(user_id)

    async def get_pagos(self, user_id: int) -> list[PagoItem]:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

        _MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        _CHARGE_ESTADO = {
            "pending": "Pendiente", "paid": "Pagado",
            "overdue": "Vencido", "waived": "Eximido",
        }
        _ENROLLMENT_ESTADO = {
            "pending": "Pendiente", "confirmed": "Confirmado",
            "cancelled": "Cancelado", "deposit_paid": "Seña pagada",
            "deposit_forfeited": "Seña perdida", "refunded": "Reembolsado",
        }

        charges = await self._subscription_repo.list_charges_for_user(user_id)
        enrollments = await self._single_enrollment_repo.list_for_pagos(user_id)

        items: list[PagoItem] = []

        for c in charges:
            raw_status = c["status"].value if hasattr(c["status"], "value") else str(c["status"])
            fecha = c["paid_at"].date() if c["paid_at"] else c["due_date"]
            items.append(PagoItem(
                tipo="suscripcion",
                fecha=fecha,
                actividad=f"{c['activity_name']} — {c['turno_description']}",
                monto=c["amount"],
                estado=_CHARGE_ESTADO.get(raw_status, raw_status),
                periodo=f"{_MESES[c['period_month']]} {c['period_year']}",
            ))

        for e in enrollments:
            raw_status = e["status"].value if hasattr(e["status"], "value") else str(e["status"])
            fecha = e["clase_date"] if e["clase_date"] else None
            items.append(PagoItem(
                tipo="clase_individual",
                fecha=fecha,
                actividad=f"{e['activity_name']} — {e['turno_description']}",
                monto=e["amount"],
                estado=_ENROLLMENT_ESTADO.get(raw_status, raw_status),
                periodo=None,
            ))

        items.sort(key=lambda x: x.fecha or date.min, reverse=True)
        return items