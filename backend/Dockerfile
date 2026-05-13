FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Copiamos solo los archivos de dependencias
COPY pyproject.toml uv.lock ./

# 2. Sincronizamos TODO (incluyendo dev dependencies)
# Uso --no-install-project para que esta capa se cachee 
# si no cambio el pyproject.toml
RUN uv sync --frozen --no-install-project

# 3. Copiamos el código fuente
COPY . .

#CMD ["uv", "run", "alembic", "upgrade", "head", "&&", "uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
CMD ["/bin/sh", "-c", "uv run alembic upgrade head && uv run python -m app.seeds && uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"]