from app.domain.enrollment import Enrollment, MyMonthlyEnrollment, MySingleEnrollment
from app.repositories.enrollment_repository import AbstractEnrollmentRepository


class EnrollmentService:

    def __init__(self, enrollment_repo: AbstractEnrollmentRepository):
        self._enrollment_repo = enrollment_repo

    async def create_monthly(self, turno_id: int, user_id: int) -> Enrollment:
        return await self._enrollment_repo.create_monthly(turno_id=turno_id, user_id=user_id)

    async def create_single(self, clase_id: int, user_id: int) -> Enrollment:
        return await self._enrollment_repo.create_single(clase_id=clase_id, user_id=user_id)

    async def get_monthly_by_user(self, user_id: int) -> list[MyMonthlyEnrollment]:
        return await self._enrollment_repo.get_monthly_by_user(user_id=user_id)

    async def get_single_by_user(self, user_id: int) -> list[MySingleEnrollment]:
        return await self._enrollment_repo.get_single_by_user(user_id=user_id)
