from fastapi import APIRouter

from app.api.v1.endpoints import activities, auth, turnos, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])
api_router.include_router(turnos.router, prefix="/turnos", tags=["turnos"])
