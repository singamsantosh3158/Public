import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8787',
    },
    // Allows access via a tunnel hostname (e.g. *.trycloudflare.com) for sharing
    // a temporary public link — Vite otherwise rejects unrecognized Host headers.
    allowedHosts: true,
  },
})
