from __future__ import annotations

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

    async def update(self, activity_id: int, name: str, description: str) -> Activity:
        activity = await self._activity_repo.get_by_id(activity_id)
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actividad no encontrada.")

        if name != activity.name:
            existing = await self._activity_repo.get_active_by_name(name)
            if existing and existing.id != activity_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una actividad activa con ese nombre.",
                )

        return await self._activity_repo.update(activity_id, name, description)
