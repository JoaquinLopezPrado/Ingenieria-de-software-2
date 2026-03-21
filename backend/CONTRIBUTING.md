# 🤝 Guía de Contribución - Proyecto Cursada Inge. 2

Para que no rompamos el código del otro y las entregas sean fluidas, vamos a seguir estas reglas de trabajo en Git.

---

## 🛠 Configuración del Entorno (`uv`)

Usamos **`uv`** para gestionar el proyecto y las dependencias. Nos asegura que todos los del grupo tengamos las mismas versiones de las librerías al instante.

**1. Instalar dependencias (la primera vez o al bajar cambios):**
```bash
uv sync
```

**2. Para correr el proyecto localmente (FastAPI):**
```bash
uv run uvicorn main:app --reload
```

**3. Para instalar una librería nueva (ej. SQLAlchemy):**
```bash
uv add nombre-del-paquete
```
*(⚠️ Ojo: esto modifica `pyproject.toml` y `uv.lock`. Asegurate de commitear ambos archivos).*

**4. Chequeo y formato de código (Ruff):**
Antes de hacer commit, corré:
```bash
uv run ruff format .
uv run ruff check --fix .
```

---

## 🌿 Estructura de Ramas

* **`main`**: Código estable y entregable. Nadie pushea aquí directamente.
* **`develop`**: Rama de integración. Aquí unimos nuestras funcionalidades.
* **`feature/nombre-tarea`**: Ramas temporales para cada funcionalidad (ej: `feature/api-usuarios`).

---

## 🚀 Flujo de Trabajo (Paso a Paso)

### 1. Sincronización Diaria
Antes de empezar a programar, bajar lo último de `develop` y sincronizar dependencias:
```bash
git checkout develop
git pull origin develop
uv sync
```

### 2. Nueva Funcionalidad
Crea tu rama desde `develop`:
```bash
git checkout -b feature/mi-funcionalidad
```

### 3. Mensajes de Commit
Usemos prefijos para que el historial sea legible:
* `feat:` (nueva funcionalidad)
* `fix:` (corrección de un error)
* `docs:` (README o documentación)
* `refactor:` (mejorar código sin cambiar lo que hace)

*Ejemplo:* `git commit -m "feat: agrega endpoint de consulta de saldo"`

### 4. Pull Request (PR)
1. Subí tu rama: `git push origin feature/mi-funcionalidad`.
2. En GitHub, abrí un **Pull Request** hacia `develop`.
3. **Regla:** Al menos uno debe dar el "Approve" antes del merge.

---

## 📋 Checklist antes del PR
- [ ] ¿El código corre localmente sin errores?
- [ ] ¿Corrí `uv run ruff format .` y `uv run ruff check --fix .`?
- [ ] ¿Commiteé el `pyproject.toml` y el `uv.lock` si agregué librerías nuevas?
- [ ] ¿Seguí el estilo de código acordado?
- [ ] ¿Actualicé el `.env.example` si hay nuevas variables de PostgreSQL u otras?