import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/login/',

  // In dev: proxy API calls to the FastAPI backend
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  // Build output goes alongside the existing vanilla frontend
  // so FastAPI StaticFiles can serve both at /login/*
  build: {
    outDir: '../frontend/login',
    emptyOutDir: true,
  },
})

