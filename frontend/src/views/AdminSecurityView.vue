<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const TWO_FACTOR_STORAGE_KEY = 'admin-two-factor-enabled'

const twoFactorEnabled = ref(false)

const readStoredTwoFactor = () => {
  if (typeof window === 'undefined') return false

  return localStorage.getItem(TWO_FACTOR_STORAGE_KEY) === 'true'
}

const twoFactorLabel = computed(() => (twoFactorEnabled.value ? 'Habilitado' : 'Deshabilitado'))
const twoFactorDescription = computed(() =>
  twoFactorEnabled.value
    ? 'El acceso de administrador pedira un segundo factor cuando se conecte con el backend.'
    : 'El acceso de administrador seguira funcionando solo con la autenticacion actual.'
)

onMounted(() => {
  twoFactorEnabled.value = readStoredTwoFactor()
})

watch(twoFactorEnabled, (value: boolean) => {
  if (typeof window === 'undefined') return

  localStorage.setItem(TWO_FACTOR_STORAGE_KEY, String(value))
})
</script>

<template>
  <AdminLayout>
    <section class="admin-security">
      <div class="security-card">
        <p class="eyebrow">Seguridad</p>
        <h1>Configuracion de 2FA</h1>
        <p class="intro">
          Habilita o deshabilita el segundo factor para el panel de administracion.
        </p>

        <div class="toggle-panel">
          <div class="toggle-copy">
            <span class="toggle-title">Estado del 2FA</span>
            <span class="toggle-description">{{ twoFactorDescription }}</span>
          </div>

          <label class="toggle-row">
            <input
              v-model="twoFactorEnabled"
              type="checkbox"
              class="toggle-input"
              aria-label="Habilitar o deshabilitar 2FA"
            />
            <span class="toggle-track" :class="twoFactorEnabled ? 'is-on' : 'is-off'">
              <span class="toggle-thumb"></span>
            </span>
            <span class="toggle-state" :class="twoFactorEnabled ? 'active' : 'inactive'">
              {{ twoFactorLabel }}
            </span>
          </label>
        </div>

    
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.admin-security {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem;
  box-sizing: border-box;
}

.security-card {
  width: min(100%, 540px);
  padding: 2.25rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f7f6 100%);
  box-shadow: 0 18px 40px rgba(13, 48, 39, 0.12);
  border: 1px solid rgba(17, 153, 142, 0.12);
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: #0d9b8a;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #0f172a;
  font-size: clamp(1.8rem, 4vw, 2.5rem);
  line-height: 1.1;
}

.intro {
  margin: 1rem 0 0;
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
}

.toggle-panel {
  margin-top: 1.75rem;
  padding: 1.25rem 1.25rem 1.1rem;
  border-radius: 18px;
  border: 1px solid rgba(17, 153, 142, 0.14);
  background: rgba(255, 255, 255, 0.72);
}

.toggle-copy {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 1rem;
}

.toggle-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.toggle-description {
  color: #64748b;
  font-size: 0.92rem;
  line-height: 1.5;
}

.toggle-row {
  display: inline-flex;
  align-items: center;
  gap: 0.85rem;
  cursor: pointer;
  user-select: none;
}

.toggle-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.toggle-track {
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background-color: #d1d5db;
  padding: 3px;
  box-sizing: border-box;
  transition: background-color 0.2s ease;
}

.toggle-track.is-on {
  background-color: #11998e;
}

.toggle-track.is-off {
  background-color: #cbd5e1;
}

.toggle-thumb {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transform: translateX(0);
  transition: transform 0.2s ease;
}

.toggle-track.is-on .toggle-thumb {
  transform: translateX(22px);
}

.toggle-state {
  font-size: 0.95rem;
  font-weight: 700;
}

.toggle-state.active {
  color: #0c8a70;
}

.toggle-state.inactive {
  color: #64748b;
}

.status-note {
  margin: 1rem 0 0;
  color: #475569;
  font-size: 0.92rem;
}

@media (max-width: 640px) {
  .security-card {
    padding: 1.5rem;
    border-radius: 22px;
  }

  .toggle-panel {
    padding: 1rem;
  }

  .toggle-row {
    align-items: flex-start;
  }
}
</style>