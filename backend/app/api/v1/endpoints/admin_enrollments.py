import asyncio

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles
from app.core.tasks import promote_freed_turnos
from app.repositories.config_repository import ConfigRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.repositories.waitlist_repository import WaitlistRepository
from app.schemas.admin_enrollment import (
    AdminSingleEnrollRequest,
    AdminSingleEnrollResponse,
    AdminSubscriptionEnrollRequest,
    AdminSubscriptionEnrollResponse,
    AdminSubscriptionPreviewRequest,
    AdminSubscriptionPreviewResponse,
    AdminWaitlistEntry,
    AdminWaitlistRequest,
    AdminWaitlistResponse,
    ClasePreviewItem,
)
from app.services.email_service import EmailService
from app.services.payment_service import PaymentService
from app.services.single_enrollment_service import SingleEnrollmentService
from app.services.subscription_service import SubscriptionService
from app.services.waitlist_service import WaitlistService

router = APIRouter()


def _get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(subscription_repo=SubscriptionRepository(db))


def _get_single_service(db: AsyncSession = Depends(get_db)) -> SingleEnrollmentService:
    return SingleEnrollmentService(single_repo=SingleEnrollmentRepository(db))


def _get_waitlist_service(db: AsyncSession = Depends(get_db)) -> WaitlistService:
    return WaitlistService(
        waitlist_repo=WaitlistRepository(db),
        subscription_service=SubscriptionService(subscription_repo=SubscriptionRepository(db)),
        email_service=EmailService(),
    )


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
        turno_id=body.turno_id,
        user_id=body.user_id,
        precio_por_clase=plan.class_price,
        clases_con_cupo=[ClasePreviewItem(clase_id=cid, fecha=d) for cid, d in plan.clases_con_cupo],
        clases_sin_cupo=[ClasePreviewItem(clase_id=cid, fecha=d) for cid, d in plan.clases_sin_cupo],
        clases_ya_abonadas=[ClasePreviewItem(clase_id=cid, fecha=d) for cid, d in plan.clases_ya_abonadas],
        total=plan.amount,
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


@router.get("/waitlist/{user_id}", response_model=list[AdminWaitlistEntry], status_code=status.HTTP_200_OK)
async def get_user_waitlist_entries(
    user_id: int,
    _=require_roles("admin", "empleado"),
    service: WaitlistService = Depends(_get_waitlist_service),
):
    entries = await service.get_by_user(user_id=user_id)
    return [AdminWaitlistEntry(entry_id=e.entry_id, turno_id=e.turno_id) for e in entries]


@router.delete("/waitlist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_remove_from_waitlist(
    entry_id: int,
    _=require_roles("admin", "empleado"),
    service: WaitlistService = Depends(_get_waitlist_service),
):
    await service.admin_leave(entry_id=entry_id)


@router.post(
    "/waitlist",
    response_model=AdminWaitlistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_waitlist(
    body: AdminWaitlistRequest,
    _=require_roles("admin", "empleado"),
    service: WaitlistService = Depends(_get_waitlist_service),
):
    entry = await service.join(turno_id=body.turno_id, user_id=body.user_id)
    return AdminWaitlistResponse(
        entry_id=entry.id,
        turno_id=entry.turno_id,
        user_id=entry.user_id,
    )


@router.post(
    "/subscription/{subscription_id}/cancel",
    status_code=status.HTTP_200_OK,
)
async def admin_cancel_subscription(
    subscription_id: int,
    _=require_roles("admin", "empleado"),
    service: SubscriptionService = Depends(_get_subscription_service),
    db: AsyncSession = Depends(get_db),
):
    """Baja programada iniciada por admin: efectiva al fin del período pagado."""
    ends_on, turno_id = await service.admin_unsubscribe(subscription_id=subscription_id)
    await db.commit()
    asyncio.create_task(promote_freed_turnos([turno_id]))
    return {"ends_on": ends_on.isoformat()}
