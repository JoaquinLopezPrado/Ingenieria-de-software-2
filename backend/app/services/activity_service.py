from fastapi import HTTPException, status

from app.domain.activity import Activity
from app.repositories.activity_repository import AbstractActivityRepository


class ActivityService:

    def __init__(self, activity_repo: AbstractActivityRepository):
        self._activity_repo = activity_repo

    async def list(self) -> list[Activity]:
        return await self._activity_repo.list_active()

    async def list_all(self) -> list[Activity]:
        return await self._activity_repo.list_all()

    async def create(self, name: str, description: str) -> Activity:
        if await self._activity_repo.get_active_by_name(name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una actividad activa con ese nombre.",
            )
        return await self._activity_repo.create(name, description)
