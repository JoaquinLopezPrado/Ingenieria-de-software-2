from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domain.user import User
from app.repositories.enrollment_repository import EnrollmentRepository
from app.schemas.enrollment import (
    CreateSubscriptionEnrollmentRequest,
    CreateSingleEnrollmentRequest,
    EnrollmentResponse,
    MySubscriptionEnrollmentResponse,
    MySingleEnrollmentResponse,
)
from app.services.enrollment_service import EnrollmentService

router = APIRouter()


def get_enrollment_service(db: AsyncSession = Depends(get_db)) -> EnrollmentService:
    return EnrollmentService(enrollment_repo=EnrollmentRepository(db))


@router.post(
    "/subscription",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_enrollment(
    body: CreateSubscriptionEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment = await service.create_subscription(turno_id=body.turno_id, user_id=current_user.id)
    return EnrollmentResponse.model_validate(enrollment.__dict__)


@router.post(
    "/single",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_single_enrollment(
    body: CreateSingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: EnrollmentService = Depends(get_enrollment_service),
):
    enrollment = await service.create_single(clase_id=body.clase_id, user_id=current_user.id)
    return EnrollmentResponse.model_validate(enrollment.__dict__)


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    service: EnrollmentService = Depends(get_enrollment_service),
):
    await service.cancel_enrollment(enrollment_id=enrollment_id, user_id=current_user.id)


@router.get(
    "/my/subscription",
    response_model=list[MySubscriptionEnrollmentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_my_subscriptions(
    current_user: User = Depends(get_current_user),
    service: EnrollmentService = Depends(get_enrollment_service),
):
    items = await service.get_subscriptions_by_user(user_id=current_user.id)
    return [MySubscriptionEnrollmentResponse.model_validate(e.__dict__) for e in items]


@router.get(
    "/my/single",
    response_model=list[MySingleEnrollmentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_my_single_enrollments(
    current_user: User = Depends(get_current_user),
    service: EnrollmentService = Depends(get_enrollment_service),
):
    items = await service.get_single_by_user(user_id=current_user.id)
    return [MySingleEnrollmentResponse.model_validate(e.__dict__) for e in items]
