from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domain.user import User
from app.repositories.config_repository import ConfigRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.single_enrollment_repository import SingleEnrollmentRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payment import CancelDepositResponse, MpStatusResponse, PreferenceResponse
from app.services.payment_service import PaymentService

router = APIRouter()


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        subscription_repo=SubscriptionRepository(db),
        single_repo=SingleEnrollmentRepository(db),
        user_repo=UserRepository(db),
        payment_repo=PaymentRepository(db),
        config_repo=ConfigRepository(db),
    )


class ChargeRequest(BaseModel):
    charge_id: int


class SingleEnrollmentRequest(BaseModel):
    enrollment_id: int


# ---------------------------------------------------------------------- #
# Suscripción (cargo mensual)                                            #
# ---------------------------------------------------------------------- #

@router.post("/subscription-preference", response_model=PreferenceResponse, status_code=status.HTTP_200_OK)
async def create_subscription_preference(
    body: ChargeRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    init_point = await service.create_subscription_charge_preference(charge_id=body.charge_id, user_id=current_user.id)
    return PreferenceResponse(init_point=init_point)


@router.post("/subscription-free-confirm", status_code=status.HTTP_200_OK)
async def free_confirm_subscription(
    body: ChargeRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    await service.free_confirm_subscription(charge_id=body.charge_id, user_id=current_user.id)
    return {"ok": True}


# ---------------------------------------------------------------------- #
# Clase suelta                                                           #
# ---------------------------------------------------------------------- #

@router.post("/single-preference", response_model=PreferenceResponse, status_code=status.HTTP_200_OK)
async def create_single_preference(
    body: SingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    init_point = await service.create_single_preference(enrollment_id=body.enrollment_id, user_id=current_user.id)
    return PreferenceResponse(init_point=init_point)


@router.post("/single-deposit-preference", response_model=PreferenceResponse, status_code=status.HTTP_200_OK)
async def create_single_deposit_preference(
    body: SingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    init_point = await service.create_single_deposit_preference(enrollment_id=body.enrollment_id, user_id=current_user.id)
    return PreferenceResponse(init_point=init_point)


@router.post("/single-balance-preference", response_model=PreferenceResponse, status_code=status.HTTP_200_OK)
async def create_single_balance_preference(
    body: SingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    init_point = await service.create_single_balance_preference(enrollment_id=body.enrollment_id, user_id=current_user.id)
    return PreferenceResponse(init_point=init_point)


@router.post("/cancel-deposit", response_model=CancelDepositResponse, status_code=status.HTTP_200_OK)
async def cancel_deposit_enrollment(
    body: SingleEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    result = await service.cancel_deposit_enrollment(enrollment_id=body.enrollment_id, user_id=current_user.id)
    return CancelDepositResponse(**result)


# ---------------------------------------------------------------------- #
# Utilidades / webhook                                                   #
# ---------------------------------------------------------------------- #

@router.get("/mp-status", response_model=MpStatusResponse, status_code=status.HTTP_200_OK)
async def get_mp_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    detail = await service.get_mp_status_detail(payment_id)
    return MpStatusResponse(status_detail=detail)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    data_id: str | None = Query(default=None, alias="data.id"),
    notification_type: str | None = Query(default=None, alias="type"),
    ipn_id: str | None = Query(default=None, alias="id"),
    topic: str | None = Query(default=None),
    service: PaymentService = Depends(get_payment_service),
):
    payment_id = None
    if notification_type == "payment" and data_id:
        payment_id = data_id
    elif topic == "payment" and ipn_id:
        payment_id = ipn_id
    else:
        try:
            body = await request.json()
            if body.get("type") == "payment":
                payment_id = str(body.get("data", {}).get("id", ""))
        except Exception:
            pass

    if payment_id:
        await service.handle_webhook(payment_id)
    return {"ok": True}
