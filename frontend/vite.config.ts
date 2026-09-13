import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server proxies /api/* to the FastAPI backend (plan.md §7).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
