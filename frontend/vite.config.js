import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
      '/auth': {
        target: 'http://localhost:5000',
      },
      '/me': {
        target: 'http://localhost:5000',
      },
      '/decodificar-qr': {
        target: 'http://localhost:5000',
      },
    },
  },
})
