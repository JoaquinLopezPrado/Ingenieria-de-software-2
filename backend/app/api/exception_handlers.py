from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_LOCATION_PREFIXES = {"body", "query", "path", "header"}


def _extract_field(loc: tuple) -> str:
    parts = [p for p in loc if p not in _LOCATION_PREFIXES]
    return str(parts[0]) if parts else "general"


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = exc if isinstance(exc, RequestValidationError) else RequestValidationError([])
    errors: dict[str, str] = {}
    for error in validation_error.errors():
        field = _extract_field(error.get("loc", ()))
        if field not in errors:
            message = error.get("ctx", {}).get("error") or error.get("msg", "Error de validación.")
            errors[field] = str(message)
    return JSONResponse(
        status_code=422,
        content={"errors": errors},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = exc if isinstance(exc, HTTPException) else HTTPException(status_code=500)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"errors": {"general": http_exc.detail}},
    )
