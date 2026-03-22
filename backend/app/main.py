from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import get_db
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,  # ocultar docs en prod
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unreachable"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
    }
