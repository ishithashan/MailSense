import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/fetch_emails": "http://localhost:5000",
      "/login": "http://localhost:5000",
      "/oauth2callback": "http://localhost:5000",
      "/check_auth": "http://localhost:5000"
    }
  }
})