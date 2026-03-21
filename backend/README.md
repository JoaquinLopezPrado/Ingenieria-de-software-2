# Backend

Este directorio contiene el código del servidor y la lógica de negocio del proyecto.

---

## Requisitos previos

Tener [uv](https://docs.astral.sh/uv/) instalado en el sistema. Es la única dependencia externa necesaria — uv se encarga de instalar Python y las dependencias del proyecto automáticamente.

### Instalar uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> Verificá que esté disponible ejecutando `uv --version`.

---

## Configuración del entorno

Una vez instalado uv, desde la carpeta `backend/` ejecutá:

```bash
uv sync
```

Esto se encarga de todo:
1. Descarga e instala Python 3.13.9 si no está en el sistema
2. Crea el entorno virtual en `.venv/`
3. Instala todas las dependencias definidas en `pyproject.toml`

---

## Activar el entorno virtual

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

Para salir del entorno: `deactivate`.

---

## Notas

- El directorio `.venv/` está incluido en el `.gitignore` y no se versiona.
- Si se agregan nuevas dependencias al `pyproject.toml`, volvé a correr `uv sync` para actualizar tu entorno.