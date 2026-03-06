import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // WHY proxy:
    // During development, the frontend runs on port 5173 and the backend on 8000.
    // This proxy lets the frontend call /api/* without CORS issues in development
    // (the browser thinks it's all one server).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
