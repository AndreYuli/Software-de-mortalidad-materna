import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsparser,
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    extends: [
      js.configs.recommended,
      tseslint.configs['flat/recommended'],
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
  },
])
