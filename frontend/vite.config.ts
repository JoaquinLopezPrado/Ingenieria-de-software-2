import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // =========================================================================
  // CONFIGURACIÓN DEL SERVIDOR PARA DOCKER Y NGROK
  // =========================================================================
  server: {
    host: true, // Permite que Docker exponga el puerto hacia afuera del contenedor
    port: 5173, // Asegura que use el puerto que mapeaste en tu docker-compose
    allowedHosts: [
      'frontend',          // Permite el nombre del servicio interno de Docker
      '.ngrok-free.app',   // Permite dominios públicos estándar de ngrok
      '.ngrok-free.dev'    // Permite los nuevos dominios de desarrollo de ngrok
    ]
  }
})
