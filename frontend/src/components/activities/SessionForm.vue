<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getFormOptions, type SessionData } from '@/services/sessionService'

// Props (datos que recibe de la vista)
defineProps<{
  isLoading: boolean
}>()

// Emits (eventos que le avisan a la vista que el form se envió)
const emit = defineEmits<{
  (e: 'submit-session', payload: SessionData): void
}>()

const daysOfWeek = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado']

// Variables reactivas para las opciones de los selects
const availableActivities = ref<string[]>([])
const availableInstructors = ref<string[]>([])
const availableRooms = ref<string[]>([])

// El estado del formulario usando la interfaz que creamos
const newSession = ref<SessionData>({
  activity: '',
  instructor: '',
  days: [],
  startTime: '',
  endTime: '',
  maxCapacity: null,
  room: ''
})

// Cargar las opciones cuando el componente aparece en pantalla
onMounted(async () => {
  const options = await getFormOptions()
  availableActivities.value = options.activities
  availableInstructors.value = options.instructors
  availableRooms.value = options.rooms
})

const handleSubmit = () => {
  emit('submit-session', newSession.value)
}
</script>

<template>
  <div class="form-card">
    <form @submit.prevent="handleSubmit">
      
      <!-- Activity & Instructor -->
      <div class="form-grid-2">
        <div class="input-group">
          <label>Actvidad</label>
          <select v-model="newSession.activity" required>
            <option value="" disabled>Selecciona actividad...</option>
            <option v-for="act in availableActivities" :key="act" :value="act">{{ act }}</option>
          </select>
        </div>
        <div class="input-group">
          <label>Instructor</label>
          <select v-model="newSession.instructor" required>
            <option value="" disabled>Selecciona instructor...</option>
            <option v-for="prof in availableInstructors" :key="prof" :value="prof">{{ prof }}</option>
          </select>
        </div>
      </div>

      <!-- Days of Week -->
      <div class="input-group">
        <label>Programa Dias</label>
        <div class="days-container">
          <label v-for="day in daysOfWeek" :key="day" class="day-label">
            <input type="checkbox" :value="day" v-model="newSession.days" class="hidden-checkbox" />
            <span class="day-pill">{{ day }}</span>
          </label>
        </div>
      </div>

      <!-- Times & Room -->
      <div class="form-grid-3">
        <div class="input-group">
          <label>Hora de Inicio</label>
          <input type="time" v-model="newSession.startTime" required>
        </div>
        <div class="input-group">
          <label>Hora de Fin</label>
          <input type="time" v-model="newSession.endTime" required>
        </div>
        <div class="input-group">
          <label>Salon</label>
          <select v-model="newSession.room" required>
            <option value="" disabled>Select room...</option>
            <option v-for="room in availableRooms" :key="room" :value="room">{{ room }}</option>
          </select>
        </div>
      </div>

      <!-- Capacity -->
      <div class="input-group capacity-input">
        <label>Cupo maximo</label>
        <input type="number" v-model="newSession.maxCapacity" min="1" placeholder="Ej: 15" required>
      </div>

      <!-- Submit Button -->
      <div class="form-actions">
        <button type="submit" :disabled="isLoading" class="btn-submit">
          {{ isLoading ? 'Guardando...' : 'Guardar Turno' }}
        </button>
      </div>

    </form>
  </div>
</template>

<style scoped>
.form-card {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  padding: 2.5rem;
  border: 1px solid #f3f4f6;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
}

.input-group {
  margin-bottom: 1.5rem;
}

.capacity-input {
  max-width: 30%;
}

label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 0.5rem;
}

input[type="time"], 
input[type="number"], 
select {
  width: 100%;
  padding: 0.7rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background-color: #f9fafb;
  font-size: 0.95rem;
  color: #1f2937;
  outline: none;
  box-sizing: border-box;
}

input:focus, select:focus {
  border-color: #11998e;
  box-shadow: 0 0 0 2px rgba(17, 153, 142, 0.2);
}

/* Estilos para los "Pills" de los días */
.days-container {
  display: flex;
  gap: 0.7rem;
  flex-wrap: wrap;
}

.day-label {
  cursor: pointer;
}

.hidden-checkbox {
  display: none;
}

.day-pill {
  display: inline-block;
  padding: 0.5rem 1.2rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 500;
  background-color: #f3f4f6;
  color: #6b7280;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.hidden-checkbox:checked + .day-pill {
  background-color: #0c8a70;
  color: white;
  border-color: #0c8a70;
}

.form-actions {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
  text-align: right;
}

.btn-submit {
  background-color: #11998e;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  padding: 0.8rem 2rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #0c8a70;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>