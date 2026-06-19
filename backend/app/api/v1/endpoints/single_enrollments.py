from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domain.user import User
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.schemas.single_enrollment import (
    CreateSingleEnrollmentRequest,
    MySingleEnrollmentResponse,
    SingleEnrollmentResponse,
)
from app.services.single_enrollment_service import SingleEnrollmentService

router = APIRouter()


def get_single_service(db: AsyncSession = Depends(get_db)) -> SingleEnrollmentService:
    return SingleEnrollmentService(single_repo=SingleEnrollmentRepository(db))


@router.post("", response_model=SingleEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def create_single_enrollment(
    body: CreateSingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: SingleEnrollmentService = Depends(get_single_service),
):
    enrollment = await service.create_single(clase_ids=body.clase_ids, user_id=current_user.id)
    return SingleEnrollmentResponse.model_validate(enrollment.__dict__)


@router.get("/me", response_model=list[MySingleEnrollmentResponse], status_code=status.HTTP_200_OK)
async def list_my_single_enrollments(
    current_user: User = Depends(get_current_user),
    service: SingleEnrollmentService = Depends(get_single_service),
):
    items = await service.get_single_by_user(user_id=current_user.id)
    return [MySingleEnrollmentResponse.model_validate(e.__dict__) for e in items]


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_single_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    service: SingleEnrollmentService = Depends(get_single_service),
):
    await service.cancel_enrollment(enrollment_id=enrollment_id, user_id=current_user.id)
