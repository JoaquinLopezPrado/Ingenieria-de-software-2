<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  const access_token = route.query.access_token as string
  const refresh_token = route.query.refresh_token as string

  if (access_token && refresh_token) {
    try {
      await authStore.loginWithTokens(access_token, refresh_token)
      router.replace('/home')
    } catch {
      router.replace('/')
    }
  } else {
    router.replace('/')
  }
})
</script>

<template>
  <div class="callback-wrapper">
    <div class="spinner"></div>
    <p>Iniciando sesión con Google...</p>
  </div>
</template>

<style scoped>
.callback-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 16px;
  color: #546e7a;
  font-size: 15px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e0f2f1;
  border-top-color: #11a691;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
