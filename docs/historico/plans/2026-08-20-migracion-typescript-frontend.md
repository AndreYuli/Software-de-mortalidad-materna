# Migración del frontend a TypeScript — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar `FRONTED/maternanalytics` de JavaScript a TypeScript sin cambiar comportamiento visible, con `vitest` corriendo como test runner nuevo.

**Architecture:** Migración archivo por archivo, de hojas a raíz (componentes sin dependencias propias primero, los dos componentes grandes al final). Cada archivo migrado gana tipos explícitos y un test de humo. `allowJs: true` mientras conviven `.jsx`/`.tsx`; se cierra a `false` al final.

**Tech Stack:** TypeScript 5.x, Vite 8, vitest, @testing-library/react, @testing-library/jest-dom.

---

## Nota de corrección sobre la spec

La spec (`docs/historico/specs/2026-08-20-migracion-typescript-frontend-design.md`) asume que `src/api.js` es un "fetch wrapper". Verificado en código: hoy solo exporta la constante `API_URL`; cada componente hace sus propios `fetch()`. Este plan migra `api.ts` tal cual es (una constante tipada), sin inventar una abstracción que no existe — la función `obtenerNarrativa` se agrega ahí en el plan de la spec de IA generativa, no en este.

También se descubrió que `src/components/Dashboard.jsx` (524 líneas) no está importado por nadie (`App.jsx` solo usa `DashboardOKD.jsx`). El usuario confirmó eliminarlo — Task 2 de este plan.

---

## File Structure

```
FRONTED/maternanalytics/
├── tsconfig.json                 ← NUEVO
├── tsconfig.node.json            ← NUEVO
├── src/vite-env.d.ts             ← NUEVO
├── vitest.config.ts              ← NUEVO
├── eslint.config.js              ← MODIFICADO (soporte .ts/.tsx)
├── package.json                  ← MODIFICADO (deps + script test)
├── src/
│   ├── setupTests.ts             ← NUEVO
│   ├── types.ts                  ← NUEVO
│   ├── api.ts                    ← migrado desde api.js
│   ├── api.test.ts               ← NUEVO
│   ├── App.tsx                   ← migrado
│   ├── main.tsx                  ← migrado
│   └── components/
│       ├── Login.tsx             ← migrado
│       ├── Login.test.tsx        ← NUEVO
│       ├── Register.tsx          ← migrado
│       ├── Register.test.tsx     ← NUEVO
│       ├── DashboardOKD.tsx      ← migrado
│       ├── DashboardOKD.test.tsx ← NUEVO
│       ├── AnalisisView.tsx      ← migrado
│       ├── AnalisisView.test.tsx ← NUEVO
│       ├── Dashboard.jsx         ← ELIMINADO (código muerto)
│       └── Dashboard.css         ← ELIMINADO (código muerto)
```

---

### Task 1: Instalar TypeScript + vitest y configurar el proyecto

**Files:**
- Modify: `FRONTED/maternanalytics/package.json`
- Create: `FRONTED/maternanalytics/tsconfig.json`
- Create: `FRONTED/maternanalytics/tsconfig.node.json`
- Create: `FRONTED/maternanalytics/src/vite-env.d.ts`
- Create: `FRONTED/maternanalytics/vitest.config.ts`
- Create: `FRONTED/maternanalytics/src/setupTests.ts`

- [ ] **Step 1: Instalar dependencias**

Run (desde `FRONTED/maternanalytics`):
```bash
pnpm add -D typescript vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @typescript-eslint/eslint-plugin @typescript-eslint/parser
```
Expected: se agregan a `devDependencies` en `package.json` (ya existían `@types/react`, `@types/react-dom`).

- [ ] **Step 2: Crear `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "allowJs": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Crear `tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.js", "vitest.config.ts"]
}
```

- [ ] **Step 4: Crear `src/vite-env.d.ts`**

```ts
/// <reference types="vite/client" />
```

- [ ] **Step 5: Crear `vitest.config.ts`**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setupTests.ts'],
  },
})
```

- [ ] **Step 6: Crear `src/setupTests.ts`**

```ts
import '@testing-library/jest-dom/vitest'
```

- [ ] **Step 7: Agregar script `test` a `package.json`**

En la sección `scripts` de `FRONTED/maternanalytics/package.json`, agregar:
```json
"test": "vitest run"
```

- [ ] **Step 8: Verificar que el build actual sigue funcionando (baseline antes de migrar nada)**

Run: `pnpm run build`
Expected: build exitoso (todavía todo en `.jsx`, `allowJs: true` lo permite).

- [ ] **Step 9: Commit**

```bash
git add package.json pnpm-lock.yaml tsconfig.json tsconfig.node.json src/vite-env.d.ts vitest.config.ts src/setupTests.ts
git commit -m "chore: configurar TypeScript y vitest en el frontend"
```

---

### Task 2: Eliminar código muerto (`Dashboard.jsx`)

**Files:**
- Delete: `FRONTED/maternanalytics/src/components/Dashboard.jsx`
- Delete: `FRONTED/maternanalytics/src/components/Dashboard.css`

- [ ] **Step 1: Confirmar que no hay importadores**

Run: `grep -rn "components/Dashboard'" FRONTED/maternanalytics/src --include="*.jsx" --include="*.js" | grep -v DashboardOKD`
Expected: sin resultados (ya verificado en brainstorming; esto es el chequeo de seguridad antes de borrar).

- [ ] **Step 2: Eliminar los archivos**

```bash
git rm FRONTED/maternanalytics/src/components/Dashboard.jsx FRONTED/maternanalytics/src/components/Dashboard.css
```

- [ ] **Step 3: Verificar que el build sigue funcionando**

Run: `pnpm run build` (desde `FRONTED/maternanalytics`)
Expected: build exitoso, sin referencias rotas.

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: eliminar Dashboard.jsx (código muerto, no importado por nadie)"
```

---

### Task 3: Migrar `api.js` → `api.ts` + `types.ts`

**Files:**
- Create: `FRONTED/maternanalytics/src/types.ts`
- Create: `FRONTED/maternanalytics/src/api.ts` (reemplaza `api.js`)
- Delete: `FRONTED/maternanalytics/src/api.js`
- Test: `FRONTED/maternanalytics/src/api.test.ts`

- [ ] **Step 1: Crear `src/types.ts` con las interfaces de dominio verificadas contra `BACKEND/services/_analisis_calculo.py`**

```ts
export interface AnalisisMeta {
  id: number
  nombre_archivo: string
  fecha_carga: string
  limpieza_datos: Record<string, unknown>
  anos_disponibles: number[]
  filtros_activos: { year: string | null; month: string | null }
  distribucion_mensual: Record<string, unknown>
}

export interface CausaCie10 {
  codigo: string
  casos: number
}

export interface DemoraDetalle {
  nombre: string
  casos_con_demora: number
  porcentaje: number
}

export interface CriterioInclusion {
  nombre: string
  casos: number
}

export interface IndicadoresMortalidad extends AnalisisMeta {
  tipo: 'mortalidad'
  estadisticas_basicas: Record<string, unknown>
  momento_muerte: Record<string, unknown>
  demoras: Record<string, DemoraDetalle>
  causas_cie10: { top_causas: CausaCie10[]; total_causas_unicas: number }
  obstetrico_edad: Record<string, unknown>
}

export interface IndicadoresMorbilidad extends AnalisisMeta {
  tipo: 'morbilidad'
  estadisticas_basicas: Record<string, unknown>
  criterios_inclusion: Record<string, CriterioInclusion>
  momento_ocurrencia: Record<string, unknown>
  institucion_referencia: Record<string, unknown>
  tiempo_remision: Record<string, unknown>
  obstetrico_edad: Record<string, unknown>
}

export type AnalisisCompleto = IndicadoresMortalidad | IndicadoresMorbilidad

export interface AnalisisResponse {
  id: number
  tipo: 'mortalidad' | 'morbilidad'
  nombre_archivo: string
  fecha_carga: string
  total_registros: number
}
```

- [ ] **Step 2: Crear `src/api.ts`**

```ts
export const API_URL = 'http://localhost:8000/api'
```

- [ ] **Step 3: Eliminar `src/api.js`**

```bash
git rm FRONTED/maternanalytics/src/api.js
```

- [ ] **Step 4: Escribir test de humo**

`src/api.test.ts`:
```ts
import { describe, expect, it } from 'vitest'
import { API_URL } from './api'

describe('api', () => {
  it('expone una URL base http válida', () => {
    expect(API_URL).toMatch(/^https?:\/\//)
  })
})
```

- [ ] **Step 5: Correr el test**

Run: `pnpm test`
Expected: PASS (1 test).

- [ ] **Step 6: Commit**

```bash
git add src/types.ts src/api.ts src/api.test.ts
git commit -m "feat: migrar api.js a TypeScript y agregar types.ts de dominio"
```

---

### Task 4: Migrar `main.jsx` → `main.tsx` y `App.jsx` → `App.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/main.tsx` (reemplaza `main.jsx`)
- Create: `FRONTED/maternanalytics/src/App.tsx` (reemplaza `App.jsx`)
- Delete: `FRONTED/maternanalytics/src/main.jsx`, `FRONTED/maternanalytics/src/App.jsx`
- Modify: `FRONTED/maternanalytics/index.html:` referencia a `main.jsx` → `main.tsx`
- Test: `FRONTED/maternanalytics/src/App.test.tsx`

- [ ] **Step 1: Crear `src/main.tsx`**

```tsx
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('No se encontró el elemento #root en el HTML.')
}

createRoot(rootElement).render(<App />)
```

- [ ] **Step 2: Crear `src/App.tsx`**

```tsx
import { useState, Suspense, lazy } from 'react'
import Login from './components/Login'
import Register from './components/Register'

const DashboardOKD = lazy(() => import('./components/DashboardOKD'))

type View = 'login' | 'register' | 'dashboard'

function App() {
  const [view, setView] = useState<View>('login')

  if (view === 'dashboard') return (
    <Suspense fallback={<div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',fontFamily:'sans-serif'}}>Cargando...</div>}>
      <DashboardOKD onLogout={() => setView('login')} />
    </Suspense>
  )
  if (view === 'register') return <Register onRegistered={() => setView('login')} onBack={() => setView('login')} />
  return <Login onLogin={() => setView('dashboard')} onRegister={() => setView('register')} />
}

export default App
```

- [ ] **Step 3: Eliminar los `.jsx` originales**

```bash
git rm FRONTED/maternanalytics/src/main.jsx FRONTED/maternanalytics/src/App.jsx
```

- [ ] **Step 4: Actualizar `index.html`**

En `FRONTED/maternanalytics/index.html`, cambiar:
```html
<script type="module" src="/src/main.jsx"></script>
```
por:
```html
<script type="module" src="/src/main.tsx"></script>
```

- [ ] **Step 5: Verificar tipos**

Run: `npx tsc --noEmit`
Expected: sin errores en `main.tsx`/`App.tsx` (los componentes que aún importa, `Login`/`Register`/`DashboardOKD`, siguen en `.jsx` y `allowJs: true` los tolera todavía).

- [ ] **Step 6: Commit**

```bash
git add src/main.tsx src/App.tsx index.html
git commit -m "feat: migrar main.jsx y App.jsx a TypeScript"
```

---

### Task 5: Migrar `Login.jsx` → `Login.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/Login.tsx` (reemplaza `Login.jsx`)
- Delete: `FRONTED/maternanalytics/src/components/Login.jsx`
- Test: `FRONTED/maternanalytics/src/components/Login.test.tsx`

- [ ] **Step 1: Crear `Login.tsx`**

Contenido idéntico a `Login.jsx` (leído en `FRONTED/maternanalytics/src/components/Login.jsx`), con estos cambios de tipos:

```tsx
import { useState, FormEvent } from 'react'
import './Login.css'
import { API_URL } from '../api'

interface LoginProps {
  onLogin: () => void
  onRegister: () => void
}

export default function Login({ onLogin, onRegister }: LoginProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Correo o contraseña incorrectos.')
        return
      }
      localStorage.setItem('username', data.nombre)
      localStorage.setItem('user_email', data.email)
      onLogin()
    } catch {
      setError('No se pudo conectar al servidor. Verifica que el backend esté activo.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page">

      {/* LEFT PANEL */}
      <div className="left">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>

        <div className="left-content">
          <div className="logo-icon">
            <svg width="90" height="90" viewBox="0 0 64 64">
              <path d="M32 4 C52 4 58 20 58 34 C58 52 46 60 32 60 C18 60 6 52 6 34 C6 20 12 4 32 4Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.2"/>
              <path d="M26 16 C18 24 16 34 22 44 C26 48 30 52 32 54" fill="none" stroke="#F4C0D1" strokeWidth="2" strokeLinecap="round"/>
              <path d="M38 14 C46 22 48 34 42 44 C38 48 34 52 32 54" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="32" cy="36" r="5" fill="none" stroke="#F4C0D1" strokeWidth="1.2"/>
              <circle cx="32" cy="36" r="1.8" fill="#F4C0D1"/>
              <circle cx="20" cy="26" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="17" cy="36" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="20" cy="44" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="44" cy="24" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="47" cy="34" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="44" cy="44" r="1.5" fill="rgba(255,255,255,0.25)"/>
            </svg>
          </div>
          <h1 className="brand-title">Vida<span>Materna</span></h1>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="right">
        <div className="form-container">
          <div className="form-header">
            <h2>Inicio de sesión</h2>
            <p>Ingresa tus credenciales para acceder a la plataforma de análisis.</p>
          </div>

          <form onSubmit={handleLogin}>
            <div className="field">
              <label>Correo electrónico</label>
              <input
                type="email"
                placeholder="tu.correo@institucion.gov.co"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="3"/><path d="M22 4L12 13 2 4"/>
              </svg>
            </div>

            <div className="field">
              <label>Contraseña</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="3"/><path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </div>

            {error && <p className="error-msg">{error}</p>}

            <div className="field-row">
              <label className="remember">
                <input type="checkbox" /> Recordarme
              </label>
              <a href="#" className="forgot">¿Olvidaste tu contraseña?</a>
            </div>

            <button type="submit" className="btn-login" disabled={isLoading}>
              {isLoading ? 'Verificando...' : 'Iniciar sesión'}
            </button>
          </form>

          <p className="footer-text">
            ¿No tienes una cuenta?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onRegister() }}>Crear cuenta</a>
          </p>
        </div>


      </div>

    </div>
  )
}
```

- [ ] **Step 2: Eliminar `Login.jsx`**

```bash
git rm FRONTED/maternanalytics/src/components/Login.jsx
```

- [ ] **Step 3: Escribir test de humo**

`src/components/Login.test.tsx`:
```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Login from './Login'

describe('Login', () => {
  it('renderiza el formulario de inicio de sesión', () => {
    render(<Login onLogin={vi.fn()} onRegister={vi.fn()} />)
    expect(screen.getByRole('heading', { name: /inicio de sesión/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Correr tipos y tests**

Run: `npx tsc --noEmit && pnpm test`
Expected: sin errores de tipos; test PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/Login.tsx src/components/Login.test.tsx
git commit -m "feat: migrar Login.jsx a TypeScript"
```

---

### Task 6: Migrar `Register.jsx` → `Register.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/Register.tsx` (reemplaza `Register.jsx`)
- Delete: `FRONTED/maternanalytics/src/components/Register.jsx`
- Test: `FRONTED/maternanalytics/src/components/Register.test.tsx`

- [ ] **Step 1: Crear `Register.tsx`**

Mismo patrón que Task 5. Firma tipada:

```tsx
import { useState, FormEvent } from 'react'
import './Login.css'
import { API_URL } from '../api'

interface RegisterProps {
  onRegistered: () => void
  onBack: () => void
}

export default function Register({ onRegistered, onBack }: RegisterProps) {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleRegister = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, email, password }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Error al crear la cuenta.')
        return
      }
      setSuccess(true)
      setTimeout(() => onRegistered(), 1800)
    } catch {
      setError('No se pudo conectar al servidor. Verifica que el backend esté activo.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page">

      {/* LEFT PANEL */}
      <div className="left">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="node"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>
        <div className="pulse-line"></div>

        <div className="left-content">
          <div className="logo-icon">
            <svg width="90" height="90" viewBox="0 0 64 64">
              <path d="M32 4 C52 4 58 20 58 34 C58 52 46 60 32 60 C18 60 6 52 6 34 C6 20 12 4 32 4Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.2"/>
              <path d="M26 16 C18 24 16 34 22 44 C26 48 30 52 32 54" fill="none" stroke="#F4C0D1" strokeWidth="2" strokeLinecap="round"/>
              <path d="M38 14 C46 22 48 34 42 44 C38 48 34 52 32 54" fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="32" cy="36" r="5" fill="none" stroke="#F4C0D1" strokeWidth="1.2"/>
              <circle cx="32" cy="36" r="1.8" fill="#F4C0D1"/>
              <circle cx="20" cy="26" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="17" cy="36" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="20" cy="44" r="1.5" fill="rgba(255,255,255,0.35)"/>
              <circle cx="44" cy="24" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="47" cy="34" r="1.5" fill="rgba(255,255,255,0.25)"/>
              <circle cx="44" cy="44" r="1.5" fill="rgba(255,255,255,0.25)"/>
            </svg>
          </div>
          <h1 className="brand-title">Vida<span>Materna</span></h1>
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div className="right">
        <div className="form-container">
          <div className="form-header">
            <h2>Crear cuenta</h2>
            <p>Completa los datos para registrarte en la plataforma de análisis.</p>
          </div>

          {success ? (
            <div className="register-success">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <p>¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...</p>
            </div>
          ) : (
            <form onSubmit={handleRegister}>
              <div className="field">
                <label>Nombre completo</label>
                <input
                  type="text"
                  placeholder="Tu nombre y apellido"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
              </div>

              <div className="field">
                <label>Correo electrónico</label>
                <input
                  type="email"
                  placeholder="tu.correo@institucion.gov.co"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="3"/><path d="M22 4L12 13 2 4"/>
                </svg>
              </div>

              <div className="field">
                <label>Contraseña</label>
                <input
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="3"/><path d="M7 11V7a5 5 0 0110 0v4"/>
                </svg>
              </div>

              <div className="field">
                <label>Confirmar contraseña</label>
                <input
                  type="password"
                  placeholder="Repite tu contraseña"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <svg className="field-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>

              {error && <p className="error-msg">{error}</p>}

              <button type="submit" className="btn-login" disabled={isLoading}>
                {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
              </button>
            </form>
          )}

          <p className="footer-text">
            ¿Ya tienes una cuenta?{' '}
            <a href="#" onClick={(e) => { e.preventDefault(); onBack() }}>Iniciar sesión</a>
          </p>
        </div>
      </div>

    </div>
  )
}
```

- [ ] **Step 2: Eliminar `Register.jsx`**

```bash
git rm FRONTED/maternanalytics/src/components/Register.jsx
```

- [ ] **Step 3: Escribir test de humo**

`src/components/Register.test.tsx`:
```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Register from './Register'

describe('Register', () => {
  it('renderiza el formulario de registro', () => {
    render(<Register onRegistered={vi.fn()} onBack={vi.fn()} />)
    expect(screen.getByRole('button', { name: /crear cuenta/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 4: Correr tipos y tests**

Run: `npx tsc --noEmit && pnpm test`
Expected: sin errores; todos los tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/Register.tsx src/components/Register.test.tsx
git commit -m "feat: migrar Register.jsx a TypeScript"
```

---

### Task 7: Migrar `DashboardOKD.jsx` → `DashboardOKD.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/DashboardOKD.tsx` (reemplaza `.jsx`)
- Delete: `FRONTED/maternanalytics/src/components/DashboardOKD.jsx`
- Test: `FRONTED/maternanalytics/src/components/DashboardOKD.test.tsx`

Este archivo (1557 líneas) define varios componentes internos que ya tienen `PropTypes` — se convierten 1:1 a `interface`. El contenido JSX/lógica no cambia; solo se le agregan anotaciones de tipo.

- [ ] **Step 1: Renombrar el archivo**

```bash
git mv FRONTED/maternanalytics/src/components/DashboardOKD.jsx FRONTED/maternanalytics/src/components/DashboardOKD.tsx
```

- [ ] **Step 2: Reemplazar el import de PropTypes por las interfaces TS equivalentes**

Quitar `import PropTypes from 'prop-types'` (línea 2) y el bloque `.propTypes = {...}` de cada componente, reemplazándolos por interfaces antes de cada función, siguiendo esta correspondencia exacta (derivada de los bloques `PropTypes` verificados en el archivo original):

```tsx
interface UploadCardProps {
  onFile: (file: File) => void
  onRemove: () => void
  eventLabel: string
  file: { name: string } | null
  error: { parseError?: boolean; missing?: string[]; found?: string[] } | null
  validating: boolean
}
// function UploadCard({ onFile, file, error, validating, onRemove, eventLabel }: UploadCardProps) { ... }

interface CasosCombinadosProps {
  latestMortalidad: { total_registros?: number } | null
  latestMorbilidad: { total_registros?: number } | null
}
// function CasosCombinados({ latestMortalidad, latestMorbilidad }: CasosCombinadosProps) { ... }

interface FilterPanelProps {
  year: string
  month: string
  eventos: string[]
  availableYears: number[]
  onYearChange: (year: string) => void
  onMonthChange: (month: string) => void
  onEventosChange: (eventos: string[]) => void
}
// function FilterPanel({ year, month, eventos, availableYears, onYearChange, onMonthChange, onEventosChange }: FilterPanelProps) { ... }

interface AnalysisHomeSectionProps {
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  onGoToUpload: () => void
  filterYear: string
  filterMonth: string
  availableYears: number[]
  onAvailableYears: (years: number[]) => void
  onYearChange: (year: string) => void
  onMonthChange: (month: string) => void
}
// function AnalysisHomeSection({ ... }: AnalysisHomeSectionProps) { ... }

interface UploadSectionProps {
  title: string
  description: string
  eventLabel: string
  file: { name: string } | null
  error: { parseError?: boolean; missing?: string[]; found?: string[] } | null
}
// function UploadSection({ title, description, eventLabel, file, error, ...resto }: UploadSectionProps & Record<string, unknown>) { ... }

interface DashboardOKDProps {
  onLogout: () => void
}
// export default function DashboardOKD({ onLogout }: DashboardOKDProps) { ... }
```

Aplicar cada interfaz a su función correspondiente (mismo nombre de componente, misma línea aproximada que en el original) y borrar el bloque `X.propTypes = {...}` asociado — ya no hace falta, TS lo reemplaza en tiempo de compilación. Mantener el resto del cuerpo de cada función sin cambios.

Nota: `UploadSection` recibe más props además de las 5 con PropTypes explícito (revisar en el original qué otros props usa internamente, p.ej. handlers pasados sin declarar en `propTypes` — típico de este archivo). Al tipar, si `tsc` reporta una prop usada pero no declarada, agregarla a `UploadSectionProps` con el tipo que exija el uso real (no adivinar — leer cómo se invoca el componente en el JSX para inferir el tipo).

- [ ] **Step 3: Quitar la dependencia `prop-types` del `package.json` si ningún otro archivo la usa**

Run: `grep -rn "prop-types" FRONTED/maternanalytics/src`
Si no hay más resultados que en `AnalisisView.jsx` (que se migra en el Task 8), esperar a completar ese task antes de desinstalar. Si ya no queda ninguno:
```bash
pnpm remove prop-types
```

- [ ] **Step 4: Tipar los `useState` que lo necesiten**

Correr `npx tsc --noEmit` y por cada error de tipo implícito (`useState(null)` sin genérico, callbacks de evento sin tipo, etc.), agregar el tipo explícito mínimo necesario, por ejemplo:
```tsx
const [file, setFile] = useState<{ name: string } | null>(null)
const [error, setError] = useState<{ parseError?: boolean; missing?: string[]; found?: string[] } | null>(null)
```
Repetir hasta que `tsc --noEmit` no reporte errores en este archivo.

- [ ] **Step 5: Escribir test de humo**

`src/components/DashboardOKD.test.tsx`:
```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DashboardOKD from './DashboardOKD'

vi.mock('react-plotly.js', () => ({ default: () => null }))

describe('DashboardOKD', () => {
  it('renderiza sin lanzar errores', () => {
    render(<DashboardOKD onLogout={vi.fn()} />)
    expect(document.body).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Correr tipos y tests**

Run: `npx tsc --noEmit && pnpm test`
Expected: sin errores de tipos; el nuevo test PASS (junto con los anteriores).

- [ ] **Step 7: Commit**

```bash
git add src/components/DashboardOKD.tsx src/components/DashboardOKD.test.tsx package.json pnpm-lock.yaml
git commit -m "feat: migrar DashboardOKD.jsx a TypeScript"
```

---

### Task 8: Migrar `AnalisisView.jsx` → `AnalisisView.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/AnalisisView.tsx` (reemplaza `.jsx`)
- Delete: `FRONTED/maternanalytics/src/components/AnalisisView.jsx`
- Test: `FRONTED/maternanalytics/src/components/AnalisisView.test.tsx`

Este archivo (1293 líneas) **no tiene `PropTypes`** — las interfaces se derivan de la firma real de cada función (verificada en el código) y de `types.ts` (Task 3).

- [ ] **Step 1: Renombrar el archivo**

```bash
git mv FRONTED/maternanalytics/src/components/AnalisisView.jsx FRONTED/maternanalytics/src/components/AnalisisView.tsx
```

- [ ] **Step 2: Agregar interfaces de props a cada componente del archivo**

Basado en las firmas verificadas (`ChartExplanation`, `AnalisisView`, `OverviewTab`, `ChartsTab`, `ClusteringTab`):

```tsx
import type { AnalisisCompleto } from '../types'

interface ChartExplanationProps {
  title: string
  text: string
}
// function ChartExplanation({ title, text }: ChartExplanationProps) { ... }

interface AnalisisViewProps {
  analisisId: number
  onBack?: () => void
  showBackButton?: boolean
  embedded?: boolean
  filterYear?: string
  filterMonth?: string
  onAvailableYears?: ((years: number[]) => void) | null
}
// function AnalisisView({ analisisId, onBack, showBackButton = true, embedded = false, filterYear = '', filterMonth = '', onAvailableYears = null }: AnalisisViewProps) { ... }

interface OverviewTabProps {
  data: AnalisisCompleto
}
// function OverviewTab({ data }: OverviewTabProps) { ... }

interface ChartsTabProps {
  data: AnalisisCompleto
  analisisId: number
}
// function ChartsTab({ data, analisisId }: ChartsTabProps) { ... }

interface ClusteringTabProps {
  data: Record<string, unknown> | null
  loading: boolean
  onGenerate: (tipoClustering: string, nClusters: number) => void
  clusterCount: number
  setClusterCount: (n: number) => void
}
// function ClusteringTab({ data, loading, onGenerate, clusterCount, setClusterCount }: ClusteringTabProps) { ... }
```

Aplicar cada interfaz a su función. Mantener el resto del cuerpo (JSX, lógica, `useState`, `useEffect`) sin cambios.

- [ ] **Step 3: Tipar los `useState`/`useEffect` que lo necesiten**

Correr `npx tsc --noEmit` y resolver cada error igual que en Task 7 Step 4 — agregar genéricos explícitos a `useState` donde el tipo no se pueda inferir, tipar callbacks de eventos DOM (`onChange`, `onClick`) con los tipos de React (`ChangeEvent<HTMLSelectElement>`, etc.) según lo que reporte el compilador.

- [ ] **Step 4: Desinstalar `prop-types` si ya no se usa en ningún archivo**

Run: `grep -rn "prop-types" FRONTED/maternanalytics/src`
Expected: sin resultados (ya migrado `DashboardOKD.tsx` en Task 7).
```bash
pnpm remove prop-types
```

- [ ] **Step 5: Escribir test de humo**

`src/components/AnalisisView.test.tsx`:
```tsx
import { describe, expect, it, vi } from 'vitest'
import { render } from '@testing-library/react'
import AnalisisView from './AnalisisView'

vi.mock('react-plotly.js', () => ({ default: () => null }))
vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve({ ok: true, json: () => Promise.resolve({}) } as Response)
))

describe('AnalisisView', () => {
  it('renderiza sin lanzar errores con props mínimas', () => {
    render(<AnalisisView analisisId={1} />)
  })
})
```

- [ ] **Step 6: Correr tipos y tests**

Run: `npx tsc --noEmit && pnpm test`
Expected: sin errores de tipos; todos los tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/components/AnalisisView.tsx src/components/AnalisisView.test.tsx package.json pnpm-lock.yaml
git commit -m "feat: migrar AnalisisView.jsx a TypeScript"
```

---

### Task 9: Cerrar la migración — `allowJs: false`, lint, build final

**Files:**
- Modify: `FRONTED/maternanalytics/tsconfig.json`
- Modify: `FRONTED/maternanalytics/eslint.config.js`

- [ ] **Step 1: Confirmar que no queda ningún `.jsx`/`.js` en `src/`**

Run: `find FRONTED/maternanalytics/src -name "*.jsx" -o -name "*.js"`
Expected: sin resultados.

- [ ] **Step 2: Cerrar `allowJs`**

En `tsconfig.json`, cambiar `"allowJs": true` por `"allowJs": false`.

- [ ] **Step 3: Actualizar `eslint.config.js` para reconocer `.ts`/`.tsx`**

```js
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
    plugins: { '@typescript-eslint': tseslint, 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
  },
])
```

- [ ] **Step 4: Correr build, tipos, lint y tests completos**

Run:
```bash
npx tsc --noEmit
pnpm run build
pnpm run lint
pnpm test
```
Expected: los cuatro comandos terminan sin errores.

- [ ] **Step 5: Commit**

```bash
git add tsconfig.json eslint.config.js
git commit -m "chore: cerrar migración a TypeScript (allowJs: false)"
```

---

## Criterio de aceptación (verificado, no asumido)

- [ ] `npx tsc --noEmit` sin errores.
- [ ] `pnpm run build` compila sin errores.
- [ ] `pnpm test` pasa en verde (9 archivos de test: api, Login, Register, DashboardOKD, AnalisisView + los que ya existan).
- [ ] `pnpm run lint` sin errores.
- [ ] Cero archivos `.jsx`/`.js` en `src/`.
- [ ] La app corre igual que antes (`pnpm dev` — verificación manual de login, subida de Excel, dashboard).
