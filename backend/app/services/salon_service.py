from __future__ import annotations

from fastapi import HTTPException, status

from app.domain.salon import Salon
from app.repositories.salon_repository import AbstractSalonRepository


class SalonService:

    def __init__(self, salon_repo: AbstractSalonRepository):
        self._salon_repo = salon_repo

    async def list(self) -> list[Salon]:
        return await self._salon_repo.list_active()

    async def list_all(self) -> list[Salon]:
        return await self._salon_repo.list_all()

    async def create(self, name: str, capacity: int) -> Salon:
        if await self._salon_repo.get_active_by_name(name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un salón activo con ese nombre.",
            )
        return await self._salon_repo.create(name, capacity)

    async def update(self, salon_id: int, name: str, capacity: int) -> Salon:
        salon = await self._salon_repo.get_by_id(salon_id)
        if not salon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salón no encontrado.")

        if name != salon.name:
            existing = await self._salon_repo.get_active_by_name(name)
            if existing and existing.id != salon_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un salón activo con ese nombre.",
                )

        return await self._salon_repo.update(salon_id, name, capacity)
