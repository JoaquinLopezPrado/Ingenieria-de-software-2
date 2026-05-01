from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_id

router = APIRouter()


@router.get("/me")
async def me(user_id: int = Depends(get_current_user_id)):
    return {"user_id": user_id}