import asyncio
from datetime import date

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domain.profile import Gender
from app.domain.user import AuthProvider
from app.models.auth import Role, User
from app.models.profile import ClientProfile, DocumentType, EmployeeProfile
from app.utils.security import hash_password

ROLES = [
    {"name": "admin", "description": "Administrador del sistema"},
    {"name": "empleado", "description": "Empleado del centro"},
    {"name": "cliente", "description": "Cliente del centro"},
]

DOCUMENT_TYPES = ["DNI", "PASAPORTE"]

USERS = [
    {
        "email": "admin@admin.com",
        "password": "admin1234",
        "role": "admin",
        "profile": None,
    },
    {
        "email": "empleado@centro.com",
        "password": "empleado1234",
        "role": "empleado",
        "profile": {
            "type": "employee",
            "first_name": "Juan",
            "last_name": "Pérez",
            "internal_file_number": "EMP-001",
        },
    },
    {
        "email": "cliente@centro.com",
        "password": "cliente1234",
        "role": "cliente",
        "profile": {
            "type": "client",
            "first_name": "María",
            "last_name": "González",
            "phone": "1122334455",
            "birth_date": date(1990, 6, 15),
            "doc_type": "DNI",
            "doc_number": "12345678",
            "gender": Gender.FEMALE,
        },
    },
]


async def seed_roles(session) -> dict[str, Role]:
    roles = {}
    for data in ROLES:
        result = await session.execute(select(Role).where(Role.name == data["name"]))
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(**data)
            session.add(role)
            print(f"[seed] rol creado: {data['name']}")
        roles[data["name"]] = role
    await session.flush()
    return roles


async def seed_document_types(session) -> dict[str, DocumentType]:
    doc_types = {}
    for name in DOCUMENT_TYPES:
        result = await session.execute(select(DocumentType).where(DocumentType.name == name))
        doc_type = result.scalar_one_or_none()
        if doc_type is None:
            doc_type = DocumentType(name=name)
            session.add(doc_type)
            print(f"[seed] tipo de documento creado: {name}")
        doc_types[name] = doc_type
    await session.flush()
    return doc_types


async def seed_users(session, roles: dict[str, Role], doc_types: dict[str, DocumentType]) -> None:
    for data in USERS:
        result = await session.execute(select(User).where(User.email == data["email"]))
        if result.scalar_one_or_none() is not None:
            continue

        user = User(
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            role=roles[data["role"]],
            auth_provider=AuthProvider.LOCAL,
            is_active=True,
        )
        session.add(user)
        await session.flush()

        profile = data["profile"]
        if profile is None:
            pass
        elif profile["type"] == "employee":
            session.add(EmployeeProfile(
                user_id=user.id,
                first_name=profile["first_name"],
                last_name=profile["last_name"],
                internal_file_number=profile.get("internal_file_number"),
            ))
        elif profile["type"] == "client":
            session.add(ClientProfile(
                user_id=user.id,
                first_name=profile["first_name"],
                last_name=profile["last_name"],
                phone=profile["phone"],
                birth_date=profile["birth_date"],
                document_type=doc_types[profile["doc_type"]],
                doc_number=profile["doc_number"],
                gender=profile["gender"],
            ))

        print(f"[seed] usuario creado: {data['email']}")


async def run():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            roles = await seed_roles(session)
            doc_types = await seed_document_types(session)
            await seed_users(session, roles, doc_types)
    print("[seed] listo")


if __name__ == "__main__":
    asyncio.run(run())
