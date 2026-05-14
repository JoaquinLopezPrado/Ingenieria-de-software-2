<template>
  <div class="class-page">
    <div class="class-card">
      <h1 class="title">Inscripción a clases</h1>
      <p class="subtitle">Elegí un tipo de clase y después seleccioná un turno disponible.</p>

      <div class="field-group">
        <label for="classType" class="label">Tipo de clase</label>
        <select id="classType" v-model="selectedClassType" class="select-input">
          <option disabled value="">Seleccioná una opción</option>
          <option value="funcional">Entrenamiento funcional</option>
          <option value="pilates">Pilates</option>
          <option value="yoga">Yoga</option>
        </select>
      </div>

      <div v-if="selectedClassType" class="field-group">
        <label class="label">Turnos disponibles</label>

        <div v-if="availableOptions.length > 0" class="options-list">
          <button
            v-for="option in availableOptions"
            :key="option.id"
            class="option-card"
            :class="{
              selected: selectedOptionId === option.id,
              disabled: option.currentCapacity >= option.maxCapacity
            }"
            :disabled="option.currentCapacity >= option.maxCapacity"
            @click="selectOption(option.id)"
            type="button"
          >
            <div class="option-header">
              <h3>{{ option.day }} - {{ option.time }}</h3>
              <span
                class="status-badge"
                :class="option.currentCapacity >= option.maxCapacity ? 'full' : 'available'"
              >
                {{
                  option.currentCapacity >= option.maxCapacity
                    ? 'Sin cupo'
                    : 'Disponible'
                }}
              </span>
            </div>

            <p><strong>Sala:</strong> {{ option.room }}</p>
            <p>
              <strong>Cupo:</strong>
              {{ option.currentCapacity }} / {{ option.maxCapacity }}
            </p>
          </button>
        </div>

        <p v-else class="empty-message">
          No hay turnos cargados para este tipo de clase.
        </p>
      </div>

      <button
        class="submit-btn"
        :disabled="!canSubmit"
        @click="handleSubmit"
        type="button"
      >
        Inscribirme
      </button>

      <p v-if="successMessage" class="success-message">
        {{ successMessage }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type ClassType = 'funcional' | 'pilates' | 'yoga'

interface ClassOption {
  id: number
  type: ClassType
  day: string
  time: string
  room: number
  currentCapacity: number
  maxCapacity: number
}

const selectedClassType = ref<ClassType | ''>('')
const selectedOptionId = ref<number | null>(null)
const successMessage = ref('')

const classOptions = ref<ClassOption[]>([
  {
    id: 1,
    type: 'funcional',
    day: 'Lunes',
    time: '08:00',
    room: 1,
    currentCapacity: 8,
    maxCapacity: 10,
  },
  {
    id: 2,
    type: 'funcional',
    day: 'Miércoles',
    time: '18:00',
    room: 2,
    currentCapacity: 10,
    maxCapacity: 10,
  },
  {
    id: 3,
    type: 'pilates',
    day: 'Martes',
    time: '10:00',
    room: 1,
    currentCapacity: 6,
    maxCapacity: 8,
  },
  {
    id: 4,
    type: 'pilates',
    day: 'Jueves',
    time: '17:00',
    room: 3,
    currentCapacity: 8,
    maxCapacity: 8,
  },
  {
    id: 5,
    type: 'yoga',
    day: 'Lunes',
    time: '19:00',
    room: 2,
    currentCapacity: 4,
    maxCapacity: 10,
  },
  {
    id: 6,
    type: 'yoga',
    day: 'Viernes',
    time: '09:00',
    room: 1,
    currentCapacity: 10,
    maxCapacity: 10,
  },
])

const availableOptions = computed(() => {
  selectedOptionId.value = null
  successMessage.value = ''

  return classOptions.value.filter(
    (option) => option.type === selectedClassType.value
  )
})

const canSubmit = computed(() => {
  if (!selectedOptionId.value) return false

  const selectedOption = classOptions.value.find(
    (option) => option.id === selectedOptionId.value
  )

  if (!selectedOption) return false

  return selectedOption.currentCapacity < selectedOption.maxCapacity
})

function selectOption(id: number) {
  selectedOptionId.value = id
  successMessage.value = ''
}

function handleSubmit() {
  const selectedOption = classOptions.value.find(
    (option) => option.id === selectedOptionId.value
  )

  if (!selectedOption) return

  if (selectedOption.currentCapacity >= selectedOption.maxCapacity) return

  selectedOption.currentCapacity += 1

  successMessage.value = `Te inscribiste correctamente a ${formatClassName(
    selectedOption.type
  )} - ${selectedOption.day} ${selectedOption.time}, sala ${selectedOption.room}.`

  selectedOptionId.value = null
}

function formatClassName(type: ClassType) {
  if (type === 'funcional') return 'Entrenamiento funcional'
  if (type === 'pilates') return 'Pilates'
  return 'Yoga'
}
</script>

<style scoped>
.class-page {
  min-height: 100vh;
  background: #d9eeea;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.class-card {
  width: 100%;
  max-width: 820px;
  background: #ffffff;
  border-radius: 28px;
  padding: 36px 32px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
}

.title {
  margin: 0 0 8px;
  color: #0d9b8a;
  font-size: 2rem;
  font-weight: 800;
}

.subtitle {
  margin: 0 0 28px;
  color: #6b7280;
  font-size: 1rem;
}

.field-group {
  margin-bottom: 24px;
}

.label {
  display: block;
  margin-bottom: 10px;
  color: #0d9b8a;
  font-weight: 700;
}

.select-input {
  width: 100%;
  border: 1px solid #cfd8dc;
  border-radius: 14px;
  padding: 14px 16px;
  font-size: 1rem;
  outline: none;
}

.select-input:focus {
  border-color: #18b4a3;
}

.options-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.option-card {
  border: 1px solid #d8e3e2;
  border-radius: 18px;
  background: #ffffff;
  padding: 18px;
  text-align: left;
  cursor: pointer;
  transition: all 0.18s ease;
}

.option-card:hover:not(:disabled) {
  border-color: #18b4a3;
  box-shadow: 0 8px 18px rgba(24, 180, 163, 0.12);
}

.option-card.selected {
  border-color: #18b4a3;
  background: #f3fffd;
}

.option-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f7f7f7;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.option-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
}

.status-badge {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 700;
}

.status-badge.available {
  background: rgba(24, 180, 163, 0.14);
  color: #0d9b8a;
}

.status-badge.full {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.option-card p {
  margin: 6px 0 0;
  color: #4b5563;
}

.empty-message {
  color: #6b7280;
  margin: 0;
}

.submit-btn {
  width: 100%;
  border: none;
  border-radius: 999px;
  padding: 15px 20px;
  background: #18b4a3;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(24, 180, 163, 0.25);
  transition: background 0.18s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #109889;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.success-message {
  margin-top: 16px;
  color: #0d9b8a;
  font-weight: 600;
}

@media (min-width: 768px) {
  .options-list {
    grid-template-columns: 1fr 1fr;
  }
}
</style>