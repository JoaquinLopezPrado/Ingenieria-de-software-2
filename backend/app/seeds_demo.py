"""Datos de prueba ricos para el centro de actividades.

Crea turnos activos con clases pasadas y futuras, e inscriptos en todos sus
estados, de modo que el admin pueda probar desde la app la mayoría de los flujos:

  - editar el horario/fecha/cupo de una clase puntual (con aviso a inscriptos),
  - la validación que impide bajar el cupo por debajo de los inscriptos,
  - pagos (de abonos y de clases sueltas) y cargos en estados pagado / vencido /
    condonado / pendiente,
  - suscripciones activas, pendientes y dadas de baja; sueltas confirmadas, con
    seña, pendientes, canceladas y reembolsadas,
  - una clase cancelada con su crédito generado,
  - asistencias (presente / ausente) en clases ya dictadas,
  - lista de espera (esperando y promovido) en un turno completo.

Pensado para una base recién migrada + seeds base. Idempotente: si el turno DEMO
de Yoga ya existe, no hace nada.

    docker compose exec backend uv run python -m app.seeds_demo
"""
import asyncio
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domain.attendance import AttendanceStatus
from app.domain.profile import Gender
from app.domain.single_enrollment import SingleEnrollmentStatus
from app.domain.subscription import ChargeStatus, SubscriptionStatus
from app.domain.turno import DiaSemana
from app.domain.user import AuthProvider
from app.domain.waitlist import WaitlistStatus
from app.models.activity import Activity
from app.models.attendance import Attendance
from app.models.auth import Role, User
from app.models.clase import Clase
from app.models.payment import Payment
from app.models.profile import ClientProfile, DocumentType, EmployeeProfile
from app.models.salon import Salon
from app.models.single_enrollment import SingleEnrollment, SingleEnrollmentSlot
from app.models.subscription import Subscription, SubscriptionCharge
from app.models.waitlist import SubscriptionWaitlist
from app.repositories.activity_repository import ActivityRepository
from app.repositories.clase_repository import ClaseRepository
from app.repositories.config_repository import ConfigRepository
from app.repositories.turno_repository import TurnoRepository
from app.schemas.clases import CancelClaseRequest
from app.services.clase_cancellation_service import ClaseCancellationService
from app.services.turno_service import TurnoService
from app.utils.security import hash_password

PASSWORD = "MiPass12#"
UTC = timezone.utc
M = SingleEnrollmentStatus  # alias corto

# Personal del centro: (prefijo_correo, rol, nombre, apellido, legajo|None)
# correos: admin2@demo.com, empleado2@demo.com, empleado3@demo.com
STAFF = [
    ("admin2",     "admin",    "Valeria", "Acuña",    None),
    ("empleado2",  "empleado", "Tomás",   "Herrera",  "EMP-002"),
    ("empleado3",  "empleado", "Paula",   "Giménez",  "EMP-003"),
]

CLIENTS = [
    ("ana",   "Ana",   "Díaz",    "30111222", Gender.FEMALE),
    ("beto",  "Beto",  "Suárez",  "30222333", Gender.MALE),
    ("caro",  "Caro",  "López",    "30333444", Gender.FEMALE),
    ("dario", "Darío", "Méndez",   "30444555", Gender.MALE),
    ("elena", "Elena", "Romero",   "30555666", Gender.FEMALE),
    ("gabi",  "Gabi",  "Torres",   "30666777", Gender.FEMALE),
    ("fede",  "Fede",  "Ramírez",  "30777888", Gender.MALE),
    ("nico",  "Nico",  "Gómez",    "30888999", Gender.MALE),
    ("hugo",  "Hugo",  "Vega",     "30999000", Gender.MALE),
    ("ivan",  "Iván",  "Sosa",     "31000111", Gender.MALE),
    ("pablo", "Pablo", "Acosta",   "31111222", Gender.MALE),
    ("jose",  "José",  "Núñez",    "31222333", Gender.MALE),
    ("kari",  "Kari",  "Flores",   "31333444", Gender.FEMALE),
    ("lara",  "Lara",  "Castro",   "31444555", Gender.FEMALE),
    ("mara",  "Mara",  "Ortiz",    "31555666", Gender.FEMALE),
    ("oscar", "Oscar", "Bravo",    "31666777", Gender.MALE),
]


def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, monthrange(y, m)[1]))


async def get_or_create_client(session, role, doc_type, alias, first, last, doc, gender) -> User:
    email = f"{alias}@demo.com"
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email=email, hashed_password=hash_password(PASSWORD), role=role,
        auth_provider=AuthProvider.LOCAL, is_active=True,
    )
    session.add(user)
    await session.flush()
    session.add(ClientProfile(
        user_id=user.id, first_name=first, last_name=last, phone="1100000000",
        birth_date=date(1995, 1, 1), document_type=doc_type, doc_number=doc, gender=gender,
    ))
    return user


async def get_or_create_staff(session, role, alias, first, last, legajo) -> User:
    email = f"{alias}@demo.com"
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email=email, hashed_password=hash_password(PASSWORD), role=role,
        auth_provider=AuthProvider.LOCAL, is_active=True,
    )
    session.add(user)
    await session.flush()
    if role.name == "empleado":
        session.add(EmployeeProfile(
            user_id=user.id, first_name=first, last_name=last, internal_file_number=legajo,
        ))
    return user


def add_payment(session, *, amount, price, num_classes, source_type, activity,
                month, year, when, charge_id=None, single_id=None) -> None:
    session.add(Payment(
        amount=Decimal(amount),
        class_price_snapshot=Decimal(price),
        num_classes_snapshot=num_classes,
        payment_provider_id=f"DEMO-{source_type}-{charge_id or single_id}-{month}{year}",
        confirmed_at=when,
        activity_id=activity.id,
        activity_name_snapshot=activity.name,
        month_snapshot=month,
        year_snapshot=year,
        source_type_snapshot=source_type,
        subscription_charge_id=charge_id,
        single_enrollment_id=single_id,
    ))


async def future_clases(session, turno_id, today) -> list[Clase]:
    res = await session.execute(
        select(Clase).where(Clase.turno_id == turno_id, Clase.date > today, Clase.is_active == True)
        .order_by(Clase.date)
    )
    return list(res.scalars())


async def past_clases(session, turno_id, today) -> list[Clase]:
    res = await session.execute(
        select(Clase).where(Clase.turno_id == turno_id, Clase.date < today, Clase.is_active == True)
        .order_by(Clase.date.desc())
    )
    return list(res.scalars())


async def run() -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            role = (await session.execute(select(Role).where(Role.name == "cliente"))).scalar_one()
            doc_type = (await session.execute(select(DocumentType).where(DocumentType.name == "DNI"))).scalar_one()
            admin = (await session.execute(
                select(User).join(Role, Role.id == User.role_id).where(Role.name == "admin")
            )).scalars().first()
            activities = {a.name: a for a in (await session.execute(select(Activity))).scalars()}
            salon = (await session.execute(select(Salon).where(Salon.is_active == True))).scalars().first()

            yoga = activities.get("Yoga")
            funcional = activities.get("Funcional")
            pilates = activities.get("Pilates")
            if not (yoga and funcional and pilates and admin and salon):
                print("[demo] faltan actividades/salón/admin base; corré primero los seeds normales.")
                return

            # Personal del centro: 1 admin + 2 empleados extra (independiente de los
            # turnos, así que se crea aunque el resto del demo ya exista).
            roles_by_name = {r.name: r for r in (await session.execute(select(Role))).scalars()}
            for alias, role_name, first, last, legajo in STAFF:
                await get_or_create_staff(session, roles_by_name[role_name], alias, first, last, legajo)
            await session.flush()
            print("[demo] personal creado: admin2@demo.com, empleado2@demo.com, empleado3@demo.com")

            if await TurnoRepository(session).get_by_activity_description_time(
                yoga.id, "Mañana (DEMO)", time(9, 0), time(10, 0), salon.id
            ):
                print("[demo] los turnos DEMO ya existen; nada que hacer.")
                return

            c = {}
            for alias, first, last, doc, gender in CLIENTS:
                c[alias] = await get_or_create_client(session, role, doc_type, alias, first, last, doc, gender)
            await session.flush()

            today = date.today()
            now = datetime.now(UTC)
            prev = add_months(today, -1)
            nxt = add_months(today, 1)
            price = Decimal("5000.00")

            service = TurnoService(
                turno_repo=TurnoRepository(session), clase_repo=ClaseRepository(session),
                activity_repo=ActivityRepository(session), config_repo=ConfigRepository(session),
                session=session,
            )

            # ════════════════════════════════════════════════════════════════
            # Turno A — Yoga "Mañana (DEMO)": empieza hace 30 días (clases pasadas
            # para asistencia) y sigue hacia adelante. Clase futura llena a 3/5.
            # ════════════════════════════════════════════════════════════════
            turno_a = await service.create(
                activity_id=yoga.id, description="Mañana (DEMO)", instructor="Lucía Fernández",
                start_time=time(9, 0), end_time=time(10, 0), capacity=5, class_price=price,
                start_date=today - timedelta(days=30),
                days=[DiaSemana.LUNES, DiaSemana.MIERCOLES, DiaSemana.VIERNES], is_active=True,
            )
            fut_a = await future_clases(session, turno_a.id, today)
            past_a = await past_clases(session, turno_a.id, today)

            # Abonada ACTIVE (ana): cargos mes anterior/actual/siguiente PAGADOS + pagos.
            sub_ana = Subscription(user_id=c["ana"].id, turno_id=turno_a.id,
                                   status=SubscriptionStatus.ACTIVE,
                                   start_date=prev.replace(day=1), ends_on=None)
            session.add(sub_ana)
            await session.flush()
            for ref in (prev, today, nxt):
                ch = SubscriptionCharge(subscription_id=sub_ana.id, period_month=ref.month,
                                        period_year=ref.year, amount=price, status=ChargeStatus.PAID,
                                        paid_at=now)
                session.add(ch)
                await session.flush()
                add_payment(session, amount=price, price=price, num_classes=12,
                            source_type="subscription", activity=yoga, month=ref.month,
                            year=ref.year, when=now, charge_id=ch.id)

            # Abonado dado de BAJA (ivan): ends_on el mes pasado; un cargo PAGADO y uno CONDONADO.
            sub_ivan = Subscription(user_id=c["ivan"].id, turno_id=turno_a.id,
                                    status=SubscriptionStatus.CANCELLED,
                                    start_date=add_months(today, -2).replace(day=1),
                                    ends_on=date(prev.year, prev.month, monthrange(prev.year, prev.month)[1]),
                                    cancelled_at=now)
            session.add(sub_ivan)
            await session.flush()
            ch_paid = SubscriptionCharge(subscription_id=sub_ivan.id, period_month=prev.month,
                                         period_year=prev.year, amount=price, status=ChargeStatus.PAID,
                                         paid_at=now)
            session.add(ch_paid)
            await session.flush()
            add_payment(session, amount=price, price=price, num_classes=12, source_type="subscription",
                        activity=yoga, month=prev.month, year=prev.year, when=now, charge_id=ch_paid.id)
            session.add(SubscriptionCharge(subscription_id=sub_ivan.id, period_month=today.month,
                                           period_year=today.year, amount=price, status=ChargeStatus.WAIVED))

            # 2 sueltas CONFIRMADAS (beto, caro) en la 1ª clase futura → queda 3/5 (con ana).
            for alias in ("beto", "caro"):
                enr = SingleEnrollment(turno_id=turno_a.id, user_id=c[alias].id, amount=price,
                                       status=M.CONFIRMED)
                session.add(enr)
                await session.flush()
                session.add(SingleEnrollmentSlot(enrollment_id=enr.id, clase_id=fut_a[0].id))
                add_payment(session, amount=price, price=price, num_classes=1, source_type="single",
                            activity=yoga, month=fut_a[0].date.month, year=fut_a[0].date.year,
                            when=now, single_id=enr.id)

            # Asistencias en las 3 últimas clases pasadas (ana estuvo abonada).
            for i, clase in enumerate(past_a[:3]):
                session.add(Attendance(user_id=c["ana"].id, clase_id=clase.id,
                                       status=AttendanceStatus.PRESENTE if i != 1 else AttendanceStatus.AUSENTE))

            # ════════════════════════════════════════════════════════════════
            # Turno B — Funcional "Tarde (DEMO)": variedad de sueltas + abonos
            # pendientes; una clase futura se CANCELA (genera crédito).
            # ════════════════════════════════════════════════════════════════
            price_b = Decimal("6000.00")
            turno_b = await service.create(
                activity_id=funcional.id, description="Tarde (DEMO)", instructor="Marcos Ruiz",
                start_time=time(18, 0), end_time=time(19, 0), capacity=10, class_price=price_b,
                start_date=today, days=[DiaSemana.MARTES, DiaSemana.JUEVES], is_active=True,
            )
            fut_b = await future_clases(session, turno_b.id, today)

            # dario: CONFIRMADA (paga completo) en la 1ª clase futura.
            enr_d = SingleEnrollment(turno_id=turno_b.id, user_id=c["dario"].id, amount=price_b, status=M.CONFIRMED)
            session.add(enr_d)
            await session.flush()
            session.add(SingleEnrollmentSlot(enrollment_id=enr_d.id, clase_id=fut_b[0].id))
            add_payment(session, amount=price_b, price=price_b, num_classes=1, source_type="single",
                        activity=funcional, month=fut_b[0].date.month, year=fut_b[0].date.year,
                        when=now, single_id=enr_d.id)

            # elena: PENDING (reserva en curso) en la 1ª clase futura → cuenta en cupo, sin pago/email.
            enr_e = SingleEnrollment(turno_id=turno_b.id, user_id=c["elena"].id, amount=price_b, status=M.PENDING)
            session.add(enr_e)
            await session.flush()
            session.add(SingleEnrollmentSlot(enrollment_id=enr_e.id, clase_id=fut_b[0].id))

            # gabi: DEPOSIT_PAID (pagó seña) en la 2ª clase futura + pago de seña.
            senia = (price_b / 2).quantize(Decimal("0.01"))
            enr_g = SingleEnrollment(turno_id=turno_b.id, user_id=c["gabi"].id, amount=price_b,
                                     status=M.DEPOSIT_PAID, deposit_amount=senia, deposit_payment_id="DEMO-DEP-1")
            session.add(enr_g)
            await session.flush()
            session.add(SingleEnrollmentSlot(enrollment_id=enr_g.id, clase_id=fut_b[1].id))
            add_payment(session, amount=senia, price=price_b, num_classes=1, source_type="single",
                        activity=funcional, month=fut_b[1].date.month, year=fut_b[1].date.year,
                        when=now, single_id=enr_g.id)

            # fede: CANCELADA  /  nico: REEMBOLSADA  (sin asiento; historial de estados)
            session.add(SingleEnrollment(turno_id=turno_b.id, user_id=c["fede"].id, amount=price_b, status=M.CANCELLED))
            session.add(SingleEnrollment(turno_id=turno_b.id, user_id=c["nico"].id, amount=price_b,
                                         status=M.REFUNDED, refund_id="DEMO-REF-1"))

            # hugo: abonado ACTIVE con mes anterior VENCIDO y mes actual PAGADO.
            sub_hugo = Subscription(user_id=c["hugo"].id, turno_id=turno_b.id, status=SubscriptionStatus.ACTIVE,
                                    start_date=prev.replace(day=1), ends_on=None)
            session.add(sub_hugo)
            await session.flush()
            session.add(SubscriptionCharge(subscription_id=sub_hugo.id, period_month=prev.month,
                                           period_year=prev.year, amount=price_b, status=ChargeStatus.OVERDUE,
                                           due_date=prev.replace(day=10)))
            ch_h = SubscriptionCharge(subscription_id=sub_hugo.id, period_month=today.month, period_year=today.year,
                                      amount=price_b, status=ChargeStatus.PAID, paid_at=now)
            session.add(ch_h)
            await session.flush()
            add_payment(session, amount=price_b, price=price_b, num_classes=8, source_type="subscription",
                        activity=funcional, month=today.month, year=today.year, when=now, charge_id=ch_h.id)

            # pablo: abonado PENDING (primer cargo sin pagar; ocupa asiento durante el TTL).
            sub_pablo = Subscription(user_id=c["pablo"].id, turno_id=turno_b.id, status=SubscriptionStatus.PENDING,
                                     start_date=today.replace(day=1), ends_on=None)
            session.add(sub_pablo)
            await session.flush()
            session.add(SubscriptionCharge(subscription_id=sub_pablo.id, period_month=today.month,
                                           period_year=today.year, amount=price_b, status=ChargeStatus.PENDING))

            # ════════════════════════════════════════════════════════════════
            # Turno C — Pilates "Mediodía (DEMO)": sin inscriptos (edición simple).
            # ════════════════════════════════════════════════════════════════
            await service.create(
                activity_id=pilates.id, description="Mediodía (DEMO)", instructor="Sofía Castro",
                start_time=time(12, 0), end_time=time(13, 0), capacity=8, class_price=price,
                start_date=today, days=[DiaSemana.LUNES, DiaSemana.MIERCOLES], is_active=True,
            )

            # ════════════════════════════════════════════════════════════════
            # Turno D — Pilates "Completo (DEMO)": cupo 2 lleno + lista de espera.
            # ════════════════════════════════════════════════════════════════
            turno_d = await service.create(
                activity_id=pilates.id, description="Completo (DEMO)", instructor="Sofía Castro",
                start_time=time(19, 0), end_time=time(20, 0), capacity=2, class_price=price,
                start_date=today, days=[DiaSemana.MARTES, DiaSemana.JUEVES], is_active=True,
            )
            for alias in ("jose", "kari"):
                sub = Subscription(user_id=c[alias].id, turno_id=turno_d.id, status=SubscriptionStatus.ACTIVE,
                                   start_date=today.replace(day=1), ends_on=None)
                session.add(sub)
                await session.flush()
                ch = SubscriptionCharge(subscription_id=sub.id, period_month=today.month, period_year=today.year,
                                        amount=price, status=ChargeStatus.PAID, paid_at=now)
                session.add(ch)
                await session.flush()
                add_payment(session, amount=price, price=price, num_classes=8, source_type="subscription",
                            activity=pilates, month=today.month, year=today.year, when=now, charge_id=ch.id)
            # Lista de espera: 2 esperando + 1 ya promovido.
            session.add(SubscriptionWaitlist(user_id=c["lara"].id, turno_id=turno_d.id,
                                             status=WaitlistStatus.WAITING, joined_at=now - timedelta(days=2)))
            session.add(SubscriptionWaitlist(user_id=c["mara"].id, turno_id=turno_d.id,
                                             status=WaitlistStatus.WAITING, joined_at=now - timedelta(days=1)))
            session.add(SubscriptionWaitlist(user_id=c["oscar"].id, turno_id=turno_d.id,
                                             status=WaitlistStatus.PROMOTED, joined_at=now - timedelta(days=5),
                                             promoted_at=now - timedelta(days=3)))

            # ════════════════════════════════════════════════════════════════
            # Cancelación de una clase futura del Turno A (2ª clase): ana está
            # cubierta por su período pagado → se le genera un crédito de 30 días.
            # ════════════════════════════════════════════════════════════════
            await session.flush()
            cancel_service = ClaseCancellationService(session)
            await cancel_service.cancel(
                fut_a[1].id,
                CancelClaseRequest(reason="Clase cancelada por mantenimiento del salón (DEMO)."),
                admin.id,
            )
            print(f"[demo] clase {fut_a[1].date} (Yoga) cancelada → crédito para Ana.")

            print("[demo] turnos: Yoga 'Mañana', Funcional 'Tarde', Pilates 'Mediodía' y 'Completo'.")
            print(f"[demo] clase {fut_a[0].date} (Yoga) con 3/5 inscriptos para probar la regla de cupo.")
    print("[demo] listo")


if __name__ == "__main__":
    asyncio.run(run())
