from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.employee import CreateEmployeeRequest, EmployeeListItem, UpdateEmployeeRequest
from app.services.employee_service import EmployeeService

router = APIRouter()


def get_employee_service(db: AsyncSession = Depends(get_db)) -> EmployeeService:
    return EmployeeService(
        user_repo=UserRepository(db),
        reset_repo=PasswordResetRepository(db),
    )


@router.get("", response_model=list[EmployeeListItem], status_code=status.HTTP_200_OK)
async def list_employees(
    _=require_roles("admin"),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.list_employees()


@router.post("", response_model=EmployeeListItem, status_code=status.HTTP_201_CREATED)
async def create_employee(
    body: CreateEmployeeRequest,
    _=require_roles("admin"),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.create_employee(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )


@router.put("/{employee_id}", response_model=EmployeeListItem, status_code=status.HTTP_200_OK)
async def update_employee(
    employee_id: int,
    body: UpdateEmployeeRequest,
    _=require_roles("admin"),
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.update_employee(
        employee_id=employee_id,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )


@router.patch("/{employee_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_employee(
    employee_id: int,
    _=require_roles("admin"),
    service: EmployeeService = Depends(get_employee_service),
):
    await service.deactivate_employee(employee_id)
    return {"message": "Empleado desactivado."}


@router.patch("/{employee_id}/reactivate", status_code=status.HTTP_200_OK)
async def reactivate_employee(
    employee_id: int,
    _=require_roles("admin"),
    service: EmployeeService = Depends(get_employee_service),
):
    await service.reactivate_employee(employee_id)
    return {"message": "Empleado reactivado."}
