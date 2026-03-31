# Makefile

# Levantar todo
up:
	docker compose up -d

# Bajar todo
down:
	docker compose down

# Comando mágico para crear migraciones.
# Uso: make makemigrations m="Mensaje de la migracion"
makemigrations:
	docker compose exec backend uv run alembic revision --autogenerate -m "$(m)"

# Comando para aplicar las migraciones manualmente si lo necesitas
migrate:
	docker compose exec backend uv run alembic upgrade head
