from fastapi import APIRouter

from app.api.v1.endpoints import (
    activities,
    attendances,
    auth,
    clases,
    payments,
    reports,
    single_enrollments,
    subscriptions,
    turnos,
    two_factor,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(two_factor.router, prefix="/auth/2fa", tags=["2fa"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(turnos.router, prefix="/turnos", tags=["turnos"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(single_enrollments.router, prefix="/single-enrollments", tags=["single-enrollments"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(attendances.router, prefix="/attendances", tags=["attendances"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(clases.router, prefix="/clases", tags=["clases"])
