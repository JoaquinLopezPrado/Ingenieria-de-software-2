from fastapi import FastAPI, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import get_db
from app.api.v1.router import api_router
from app.api.exception_handlers import http_exception_handler, validation_exception_handler

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.short_sha,
        "docs": "/docs",
    }


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        # Verificamos conexión a PostgreSQL (que ya tenés configurado)
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unreachable"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": db_status,
        "version": {
            "sha_short": settings.short_sha,
            "sha_full": settings.render_git_commit,
            "branch": settings.render_git_branch,
            "deployed_at": settings.deploy_timestamp,
        },
    }
