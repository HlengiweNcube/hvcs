import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API calls to the Django dev server so we avoid CORS in development.
// In production, the React build is served from Django's staticfiles.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
