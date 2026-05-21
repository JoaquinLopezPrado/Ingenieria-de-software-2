from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.domain.user import User
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.payment import CreatePreferenceRequest, PreferenceResponse
from app.services.payment_service import PaymentService

router = APIRouter()


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(
        enrollment_repo=EnrollmentRepository(db),
        user_repo=UserRepository(db),
    )


@router.post(
    "/preference",
    response_model=PreferenceResponse,
    status_code=status.HTTP_200_OK,
)
async def create_preference(
    body: CreatePreferenceRequest,
    current_user: User = Depends(get_current_user),
    service: PaymentService = Depends(get_payment_service),
):
    init_point = await service.create_preference(
        enrollment_id=body.enrollment_id,
        user_id=current_user.id,
    )
    return PreferenceResponse(init_point=init_point)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    # Formato nuevo: ?data.id=XXX&type=payment
    data_id: str | None = Query(default=None, alias="data.id"),
    notification_type: str | None = Query(default=None, alias="type"),
    # Formato IPN: ?id=XXX&topic=payment
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
        # Intenta leer del body JSON si no vienen query params
        try:
            body = await request.json()
            if body.get("type") == "payment":
                payment_id = str(body.get("data", {}).get("id", ""))
        except Exception:
            pass

    if payment_id:
        await service.handle_webhook(payment_id)

    return {"ok": True}
