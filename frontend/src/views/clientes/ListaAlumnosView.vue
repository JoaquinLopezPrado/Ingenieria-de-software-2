<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { listClientes, type Cliente } from '@/services/clientesService'
import { extractBackendError } from '@/services/sessionService'
import { useInscripcionStore } from '@/stores/inscripcionStore'

const router = useRouter()
const inscripcionStore = useInscripcionStore()

function inscribirATurno(cliente: Cliente) {
  router.push({ name: 'clientes-inscripciones-turnos', params: { clienteId: cliente.id } })
}

function inscribirAClase(cliente: Cliente) {
  inscripcionStore.setCliente({
    id: cliente.id,
    first_name: cliente.first_name,
    last_name: cliente.last_name,
    email: cliente.email,
    phone: cliente.phone,
    doc_number: cliente.doc_number,
    doc_type_name: cliente.doc_type_name as 'DNI' | 'PASAPORTE',
  })
  router.push({ name: 'inscripciones-clases' })
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const PAGE_SIZE = 10

// ─── Estado ──────────────────────────────────────────────────────────────────

const searchQuery  = ref('')
const clientes     = ref<Cliente[]>([])
const total        = ref(0)
const currentPage  = ref(1)
const totalPages   = ref(1)
const isLoading    = ref(true)
const errorMessage = ref('')

// ─── Carga ────────────────────────────────────────────────────────────────────

async function cargarClientes() {
  isLoading.value  = true
  errorMessage.value = ''

  try {
    const result = await listClientes({
      q: searchQuery.value.trim() || undefined,
      page: currentPage.value,
      page_size: PAGE_SIZE,
    })

    clientes.value    = result.items
    total.value       = result.total
    totalPages.value  = result.total_pages
  } catch (err) {
    errorMessage.value = extractBackendError(err) ?? 'No se pudo cargar el listado de clientes.'
    clientes.value = []
    total.value    = 0
  } finally {
    isLoading.value = false
  }
}

// ─── Debounce de búsqueda ─────────────────────────────────────────────────────

let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer)

  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    cargarClientes()
  }, 350)
})

watch(currentPage, () => {
  cargarClientes()
})

onMounted(() => cargarClientes())

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})

// ─── Paginación ───────────────────────────────────────────────────────────────

const paginationRange = computed((): (number | '...')[] => {
  const total = totalPages.value
  const cur   = currentPage.value

  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  if (cur <= 4) return [1, 2, 3, 4, 5, '...', total]
  if (cur >= total - 3) return [1, '...', total - 4, total - 3, total - 2, total - 1, total]

  return [1, '...', cur - 1, cur, cur + 1, '...', total]
})

const showingFrom = computed(() =>
  clientes.value.length === 0 ? 0 : (currentPage.value - 1) * PAGE_SIZE + 1,
)

const showingTo = computed(() =>
  (currentPage.value - 1) * PAGE_SIZE + clientes.value.length,
)

function goToPage(page: number | '...') {
  if (typeof page === 'number') currentPage.value = page
}

// ─── Navegación ───────────────────────────────────────────────────────────────

function irARegistrarCliente() {
  router.push({ name: 'registrar-cliente-admin' })
}

// ─── Flags de UI ──────────────────────────────────────────────────────────────

const isEmpty = computed(() =>
  !isLoading.value &&
  !errorMessage.value &&
  total.value === 0 &&
  !searchQuery.value.trim(),
)

const noResults = computed(() =>
  !isLoading.value &&
  !errorMessage.value &&
  total.value === 0 &&
  !!searchQuery.value.trim(),
)

const hasData = computed(() =>
  !isLoading.value &&
  !errorMessage.value &&
  clientes.value.length > 0,
)
</script>

<template>
  <AdminLayout>
    <div class="page-wrapper">

      <!-- ── Encabezado ── -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Clientes</h1>
          <p class="page-subtitle">Listado de clientes registrados en el sistema</p>
        </div>
      </div>

      <!-- ── Buscador ── -->
      <div v-if="!errorMessage" class="search-card">
        <div class="search-input-wrapper">
          <span class="search-icon" aria-hidden="true">⌕</span>

          <input
            v-model="searchQuery"
            type="search"
            class="search-input"
            placeholder="Buscar por nombre, apellido o documento..."
            autocomplete="off"
            aria-label="Buscar clientes"
          />

          <button
            v-if="searchQuery"
            type="button"
            class="search-clear"
            aria-label="Limpiar búsqueda"
            @click="searchQuery = ''"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- ── Estado: cargando ── -->
      <div v-if="isLoading" class="skeleton-wrapper" aria-label="Cargando clientes...">
        <div v-for="n in PAGE_SIZE" :key="n" class="skeleton-row" />
      </div>

      <!-- ── Estado: error ── -->
      <div v-else-if="errorMessage" class="state-card state-error">
        <div class="state-icon">⚠</div>
        <h2 class="state-title">Error al cargar los clientes</h2>
        <p class="state-desc">{{ errorMessage }}</p>

        <button class="btn-secondary" type="button" @click="cargarClientes">
          Reintentar
        </button>
      </div>

      <!-- ── Estado: sin clientes en el sistema ── -->
      <div v-else-if="isEmpty" class="state-card state-empty">
        <div class="state-icon">◎</div>
        <h2 class="state-title">Sin clientes registrados</h2>
        <p class="state-desc">No hay clientes registrados en el sistema.</p>
      </div>

      <!-- ── Estado: búsqueda sin resultados ── -->
      <div v-else-if="noResults" class="state-card state-empty">
        <div class="state-icon">⌕</div>
        <h2 class="state-title">Sin resultados</h2>
        <p class="state-desc">No se encontraron clientes que coincidan con la búsqueda.</p>
        <button class="btn-secondary" type="button" @click="searchQuery = ''">
          Limpiar búsqueda
        </button>
      </div>

      <!-- ── Tabla de clientes ── -->
      <div v-else-if="hasData" class="table-container">
        <div class="table-scroll">
          <table class="clientes-table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Documento</th>
                <th>Email</th>
                <th>Teléfono</th>
                <th>Acciones</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="cliente in clientes"
                :key="cliente.id"
                class="row-clickable"
                @click="router.push({ name: 'ficha-cliente', params: { clienteId: cliente.id } })"
              >
                <td class="cell-nombre">
                  {{ cliente.first_name }} {{ cliente.last_name }}
                </td>

                <td class="cell-doc">
                  <span class="doc-type">{{ cliente.doc_type_name }}</span>
                  {{ cliente.doc_number }}
                </td>

                <td class="cell-email">
                  {{ cliente.email }}
                </td>

                <td class="cell-phone">
                  {{ cliente.phone }}
                </td>

                <td class="cell-actions" @click.stop>
                  <button type="button" class="btn-accion btn-inscribir-turno" @click.stop="inscribirATurno(cliente)">
                    Inscribir a Turno
                  </button>
                  <button type="button" class="btn-accion btn-inscribir-clase" @click.stop="inscribirAClase(cliente)">
                    Inscribir a clase
                  </button>
                  <RouterLink
                    :to="{ name: 'ficha-cliente', params: { clienteId: cliente.id } }"
                    class="btn-accion btn-ver-ficha"
                  >
                    Ver ficha
                  </RouterLink>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ── Footer: conteo + paginación ── -->
        <div class="table-footer">
          <span class="table-count">
            Mostrando {{ showingFrom }}–{{ showingTo }} de
            {{ total }} cliente{{ total !== 1 ? 's' : '' }}
          </span>

          <div v-if="totalPages > 1" class="pagination">
            <button
              class="page-btn"
              :disabled="currentPage === 1"
              aria-label="Página anterior"
              @click="currentPage--"
            >
              ←
            </button>

            <button
              v-for="(page, idx) in paginationRange"
              :key="idx"
              :class="[
                'page-btn',
                {
                  'page-btn-active': page === currentPage,
                  'page-btn-dots': page === '...',
                },
              ]"
              :disabled="page === '...'"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>

            <button
              class="page-btn"
              :disabled="currentPage === totalPages"
              aria-label="Página siguiente"
              @click="currentPage++"
            >
              →
            </button>
          </div>
        </div>
      </div>

      <!-- ── Botón registrar cliente ── -->
      <div class="register-client-footer">
        <button
          type="button"
          class="btn-register-client"
          @click="irARegistrarCliente"
        >
          Registrar cliente
        </button>
      </div>

    </div>
  </AdminLayout>
</template>

<style scoped>
.page-wrapper {
  width: 100%;
}

/* ── Encabezado ── */

.page-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  color: #6b7280;
  font-size: 0.88rem;
  margin: 0;
}

/* ── Buscador ── */

.search-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 0.85rem 1.25rem;
  margin-bottom: 1.25rem;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.85rem;
  font-size: 1.1rem;
  color: #9ca3af;
  pointer-events: none;
  line-height: 1;
}

.search-input {
  width: 100%;
  max-width: 480px;
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 2.25rem 0 2.5rem;
  font-size: 0.9rem;
  color: #374151;
  background: white;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.search-input:focus {
  border-color: #11998e;
  box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.12);
}

.search-input::-webkit-search-cancel-button {
  display: none;
}

.search-clear {
  position: absolute;
  left: 456px;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1;
  padding: 0.25rem;
  transition: color 0.12s;
}

.search-clear:hover {
  color: #6b7280;
}

/* ── Skeleton ── */

.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-row {
  height: 52px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

/* ── Estados ── */

.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
}

.state-empty {
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
}

.state-error {
  background-color: #fff5f5;
  border: 1px solid #fecaca;
}

.state-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.state-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.state-desc {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  max-width: 380px;
}

.state-error .state-title,
.state-error .state-desc {
  color: #991b1b;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  background-color: #f3f4f6;
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.15s;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

/* ── Tabla ── */

.table-container {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.clientes-table {
  width: 100%;
  min-width: 820px;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.clientes-table thead {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.clientes-table th {
  padding: 0.85rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.clientes-table td {
  padding: 0.9rem 1rem;
  color: #374151;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

.clientes-table tbody tr:last-child td {
  border-bottom: none;
}

.row-clickable {
  cursor: pointer;
  transition: background-color 0.12s;
}

.row-clickable:hover td {
  background-color: #f0fdf9;
}

.cell-nombre {
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
}

.cell-doc {
  white-space: nowrap;
  color: #374151;
}

.doc-type {
  display: inline-block;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  margin-right: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  vertical-align: middle;
}

.cell-email {
  color: #6b7280;
  font-size: 0.85rem;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-phone {
  color: #6b7280;
  font-size: 0.85rem;
  white-space: nowrap;
}

.cell-actions {
  white-space: nowrap;
  text-align: right;
}

.btn-accion {
  display: inline-flex;
  align-items: center;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.3rem 0.75rem;
  white-space: nowrap;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.12s, border-color 0.12s;
  margin-left: 0.35rem;
}

.btn-accion:first-child {
  margin-left: 0;
}

.btn-accion:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-inscribir-turno {
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.btn-inscribir-turno:hover:not(:disabled) {
  background-color: #dbeafe;
  border-color: #93c5fd;
}

.btn-inscribir-clase {
  background-color: #faf5ff;
  color: #7c3aed;
  border: 1px solid #ddd6fe;
}

.btn-inscribir-clase:hover:not(:disabled) {
  background-color: #ede9fe;
  border-color: #c4b5fd;
}

.btn-ver-ficha {
  background-color: #f0fdf9;
  color: #0d9b8a;
  border: 1px solid #a7f3d0;
}

.btn-ver-ficha:hover {
  background-color: #d1fae5;
  border-color: #6ee7b7;
}

/* ── Footer tabla ── */

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #f3f4f6;
  flex-wrap: wrap;
}

.table-count {
  font-size: 0.8rem;
  color: #9ca3af;
}

/* ── Paginación ── */

.pagination {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.page-btn {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #374151;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  min-width: 2rem;
  padding: 0.3rem 0.5rem;
  transition: background-color 0.12s, border-color 0.12s, color 0.12s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
  border-color: #d1d5db;
}

.page-btn:disabled {
  cursor: default;
  opacity: 0.4;
}

.page-btn-active {
  background-color: #11998e;
  border-color: #11998e;
  color: white;
  font-weight: 700;
}

.page-btn-active:hover:not(:disabled) {
  background-color: #0c8a70;
}

.page-btn-dots {
  border-color: transparent;
  cursor: default;
}

/* ── Registrar cliente ── */

.register-client-footer {
  display: flex;
  justify-content: flex-start;
  margin-top: 1.5rem;
}

.btn-register-client {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #11998e;
  color: white;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 0.75rem 1.4rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.15s, transform 0.12s;
}

.btn-register-client:hover {
  background-color: #0c8a70;
  transform: translateY(-1px);
}

.btn-register-client:active {
  transform: translateY(0);
}

/* ── Responsivo ── */

@media (max-width: 640px) {
  .search-input {
    max-width: 100%;
  }

  .search-clear {
    left: unset;
    right: 0.5rem;
  }

  .clientes-table th,
  .clientes-table td {
    padding: 0.7rem 0.6rem;
  }

  .table-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .register-client-footer {
    justify-content: stretch;
  }

  .btn-register-client {
    width: 100%;
  }
}
</style>