from app.domain.single_enrollment import MySingleEnrollment, SingleEnrollment
from app.repositories.single_enrollment_repository import AbstractSingleEnrollmentRepository


class SingleEnrollmentService:

    def __init__(self, single_repo: AbstractSingleEnrollmentRepository):
        self._repo = single_repo

    async def create_single(self, clase_ids: list[int], user_id: int, credit_id: int | None = None) -> SingleEnrollment:
        return await self._repo.create_single(clase_ids=clase_ids, user_id=user_id, credit_id=credit_id)

    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        return await self._repo.get_single_by_user(user_id=user_id)

    async def cancel_enrollment(self, enrollment_id: int, user_id: int) -> None:
        await self._repo.cancel_pending(enrollment_id=enrollment_id, user_id=user_id)
