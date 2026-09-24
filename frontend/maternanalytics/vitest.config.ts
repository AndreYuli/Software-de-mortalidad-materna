/// <reference types="vitest" />
import { configDefaults, defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    // Los specs de Playwright (e2e/) los ejecuta `playwright test`, no Vitest.
    exclude: [...configDefaults.exclude, 'e2e/**'],
    setupFiles: ['./src/setupTests.ts'],
  },
})
