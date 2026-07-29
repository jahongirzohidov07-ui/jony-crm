import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Lokal ishlaganda frontend :5173 da, backend :8000 da turadi.
    // Shuning uchun /api so'rovlarini backendga uzatamiz.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
