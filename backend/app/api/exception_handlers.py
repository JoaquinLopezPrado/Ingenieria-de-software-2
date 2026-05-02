from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

_LOCATION_PREFIXES = {"body", "query", "path", "header"}

_TRANSLATED_MESSAGES = {
    "Not authenticated": "No autenticado.",
    "Method Not Allowed": "Método no permitido.",
    "Not Found": "Recurso no encontrado.",
    "Forbidden": "Acceso denegado.",
}

_TRANSLATED_VALIDATION_MESSAGES = {
    "Field required": "Este campo es requerido.",
    "Value error": "Valor inválido.",
    "value is not a valid email address": "El email no es válido.",
}


def _extract_field(loc: tuple) -> str:
    parts = [p for p in loc if p not in _LOCATION_PREFIXES]
    return str(parts[0]) if parts else "general"


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    validation_error = exc if isinstance(exc, RequestValidationError) else RequestValidationError([])
    errors: dict[str, str] = {}
    for error in validation_error.errors():
        field = _extract_field(error.get("loc", ()))
        if field not in errors:
            raw = str(error.get("ctx", {}).get("error") or error.get("msg", "Error de validación."))
            base = raw.split(":")[0].strip()
            message = _TRANSLATED_VALIDATION_MESSAGES.get(raw) or _TRANSLATED_VALIDATION_MESSAGES.get(base, raw)
            errors[field] = message
    return JSONResponse(
        status_code=422,
        content={"errors": errors},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    http_exc = exc if isinstance(exc, HTTPException) else HTTPException(status_code=500)
    message = _TRANSLATED_MESSAGES.get(http_exc.detail, http_exc.detail)
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"errors": {"general": message}},
    )
