"""Datos de prueba para el escenario: admin genera las cuotas del mes siguiente
y al cliente le llega el mail con el link de pago de Mercado Pago.

Crea (si no existen):
  - un salón activo (la base no trae ninguno),
  - un cliente de prueba (pagotest@demo.com / MiPass12#),
  - un turno de Yoga con clases generadas ~3 meses hacia adelante,
  - una suscripción ACTIVA de ese cliente en ese turno, sin cargo del mes
    siguiente todavía (para que "Generar cuotas del próximo mes" la tome).

Requiere haber corrido antes los seeds base (python -m app.seeds).
Idempotente.

    docker compose exec backend uv run python -m app.seeds_payment_test
"""
import asyncio
from datetime import date, time
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domain.profile import Gender
from app.domain.subscription import SubscriptionStatus
from app.domain.turno import DiaSemana
from app.domain.user import AuthProvider
from app.models.activity import Activity
from app.models.auth import Role, User
from app.models.profile import ClientProfile, DocumentType
from app.models.salon import Salon
from app.models.subscription import Subscription
from app.repositories.activity_repository import ActivityRepository
from app.repositories.clase_repository import ClaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.salon_repository import SalonRepository
from app.repositories.turno_repository import TurnoRepository
from app.services.turno_service import TurnoService
from app.utils.security import hash_password

PASSWORD = "MiPass12#"
EMAIL = "pagotest@demo.com"
TURNO_DESC = "Cuota Pendiente (TEST)"


async def run() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            role_cliente = (await session.execute(select(Role).where(Role.name == "cliente"))).scalar_one_or_none()
            doc_type = (await session.execute(select(DocumentType).where(DocumentType.name == "DNI"))).scalar_one_or_none()
            yoga = (await session.execute(select(Activity).where(Activity.name == "Yoga"))).scalar_one_or_none()
            if not (role_cliente and doc_type and yoga):
                print("[payment-test] faltan roles/actividades base; corré primero 'python -m app.seeds'.")
                return

            salon = (await session.execute(select(Salon).where(Salon.is_active == True))).scalars().first()
            if not salon:
                salon = Salon(name="Salón Principal", capacity=20, is_active=True)
                session.add(salon)
                await session.flush()
                print(f"[payment-test] salón creado: {salon.name}")

            user = (await session.execute(select(User).where(User.email == EMAIL))).scalar_one_or_none()
            if not user:
                user = User(
                    email=EMAIL, hashed_password=hash_password(PASSWORD), role=role_cliente,
                    auth_provider=AuthProvider.LOCAL, is_active=True,
                )
                session.add(user)
                await session.flush()
                session.add(ClientProfile(
                    user_id=user.id, first_name="Pago", last_name="Test", phone="1100000000",
                    birth_date=date(1995, 1, 1), document_type=doc_type, doc_number="30999888",
                    gender=Gender.MALE,
                ))
                await session.flush()
                print(f"[payment-test] cliente creado: {EMAIL} / {PASSWORD}")
            else:
                print(f"[payment-test] cliente ya existía: {EMAIL}")

            turno_repo = TurnoRepository(session)
            existing_turno = await turno_repo.get_by_activity_description_time(
                yoga.id, TURNO_DESC, time(7, 0), time(8, 0), salon.id
            )
            if existing_turno:
                turno = existing_turno
                print(f"[payment-test] turno ya existía: id={turno.id}")
            else:
                service = TurnoService(
                    turno_repo=turno_repo, clase_repo=ClaseRepository(session),
                    activity_repo=ActivityRepository(session), config_repo=ConfigRepository(session),
                    salon_repo=SalonRepository(session),
                    session=session,
                )
                today = date.today()
                turno = await service.create(
                    activity_id=yoga.id, salon_id=salon.id, description=TURNO_DESC,
                    instructor="Instructor Demo", start_time=time(7, 0), end_time=time(8, 0),
                    capacity=10, class_price=Decimal("5000.00"), start_date=today,
                    days=[
                        DiaSemana.LUNES, DiaSemana.MARTES, DiaSemana.MIERCOLES,
                        DiaSemana.JUEVES, DiaSemana.VIERNES,
                    ],
                    is_active=True,
                )
                print(f"[payment-test] turno creado: id={turno.id} (clases generadas ~3 meses hacia adelante)")

            sub = (await session.execute(
                select(Subscription).where(Subscription.user_id == user.id, Subscription.turno_id == turno.id)
            )).scalar_one_or_none()
            if sub:
                print(f"[payment-test] ya existía la suscripción id={sub.id} (status={sub.status}); no se toca.")
            else:
                sub = Subscription(
                    user_id=user.id, turno_id=turno.id, status=SubscriptionStatus.ACTIVE,
                    start_date=date.today().replace(day=1), ends_on=None,
                )
                session.add(sub)
                await session.flush()
                print(f"[payment-test] suscripción ACTIVA creada: id={sub.id}, sin cargo del mes siguiente.")

    print("[payment-test] listo. Iniciá sesión como admin (admin@admin.com / MiPass12#), "
          "generá las cuotas del próximo mes, y revisá http://localhost:8025 (Mailpit) "
          f"para ver el mail que le llega a {EMAIL}.")


if __name__ == "__main__":
    asyncio.run(run())
