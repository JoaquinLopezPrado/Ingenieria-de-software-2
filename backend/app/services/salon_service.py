from __future__ import annotations

from fastapi import HTTPException, status

from app.domain.salon import Salon
from app.repositories.activity_repository import AbstractActivityRepository
from app.repositories.salon_repository import AbstractSalonRepository
from app.repositories.turno_repository import AbstractTurnoRepository


class SalonService:

    def __init__(
        self,
        salon_repo: AbstractSalonRepository,
        turno_repo: AbstractTurnoRepository,
        activity_repo: AbstractActivityRepository,
    ):
        self._salon_repo = salon_repo
        self._turno_repo = turno_repo
        self._activity_repo = activity_repo

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

        if capacity != salon.capacity:
            conflict = await self._turno_repo.get_first_exceeding_capacity(salon_id, capacity)
            if conflict:
                activity = await self._activity_repo.get_by_id(conflict.activity_id)
                activity_name = activity.name if activity else "Actividad desconocida"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"No se puede reducir la capacidad a {capacity}: el turno "
                        f"«{activity_name} – {conflict.description}» tiene un cupo de {conflict.capacity}."
                    ),
                )

        return await self._salon_repo.update(salon_id, name, capacity)
