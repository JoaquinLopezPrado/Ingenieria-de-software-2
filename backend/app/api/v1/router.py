from fastapi import APIRouter

from app.api.v1.endpoints import activities, auth, enrollments, payments, turnos, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(turnos.router, prefix="/turnos", tags=["turnos"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
