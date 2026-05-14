# CLAUDE.md — Contexto del proyecto para sesiones de Claude

Este archivo es de uso personal/local. No se sube al repositorio (.gitignore).

---

## Feature implementada: ACT-06.01 — Programar nuevos turnos

**Historia de usuario:**
Como administrador quiero definir días, horarios y cupo máximo para las clases
de una actividad, para organizar la grilla del centro y habilitar la disponibilidad
de reservas para los socios.

**Estado actual:** Frontend completo e integrado con el backend real.

**Reglas de negocio implementadas en el frontend:**
- Actividad debe existir (select cargado desde `GET /api/v1/activities`)
- Día válido de la semana (Lunes a Sábado, pills de selección múltiple)
- Hora de inicio y fin en formato HH:mm con saltos de 15 minutos
- Hora de inicio estrictamente anterior a la hora de fin
- Cupo máximo: número entero mayor a 0
- Mes y año seleccionables por el admin (default: período actual)
- `is_active` = false por defecto (el admin lo activa manualmente luego)

---

## Mapa de archivos

### Frontend (`frontend/src/`)

| Archivo | Rol |
|---------|-----|
| `components/activities/SessionForm.vue` | Formulario completo con validaciones, campos de tiempo, toggle is_active |
| `views/activities/ScheduleSessionView.vue` | Vista que orquesta el form, maneja banners éxito/error |
| `services/sessionService.ts` | Capa HTTP: `getFormOptions()` y `createSession()`, mapeos camelCase↔snake_case |
| `services/api.ts` | Instancia axios con baseURL desde `VITE_API_URL` e interceptor JWT |
| `components/layout/AdminLayout.vue` | Sidebar fijo con RouterLink y active-class automático |
| `assets/main.css` | Reset global: quita max-width y grid de 2 col que traía el scaffold de Vue |
| `docs/integracion-backend.md` | Guía de integración: contratos, pendientes, checklist |

### Backend (`backend/app/`) — referencia

| Archivo | Rol |
|---------|-----|
| `api/v1/endpoints/activities.py` | `GET /activities` — lista actividades (requiere cualquier rol) |
| `api/v1/endpoints/turnos.py` | `POST /turnos` — crea turno (requiere rol admin) |
| `schemas/activity.py` | `ActivityResponse`: `{ id, name, instructor, is_active }` |
| `schemas/turno.py` | `CreateTurnoRequest` — campo `is_active` pendiente de agregar |
| `core/dependencies.py` | Guards: `get_current_user()` y `require_admin()` / `require_roles()` |
| `api/exception_handlers.py` | Formato de errores: `{ errors: { general: "..." } }` |

---

## Decisiones arquitectónicas

### 1. Validación solo en el frontend (por ahora)
El backend ya valida con Pydantic, pero duplicamos las validaciones críticas en
`SessionForm.vue` para dar feedback inmediato sin round-trip al servidor.
Los mensajes de error coinciden exactamente con los Criterios de Aceptación del spec.

### 2. Mapeo de datos en el servicio, no en el componente
`SessionForm.vue` trabaja con nombres display ("Lunes", camelCase).
`sessionService.ts` hace todas las transformaciones antes de llamar a la API:
- `"Lunes"` → `"lunes"` via `DAY_TO_BACKEND`
- `startTime` → `start_time` (snake_case)
- `maxCapacity` → `capacity`

El componente nunca sabe cómo habla el backend.

### 3. Errores del servidor en la vista, no en el servicio
`createSession()` deja que axios propague la excepción.
`ScheduleSessionView.vue` la captura y muestra el banner rojo.
`extractBackendError()` en el servicio lee `error.response.data.errors`.

### 4. TIME_SLOTS como array estático (IIFE)
Los slots de 15 minutos (06:00–23:45) se generan una sola vez al cargar el módulo,
no en cada render. El selector de fin (`endTimeSlots`) es un `computed` que filtra
ese array según el inicio elegido.

### 5. `is_active` = false por defecto
El turno se crea inactivo. El admin lo activa por separado cuando confirma que el
turno se dictará. El frontend ya envía el campo en el payload; el backend lo ignora
hasta que el compañero lo agregue a `CreateTurnoRequest` (ver pendientes abajo).

### 6. Layout full-screen
El scaffold de Vue CLI ponía `max-width: 1280px` y un `display: grid` de 2 columnas
en `#app` dentro de `main.css`. Se reemplazó por `width: 100%; display: block`.
El sidebar usa `position: fixed` + `margin-left: 260px` en el main.

---

## Convenciones de código

### Vue / TypeScript
- **Composition API** con `<script setup lang="ts">` en todos los componentes
- **`const` → `ref` / `computed`** para estado reactivo, nunca `data()`
- **Orden en `<script setup>`:** imports → defineProps/Emits → constantes estáticas →
  refs → computed y watch (SIEMPRE después de los refs que usan) → onMounted → funciones
- **Nombrado:** `camelCase` para variables/funciones, `UPPER_SNAKE_CASE` para constantes
  de módulo (`TIME_SLOTS`, `DAY_TO_BACKEND`, `MONTHS`)

### ⚠ Regla crítica — Temporal Dead Zone (TDZ)
`computed` y `watch` que referencian un `ref` deben declararse **DESPUÉS** de ese `ref`.
Si van antes, Vue lanza `ReferenceError: Cannot access 'X' before initialization`
y el componente no monta (pantalla en blanco).

```ts
// ❌ MAL — endTimeSlots usa `form` antes de que exista
const endTimeSlots = computed(() => form.value.startTime ...)
const form = ref({ startTime: '' })

// ✅ BIEN
const form = ref({ startTime: '' })
const endTimeSlots = computed(() => form.value.startTime ...)
```

### Estilos CSS
- **Scoped** en todos los componentes (`<style scoped>`)
- **Mobile-first:** grillas con `grid-template-columns: 1fr` base,
  breakpoints en `640px` (tablet) y `1024px` (desktop)
- **Paleta:** `#11998e` (teal primario), `#0c8a70` (hover), `#0d3027` (sidebar)
- **Errores:** borde rojo `#ef4444` + fondo `#fff5f5` en el input, texto `#dc2626` debajo

### Mensajes de UI
- Todo el texto visible al usuario en **español rioplatense** (vos, seleccioná, ingresá)
- Mensajes de error deben coincidir con los **Criterios de Aceptación del spec**
- No usar `alert()` — siempre banners con `<transition name="fade">`

### HTTP / Servicios
- Un único cliente axios en `api.ts` — nunca crear instancias nuevas en los servicios
- El token JWT se guarda en `localStorage` bajo la clave `"token"`
- Formato de error del backend: `{ errors: { general: "msg" } }` — usar `extractBackendError()`

---

## Pendientes con el compañero de backend

- [ ] Agregar `is_active: bool = False` a `CreateTurnoRequest` en `schemas/turno.py`
- [ ] Pasar `is_active` al service y al repositorio (hoy está hardcodeado en `True`)
- [ ] Verificar que el check de duplicados en `turno_service.py` considere turnos inactivos

---

## Infraestructura local

| Servicio | Puerto | Cómo levantar |
|----------|--------|---------------|
| Frontend (Vite) | 5173 | `docker compose up frontend` |
| Backend (FastAPI) | 8000 | `docker compose up backend` |
| Base de datos (Postgres) | 5442 | `docker compose up db` |
| Todo | — | `docker compose up` |

**Si el frontend no refleja cambios:**
```bash
# 1. Eliminar caché de Vite dentro del contenedor
docker compose up --build frontend

# 2. Si persiste, borrar caché local también
rm -rf frontend/node_modules/.vite
docker compose up --build frontend
```

**Variable de entorno clave del frontend:** `VITE_API_URL=http://localhost:8000/api/v1`
(definida en `frontend/.env.local`, ignorada por git)
