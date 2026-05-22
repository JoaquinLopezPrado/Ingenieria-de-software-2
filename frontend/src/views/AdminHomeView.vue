<script setup lang="ts">
import AdminLayout from '@/components/layout/AdminLayout.vue'
</script>

<template>
  <AdminLayout>
    <section class="admin-home">
      <div class="welcome-card">
        <p class="eyebrow">Panel de administración</p>
        <h1>Bienvenido al panel de administración</h1>
        <p>
          Acá podés gestionar actividades, turnos y configuraciones del centro.
        </p>
      </div>
    </section>
  </AdminLayout>
</template>

<style scoped>
.admin-home {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem;
  box-sizing: border-box;
}

.welcome-card {
  width: min(100%, 720px);
  padding: 3rem;
  border-radius: 28px;
  background: linear-gradient(135deg, #ffffff 0%, #f1f7f6 100%);
  box-shadow: 0 18px 40px rgba(13, 48, 39, 0.12);
  border: 1px solid rgba(17, 153, 142, 0.12);
  text-align: center;
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
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1.1;
}

p {
  margin: 1rem 0 0;
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.6;
}
</style>
