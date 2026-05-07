<script setup lang="ts">
import { ref } from 'vue'
import AuthHeader from '@/components/auth/AuthHeader.vue'

const email = ref('')
const success = ref(false)

const handleRecover = () => {
  if (email.value) success.value = true
}
</script>

<template>
  <div class="auth-page-wrapper">
    <div class="auth-card">
      <AuthHeader subtitle="Recuperar acceso" />
      
      <div v-if="success" class="success-banner">
        <p>¡Listo! Revisa tu correo para restablecer tu contraseña.</p>
        <router-link to="/login" class="link-accent">Volver al Inicio →</router-link>
      </div>

      <form v-else @submit.prevent="handleRecover" class="form-container">
        <div class="form-group">
          <label class="custom-label">Tu Email</label>
          <input 
            v-model="email" 
            type="email" 
            placeholder="email@ejemplo.com" 
            class="input-field" 
            required 
          />
        </div>

        <div class="actions">
          <button type="submit" class="btn-primary">Enviar </button>
          <router-link to="/login" class="link-back">Cancelar</router-link>
        </div>
      </form>

      <div class="footer-note">
        <router-link to="/login" class="link-secondary">← Volver al inicio de sesión</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Contenedor que ocupa TODA la pantalla */
.auth-page-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100vw; /* Asegura el ancho completo */
  position: fixed; /* Evita que otros elementos lo muevan */
  top: 0;
  left: 0;
  background: linear-gradient(135deg, #dff8f2 0%, #cfeee6 100%);
  z-index: 999;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 24px;
  box-shadow: 0 15px 35px rgba(13, 110, 95, 0.1);
  width: 90%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-label {
  font-weight: 700;
  color: #00897b;
  font-size: 13px;
  margin-left: 4px;
}

.input-field {
  padding: 14px 16px;
  background-color: #f8fbfb;
  border: 2px solid #e0f2f1;
  border-radius: 12px;
  font-size: 14px;
  width: 100%;
  box-sizing: border-box; /* Importante para que no se salga del card */
}

.input-field:focus {
  outline: none;
  border-color: #11a691;
  background-color: #fff;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
}

.btn-primary {
  padding: 16px;
  background: #11a691;
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

.link-back, .link-secondary {
  text-align: center;
  color: #7f8c8d;
  font-size: 14px;
  text-decoration: none;
}

.footer-note {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eef2f1;
  text-align: center;
}

.success-banner {
  background-color: #e8f4f1;
  color: #00897b;
  padding: 24px;
  border-radius: 16px;
  text-align: center;
  line-height: 1.5;
}

.link-accent {
  display: inline-block;
  margin-top: 12px;
  color: #11a691;
  font-weight: 700;
  text-decoration: none;
}
</style>