import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/authStore'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)
app.use(router)

// Si hay un token en localStorage, intentamos cargar el perfil
const authStore = useAuthStore()
if (localStorage.getItem('access_token')) {
    // No await aquí para no bloquear el bootstrap; el store validará el token y hará logout si falla
    authStore.fetchUser().catch(() => { })
}

app.mount('#app')
