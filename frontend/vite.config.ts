import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, Vite serves the screens on :5173 and forwards /api to FastAPI on :8000.
// If 8000 is taken, run uvicorn on another port and start Vite with API_PORT=<that port>.
const apiPort = process.env.API_PORT ?? '8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': `http://localhost:${apiPort}` },
  },
})
