import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../backend/static'
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
