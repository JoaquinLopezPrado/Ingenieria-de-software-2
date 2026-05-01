from fastapi import APIRouter, Depends

from app.api.v1.docs.user_responses import ME_RESPONSES
from app.core.dependencies import get_current_user_id

router = APIRouter()


@router.get("/me", responses=ME_RESPONSES)
async def me(user_id: int = Depends(get_current_user_id)):
    return {"user_id": user_id}