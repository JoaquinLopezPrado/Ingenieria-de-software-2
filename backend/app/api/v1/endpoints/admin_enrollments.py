from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.repositories.config_repository import ConfigRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_enrollment import (
    AdminSingleEnrollRequest,
    AdminSingleEnrollResponse,
    AdminSubscriptionEnrollRequest,
    AdminSubscriptionEnrollResponse,
    AdminSubscriptionPreviewRequest,
    AdminSubscriptionPreviewResponse,
)
from app.services.payment_service import PaymentService
from app.services.single_enrollment_service import SingleEnrollmentService
from app.services.subscription_service import SubscriptionService

router = APIRouter()


def _get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(subscription_repo=SubscriptionRepository(db))


def _get_single_service(db: AsyncSession = Depends(get_db)) -> SingleEnrollmentService:
    return SingleEnrollmentService(single_repo=SingleEnrollmentRepository(db))


def _get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        subscription_repo=SubscriptionRepository(db),
        single_repo=SingleEnrollmentRepository(db),
        user_repo=UserRepository(db),
        payment_repo=PaymentRepository(db),
        config_repo=ConfigRepository(db),
    )


@router.post(
    "/subscription/preview",
    response_model=AdminSubscriptionPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def preview_subscription_enrollment(
    body: AdminSubscriptionPreviewRequest,
    _=require_roles("admin", "empleado"),
    service: SubscriptionService = Depends(_get_subscription_service),
):
    plan = await service.preview_subscription(body.turno_id, body.user_id)
    return AdminSubscriptionPreviewResponse(
        amount=plan.amount,
        period_month=plan.period_month,
        period_year=plan.period_year,
    )


@router.post(
    "/subscription",
    response_model=AdminSubscriptionEnrollResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_subscription_cash(
    body: AdminSubscriptionEnrollRequest,
    _=require_roles("admin", "empleado"),
    subscription_service: SubscriptionService = Depends(_get_subscription_service),
    payment_service: PaymentService = Depends(_get_payment_service),
):
    charge = await subscription_service.create(body.turno_id, body.user_id)
    await payment_service.cash_confirm_subscription_charge(charge.id)
    return AdminSubscriptionEnrollResponse(
        subscription_id=charge.subscription_id,
        charge_id=charge.id,
        amount=charge.amount,
        period_month=charge.period_month,
        period_year=charge.period_year,
    )


@router.post(
    "/single",
    response_model=AdminSingleEnrollResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_single_cash(
    body: AdminSingleEnrollRequest,
    _=require_roles("admin", "empleado"),
    single_service: SingleEnrollmentService = Depends(_get_single_service),
    payment_service: PaymentService = Depends(_get_payment_service),
):
    enrollment = await single_service.create_single(clase_ids=body.clase_ids, user_id=body.user_id)
    await payment_service.cash_confirm_single_enrollment(enrollment.id)
    return AdminSingleEnrollResponse(
        enrollment_id=enrollment.id,
        amount=enrollment.amount,
    )
