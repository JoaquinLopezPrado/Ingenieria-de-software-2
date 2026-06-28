import asyncio

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_roles
from app.core.tasks import promote_freed_turnos
from app.domain.user import User
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.waitlist_repository import WaitlistRepository
from app.schemas.subscription import (
    CancelSubscriptionsRequest,
    CreateSubscriptionRequest,
    JoinWaitlistRequest,
    MySubscriptionResponse,
    OverdueSubscriptionResponse,
    PaidChargeResponse,
    PendingChargeResponse,
    SubscriptionChargeResponse,
    WaitlistEntryResponse,
)
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService
from app.services.waitlist_service import WaitlistService

router = APIRouter()


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(subscription_repo=SubscriptionRepository(db))


def get_waitlist_service(db: AsyncSession = Depends(get_db)) -> WaitlistService:
    sub_service = SubscriptionService(subscription_repo=SubscriptionRepository(db))
    return WaitlistService(
        waitlist_repo=WaitlistRepository(db),
        subscription_service=sub_service,
        email_service=EmailService(),
    )


@router.post("", response_model=SubscriptionChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    charge = await service.create(turno_id=body.turno_id, user_id=current_user.id)
    return SubscriptionChargeResponse.from_charge(charge)


@router.get("/me", response_model=list[MySubscriptionResponse], status_code=status.HTTP_200_OK)
async def list_my_subscriptions(
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    items = await service.get_subscriptions_by_user(user_id=current_user.id)
    return [_to_response(item) for item in items]


@router.get("/me/charges", response_model=list[PaidChargeResponse], status_code=status.HTTP_200_OK)
async def list_my_paid_charges(
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
):
    return await service.get_paid_charges(user_id=current_user.id)


@router.get("/user/{user_id}", response_model=list[MySubscriptionResponse], status_code=status.HTTP_200_OK)
async def list_subscriptions_by_user(
    user_id: int,
    _=require_roles("admin", "empleado"),
    service: SubscriptionService = Depends(get_subscription_service),
):
    items = await service.get_subscriptions_by_user(user_id=user_id)
    return [_to_response(item) for item in items]


@router.get("/overdue", response_model=list[OverdueSubscriptionResponse], status_code=status.HTTP_200_OK)
async def list_overdue_subscriptions(
    min_unpaid: int = 2,
    _=require_roles("admin", "empleado"),
    service: SubscriptionService = Depends(get_subscription_service),
):
    return await service.get_overdue(min_unpaid=min_unpaid)


@router.post("/cancel-overdue", status_code=status.HTTP_200_OK)
async def cancel_overdue_subscriptions(
    body: CancelSubscriptionsRequest,
    _=require_roles("admin"),
    service: SubscriptionService = Depends(get_subscription_service),
    db: AsyncSession = Depends(get_db),
):
    freed_turno_ids = await service.admin_cancel(subscription_ids=body.subscription_ids)
    if freed_turno_ids:
        await db.commit()
        asyncio.create_task(promote_freed_turnos(freed_turno_ids))
    return {"cancelled": len(freed_turno_ids)}


@router.post("/{subscription_id}/cancel", status_code=status.HTTP_200_OK)
async def unsubscribe(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
    db: AsyncSession = Depends(get_db),
):
    """Baja voluntaria de un abonado activo: efectiva al fin del período pagado."""
    ends_on, turno_id = await service.unsubscribe(subscription_id=subscription_id, user_id=current_user.id)
    await db.commit()
    asyncio.create_task(promote_freed_turnos([turno_id]))
    return {"ends_on": ends_on.isoformat()}


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service),
    db: AsyncSession = Depends(get_db),
):
    freed_turno_id = await service.cancel(subscription_id=subscription_id, user_id=current_user.id)
    if freed_turno_id is not None:
        await db.commit()
        asyncio.create_task(promote_freed_turnos([freed_turno_id]))


@router.post("/waitlist", response_model=WaitlistEntryResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    body: JoinWaitlistRequest,
    current_user: User = Depends(get_current_user),
    service: WaitlistService = Depends(get_waitlist_service),
):
    """Anotarse en la lista de espera para un turno."""
    entry = await service.join(turno_id=body.turno_id, user_id=current_user.id)
    return WaitlistEntryResponse(
        entry_id=entry.id,
        turno_id=entry.turno_id,
        turno_description="",
        activity_name="",
        instructor="",
        start_time=entry.joined_at.time(),
        end_time=entry.joined_at.time(),
        days=[],
        joined_at=entry.joined_at,
        status=entry.status,
    )


@router.get("/waitlist/me", response_model=list[WaitlistEntryResponse], status_code=status.HTTP_200_OK)
async def list_my_waitlist(
    current_user: User = Depends(get_current_user),
    service: WaitlistService = Depends(get_waitlist_service),
):
    """Lista las entradas activas del usuario en listas de espera."""
    items = await service.get_by_user(user_id=current_user.id)
    return [
        WaitlistEntryResponse(
            entry_id=item.entry_id,
            turno_id=item.turno_id,
            turno_description=item.turno_description,
            activity_name=item.activity_name,
            instructor=item.instructor,
            start_time=item.start_time,
            end_time=item.end_time,
            days=item.days,
            joined_at=item.joined_at,
            status=item.status,
        )
        for item in items
    ]


@router.delete("/waitlist/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_waitlist(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    service: WaitlistService = Depends(get_waitlist_service),
):
    """Salir de la lista de espera."""
    await service.leave(entry_id=entry_id, user_id=current_user.id)


def _to_response(item) -> MySubscriptionResponse:
    pending = None
    if item.pending_charge is not None:
        c = item.pending_charge
        pending = PendingChargeResponse(
            charge_id=c.id,
            period_month=c.period_month,
            period_year=c.period_year,
            amount=c.amount,
            original_amount=c.original_amount,
            status=c.status,
            due_date=c.due_date,
            expires_at=c.expires_at,
        )
    return MySubscriptionResponse(
        subscription_id=item.subscription_id,
        status=item.status,
        start_date=item.start_date,
        ends_on=item.ends_on,
        turno_id=item.turno_id,
        turno_description=item.turno_description,
        start_time=item.start_time,
        end_time=item.end_time,
        instructor=item.instructor,
        activity_name=item.activity_name,
        days=item.days,
        pending_charge=pending,
    )
