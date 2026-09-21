# Rediseño de Login y Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar las pantallas Login y Register con Tailwind y lucide-react: tarjeta centrada, sin decoraciones, con botón de ver contraseña.

**Architecture:** Cuatro piezas pequeñas y reutilizables en `src/components/auth/` (`AuthCard`, `AuthField`, `AuthNotice`, `authStyles`) que `Login` y `Register` componen. La lógica de los formularios (react-hook-form, zod, API, `localStorage`, navegación) se conserva sin cambios; solo se reescribe el JSX.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (tokens `brand-deep`, `brand-violet`, `brand-magenta` en `src/index.css`), lucide-react, react-hook-form, Vitest + Testing Library.

Spec: `docs/superpowers/specs/2026-09-20-auth-redesign-design.md`

**Todos los comandos se ejecutan desde `frontend/maternanalytics`.**

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/components/auth/authStyles.ts` | Crear | Clases compartidas del botón principal y de los enlaces |
| `src/components/auth/AuthNotice.tsx` | Crear | Aviso con ícono (error / info / success) |
| `src/components/auth/AuthField.tsx` | Crear | Campo con etiqueta, ícono, error y botón de ver contraseña |
| `src/components/auth/AuthCard.tsx` | Crear | Fondo, tarjeta, logo y encabezado |
| `src/components/auth/Login.tsx` | Reescribir | Formulario de login |
| `src/components/auth/Register.tsx` | Reescribir | Formulario de registro |
| `src/components/auth/*.test.tsx` | Crear | Un test por componente |

Restricción de los e2e (`e2e/auth.spec.ts`): en Login debe existir un `h2` "Inicio de sesión", un único elemento con etiqueta `/Correo/i`, un único elemento con etiqueta `/Contraseña/i` y un botón `/Iniciar sesión/i`. Por eso el botón de ver contraseña usa `aria-label` "Mostrar"/"Ocultar" (sin la palabra "contraseña").

---

### Task 1: AuthField, AuthNotice y estilos compartidos

**Files:**
- Create: `src/components/auth/authStyles.ts`
- Create: `src/components/auth/AuthNotice.tsx`
- Create: `src/components/auth/AuthField.tsx`
- Test: `src/components/auth/AuthField.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/auth/AuthField.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Mail } from 'lucide-react'
import type { UseFormRegisterReturn } from 'react-hook-form'
import AuthField from './AuthField'

const registration = {
  name: 'campo',
  onChange: vi.fn(),
  onBlur: vi.fn(),
  ref: vi.fn(),
} as unknown as UseFormRegisterReturn

describe('AuthField', () => {
  it('asocia la etiqueta con el input', () => {
    render(<AuthField id="email" label="Correo electrónico" icon={Mail} type="email" registration={registration} />)
    expect(screen.getByLabelText('Correo electrónico')).toHaveAttribute('type', 'email')
  })

  it('muestra el error y marca el input como inválido', () => {
    render(<AuthField id="email" label="Correo" icon={Mail} error="Formato inválido" registration={registration} />)
    expect(screen.getByText('Formato inválido')).toBeInTheDocument()
    expect(screen.getByLabelText('Correo')).toHaveAttribute('aria-invalid', 'true')
  })

  it('no muestra botón de ver en campos que no son contraseña', () => {
    render(<AuthField id="email" label="Correo" icon={Mail} type="email" registration={registration} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('alterna la visibilidad de la contraseña', async () => {
    render(<AuthField id="pw" label="Contraseña" icon={Mail} type="password" registration={registration} />)
    const input = screen.getByLabelText('Contraseña')
    expect(input).toHaveAttribute('type', 'password')

    await userEvent.click(screen.getByRole('button', { name: 'Mostrar' }))
    expect(input).toHaveAttribute('type', 'text')

    await userEvent.click(screen.getByRole('button', { name: 'Ocultar' }))
    expect(input).toHaveAttribute('type', 'password')
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/auth/AuthField.test.tsx`
Expected: FAIL, `Failed to resolve import "./AuthField"`.

- [ ] **Step 3: Crear los estilos compartidos**

Crear `src/components/auth/authStyles.ts`:

```ts
export const authButtonClass =
  'flex w-full items-center justify-center gap-2 rounded-lg bg-brand-magenta px-4 py-2.5 font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60'

export const authLinkClass =
  'font-medium text-brand-violet hover:underline focus-visible:underline'
```

- [ ] **Step 4: Crear AuthNotice**

Crear `src/components/auth/AuthNotice.tsx`:

```tsx
import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'

const VARIANTS = {
  error: { icon: AlertCircle, classes: 'border-red-200 bg-red-50 text-red-700', role: 'alert' },
  info: { icon: Info, classes: 'border-blue-200 bg-blue-50 text-blue-700', role: 'status' },
  success: { icon: CheckCircle, classes: 'border-green-200 bg-green-50 text-green-700', role: 'status' },
} as const

interface AuthNoticeProps {
  variant: keyof typeof VARIANTS
  children: ReactNode
}

export default function AuthNotice({ variant, children }: AuthNoticeProps) {
  const { icon: Icon, classes, role } = VARIANTS[variant]
  return (
    <div role={role} className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${classes}`}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}
```

- [ ] **Step 5: Crear AuthField**

Crear `src/components/auth/AuthField.tsx`:

```tsx
import { useState } from 'react'
import { Eye, EyeOff, type LucideIcon } from 'lucide-react'
import type { UseFormRegisterReturn } from 'react-hook-form'

interface AuthFieldProps {
  id: string
  label: string
  icon: LucideIcon
  type?: 'text' | 'email' | 'password'
  placeholder?: string
  error?: string
  registration: UseFormRegisterReturn
}

export default function AuthField({
  id,
  label,
  icon: Icon,
  type = 'text',
  placeholder,
  error,
  registration,
}: AuthFieldProps) {
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'
  const inputType = isPassword && visible ? 'text' : type
  const errorId = `${id}-error`

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="relative">
        <Icon
          className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          id={id}
          type={inputType}
          placeholder={placeholder}
          required
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={`w-full rounded-lg border bg-white py-2.5 pl-10 text-slate-900 outline-none transition focus:ring-2 focus:ring-brand-magenta/30 ${
            isPassword ? 'pr-11' : 'pr-3'
          } ${error ? 'border-red-500' : 'border-slate-300 focus:border-brand-magenta'}`}
          {...registration}
        />
        {isPassword && (
          <button
            type="button"
            aria-label={visible ? 'Ocultar' : 'Mostrar'}
            aria-pressed={visible}
            onClick={() => setVisible((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-brand-violet"
          >
            {visible ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
          </button>
        )}
      </div>
      {error && (
        <p id={errorId} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/auth/AuthField.test.tsx`
Expected: PASS, 4 tests.

- [ ] **Step 7: Commit** (incluye la instalación de lucide-react, aún sin commitear)

```bash
git add package.json pnpm-lock.yaml src/components/auth/authStyles.ts src/components/auth/AuthNotice.tsx src/components/auth/AuthField.tsx src/components/auth/AuthField.test.tsx
git commit -m "feat(auth): AuthField, AuthNotice y estilos compartidos con lucide-react"
```

---

### Task 2: AuthCard

**Files:**
- Create: `src/components/auth/AuthCard.tsx`
- Test: `src/components/auth/AuthCard.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/auth/AuthCard.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import AuthCard from './AuthCard'

describe('AuthCard', () => {
  it('muestra la marca, el título, el subtítulo, el contenido y el pie', () => {
    render(
      <AuthCard title="Inicio de sesión" subtitle="Ingresa tus datos" footer={<span>pie</span>}>
        <p>contenido</p>
      </AuthCard>,
    )
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('VidaMaterna')
    expect(screen.getByRole('heading', { level: 2, name: 'Inicio de sesión' })).toBeInTheDocument()
    expect(screen.getByText('Ingresa tus datos')).toBeInTheDocument()
    expect(screen.getByText('contenido')).toBeInTheDocument()
    expect(screen.getByText('pie')).toBeInTheDocument()
  })

  it('no renderiza pie si no se indica', () => {
    render(
      <AuthCard title="Crear cuenta" subtitle="Datos">
        <p>contenido</p>
      </AuthCard>,
    )
    expect(screen.queryByText('pie')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/auth/AuthCard.test.tsx`
Expected: FAIL, `Failed to resolve import "./AuthCard"`.

- [ ] **Step 3: Crear AuthCard**

Crear `src/components/auth/AuthCard.tsx`:

```tsx
import type { ReactNode } from 'react'
import { Heart } from 'lucide-react'

interface AuthCardProps {
  title: string
  subtitle: string
  children: ReactNode
  footer?: ReactNode
}

export default function AuthCard({ title, subtitle, children, footer }: AuthCardProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-3 flex size-14 items-center justify-center rounded-full bg-brand-magenta text-white">
            <Heart className="size-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-brand-deep">
            Vida<span className="text-brand-magenta">Materna</span>
          </h1>
        </div>

        <h2 className="text-xl font-semibold text-brand-deep">{title}</h2>
        <p className="mb-6 mt-1 text-sm text-slate-500">{subtitle}</p>

        {children}

        {footer && <p className="mt-6 text-center text-sm text-slate-600">{footer}</p>}
      </div>
    </main>
  )
}
```

- [ ] **Step 4: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/auth/AuthCard.test.tsx`
Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
git add src/components/auth/AuthCard.tsx src/components/auth/AuthCard.test.tsx
git commit -m "feat(auth): AuthCard con tarjeta centrada y logo de lucide"
```

---

### Task 3: Login

**Files:**
- Modify (reescribir): `src/components/auth/Login.tsx`
- Test: `src/components/auth/Login.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/auth/Login.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Login from './Login'

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<p>pantalla registro</p>} />
        <Route path="/dashboard" element={<p>panel</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body }),
  )
}

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText('Correo electrónico'), 'ana@test.com')
  await userEvent.type(screen.getByLabelText('Contraseña'), 'secreto1')
  await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
}

describe('Login', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.unstubAllGlobals())

  it('muestra el encabezado y los campos', () => {
    renderLogin()
    expect(screen.getByRole('heading', { level: 2, name: /inicio de sesión/i })).toBeInTheDocument()
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /recordarme/i })).toBeInTheDocument()
  })

  it('guarda la sesión y navega al panel si las credenciales son válidas', async () => {
    stubFetch(200, { access_token: 'tok', token_type: 'bearer', id: 1, nombre: 'Ana', email: 'ana@test.com' })
    renderLogin()
    await fillAndSubmit()
    expect(await screen.findByText('panel')).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBe('tok')
    expect(localStorage.getItem('username')).toBe('Ana')
  })

  it('muestra el error del servidor cuando las credenciales son incorrectas', async () => {
    stubFetch(401, { detail: 'Credenciales inválidas' })
    renderLogin()
    await fillAndSubmit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Credenciales inválidas')
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('muestra el aviso informativo al pulsar "¿Olvidaste tu contraseña?"', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /olvidaste/i }))
    expect(screen.getByRole('status')).toHaveTextContent(/recuperación de contraseñas/i)
  })

  it('lleva a la pantalla de registro con "Crear cuenta"', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /crear cuenta/i }))
    expect(screen.getByText('pantalla registro')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/auth/Login.test.tsx`
Expected: FAIL. El Login actual no asocia las etiquetas igual y no tiene `role="alert"` ni `role="status"` (varios tests fallan).

- [ ] **Step 3: Reescribir Login.tsx**

Reemplazar todo el contenido de `src/components/auth/Login.tsx` por (la lógica de `onSubmit` y `handleForgotPassword` es idéntica a la actual):

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Lock, Mail } from 'lucide-react'
import { API_URL, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { loginSchema } from '../../validation/loginSchema'
import AuthCard from './AuthCard'
import AuthField from './AuthField'
import AuthNotice from './AuthNotice'
import { authButtonClass, authLinkClass } from './authStyles'

interface LoginProps {
  onLogin?: () => void
  onRegister?: () => void
}
interface LoginResponse {
  access_token: string
  token_type: string
  id: number
  nombre: string
  email: string
  detail?: string
  error?: string
}

export default function Login({ onLogin, onRegister }: LoginProps = {}) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [infoMsg, setInfoMsg] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ email: string; password: string }>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: { email: string; password: string }) => {
    setError('')
    setInfoMsg('')
    setIsLoading(true)
    try {
      const res = await fetchWithTimeout(`${API_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password }),
      })
      // Un proxy/servidor caído puede devolver HTML: no debe verse como "sin conexión".
      const responseData: LoginResponse | null = await res.json().catch(() => null)
      if (!res.ok || !responseData) {
        setError(
          res.status >= 500 || !responseData
            ? 'El servidor no respondió correctamente. Intenta de nuevo en unos minutos.'
            : extractErrorMessage(responseData, 'Correo o contraseña incorrectos.'),
        )
        return
      }
      localStorage.setItem('token', responseData.access_token)
      localStorage.setItem('username', responseData.nombre || 'Usuario')
      localStorage.setItem('user_email', responseData.email || data.email)
      if (onLogin) onLogin()
      else navigate('/dashboard')
    } catch (err) {
      setError(describeNetworkError(err, 'No se pudo conectar al servidor. Verifica que el backend esté activo.'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleForgotPassword = () => {
    setError('')
    setInfoMsg('Estamos trabajando en la recuperación de contraseñas. Por favor, comunícate con el administrador para restablecer tu acceso.')
  }

  return (
    <AuthCard
      title="Inicio de sesión"
      subtitle="Ingresa tus credenciales para acceder a la plataforma de análisis."
      footer={
        <>
          ¿No tienes una cuenta?{' '}
          <button
            type="button"
            className={authLinkClass}
            onClick={() => {
              if (onRegister) onRegister()
              else navigate('/register')
            }}
          >
            Crear cuenta
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <AuthField
          id="login-email"
          label="Correo electrónico"
          icon={Mail}
          type="email"
          placeholder="tu.correo@institucion.gov.co"
          error={errors.email?.message}
          registration={register('email')}
        />
        <AuthField
          id="login-password"
          label="Contraseña"
          icon={Lock}
          type="password"
          placeholder="••••••••"
          error={errors.password?.message}
          registration={register('password')}
        />

        {error && <AuthNotice variant="error">{error}</AuthNotice>}
        {infoMsg && <AuthNotice variant="info">{infoMsg}</AuthNotice>}

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-600">
            <input type="checkbox" className="size-4 accent-brand-magenta" /> Recordarme
          </label>
          <button type="button" className={authLinkClass} onClick={handleForgotPassword}>
            ¿Olvidaste tu contraseña?
          </button>
        </div>

        <button type="submit" className={authButtonClass} disabled={isLoading}>
          {isLoading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
          {isLoading ? 'Verificando...' : 'Iniciar sesión'}
        </button>
      </form>
    </AuthCard>
  )
}
```

- [ ] **Step 4: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/auth/Login.test.tsx`
Expected: PASS, 5 tests.

- [ ] **Step 5: Comprobar tipos**

Run: `pnpm exec tsc -b`
Expected: sin salida (sin errores).

- [ ] **Step 6: Commit**

```bash
git add src/components/auth/Login.tsx src/components/auth/Login.test.tsx
git commit -m "feat(auth): rediseñar Login con AuthCard y lucide-react"
```

---

### Task 4: Register

**Files:**
- Modify (reescribir): `src/components/auth/Register.tsx`
- Test: `src/components/auth/Register.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/auth/Register.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Register from './Register'

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body }),
  )
}

async function fillForm(confirm = 'secreto1') {
  await userEvent.type(screen.getByLabelText('Nombre completo'), 'Ana Pérez')
  await userEvent.type(screen.getByLabelText('Correo electrónico'), 'ana@test.com')
  await userEvent.type(screen.getByLabelText('Contraseña'), 'secreto1')
  await userEvent.type(screen.getByLabelText('Confirmar contraseña'), confirm)
  await userEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))
}

describe('Register', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('muestra el encabezado y los cuatro campos', () => {
    renderRegister()
    expect(screen.getByRole('heading', { level: 2, name: 'Crear cuenta' })).toBeInTheDocument()
    expect(screen.getByLabelText('Nombre completo')).toBeInTheDocument()
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
  })

  it('avisa cuando las contraseñas no coinciden y no llama al servidor', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    renderRegister()
    await fillForm('otra-clave')
    expect(await screen.findByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('muestra el mensaje de éxito al crear la cuenta', async () => {
    stubFetch(201, {})
    renderRegister()
    await fillForm()
    expect(await screen.findByText(/cuenta creada exitosamente/i)).toBeInTheDocument()
  })

  it('muestra el error del servidor', async () => {
    stubFetch(400, { detail: 'El correo ya está registrado' })
    renderRegister()
    await fillForm()
    expect(await screen.findByRole('alert')).toHaveTextContent('El correo ya está registrado')
  })

  it('vuelve al login con "Iniciar sesión"', async () => {
    renderRegister()
    await userEvent.click(screen.getByRole('button', { name: 'Iniciar sesión' }))
    expect(screen.getByText('pantalla login')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/auth/Register.test.tsx`
Expected: FAIL (sin `role="alert"`, y el encabezado/etiquetas actuales no coinciden en todos los casos).

- [ ] **Step 3: Reescribir Register.tsx**

Reemplazar todo el contenido de `src/components/auth/Register.tsx` por (la lógica de `onSubmit` es idéntica a la actual):

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Lock, Mail, User } from 'lucide-react'
import { API_URL, describeNetworkError, extractErrorMessage, fetchWithTimeout } from '../../api'
import { registerSchema, type RegisterFormValues } from '../../validation/registerSchema'
import AuthCard from './AuthCard'
import AuthField from './AuthField'
import AuthNotice from './AuthNotice'
import { authButtonClass, authLinkClass } from './authStyles'

interface RegisterProps {
  onRegistered?: () => void
  onBack?: () => void
}

interface RegisterResponse {
  detail?: string
  error?: string
}

export default function Register({ onRegistered, onBack }: RegisterProps = {}) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormValues) => {
    setError('')
    setIsLoading(true)
    try {
      const res = await fetchWithTimeout(`${API_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: data.nombre, email: data.email, password: data.password }),
      })
      const responseData: RegisterResponse | null = await res.json().catch(() => null)
      if (!res.ok) {
        setError(extractErrorMessage(responseData, 'Error al crear la cuenta.'))
        return
      }
      setSuccess(true)
      setTimeout(() => {
        if (onRegistered) onRegistered()
        else navigate('/login')
      }, 1500)
    } catch (err) {
      setError(describeNetworkError(err, 'No se pudo conectar al servidor. Verifica que el backend esté activo.'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthCard
      title="Crear cuenta"
      subtitle="Completa los datos para registrarte en la plataforma de análisis."
      footer={
        <>
          ¿Ya tienes una cuenta?{' '}
          <button
            type="button"
            className={authLinkClass}
            onClick={() => {
              if (onBack) onBack()
              else navigate('/login')
            }}
          >
            Iniciar sesión
          </button>
        </>
      }
    >
      {success ? (
        <AuthNotice variant="success">
          ¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...
        </AuthNotice>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <AuthField
            id="nombre"
            label="Nombre completo"
            icon={User}
            placeholder="Tu nombre y apellido"
            error={errors.nombre?.message}
            registration={register('nombre')}
          />
          <AuthField
            id="email"
            label="Correo electrónico"
            icon={Mail}
            type="email"
            placeholder="tu.correo@institucion.gov.co"
            error={errors.email?.message}
            registration={register('email')}
          />
          <AuthField
            id="password"
            label="Contraseña"
            icon={Lock}
            type="password"
            placeholder="Mínimo 6 caracteres"
            error={errors.password?.message}
            registration={register('password')}
          />
          <AuthField
            id="confirmPassword"
            label="Confirmar contraseña"
            icon={Lock}
            type="password"
            placeholder="Repite tu contraseña"
            error={errors.confirmPassword?.message}
            registration={register('confirmPassword')}
          />

          {error && <AuthNotice variant="error">{error}</AuthNotice>}

          <button type="submit" className={authButtonClass} disabled={isLoading}>
            {isLoading && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
            {isLoading ? 'Creando cuenta...' : 'Crear cuenta'}
          </button>
        </form>
      )}
    </AuthCard>
  )
}
```

- [ ] **Step 4: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/auth/Register.test.tsx`
Expected: PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
git add src/components/auth/Register.tsx src/components/auth/Register.test.tsx
git commit -m "feat(auth): rediseñar Register con AuthCard y lucide-react"
```

---

### Task 5: Verificación final

**Files:** ninguno (solo comprobaciones).

- [ ] **Step 1: Tipos**

Run: `pnpm exec tsc -b`
Expected: sin salida (sin errores).

- [ ] **Step 2: Build**

Run: `pnpm exec vite build`
Expected: línea `✓ built in …`. Sin errores de Tailwind.

- [ ] **Step 3: Toda la suite de tests**

Run: `pnpm exec vitest run`
Expected: todos pasan (los 97 previos más los 16 nuevos: 4 + 2 + 5 + 5).

- [ ] **Step 4: Lint de los archivos nuevos**

Run: `pnpm exec eslint src/components/auth`
Expected: sin errores. (Los 8 errores de `src/hooks/` ya existían y no forman parte de este cambio.)

- [ ] **Step 5: Confirmar que no quedan restos**

Run: `grep -rn "login-\|LogoIcon" src/components/auth`
Expected: sin coincidencias.

- [ ] **Step 6: Revisar visualmente**

Run: `pnpm dev` y abrir `/login` y `/register`. Comprobar: tarjeta centrada sobre fondo gris claro, logo con corazón, ojo que muestra/oculta la contraseña, avisos de error visibles. Probar también en ancho de móvil (~375 px).

- [ ] **Step 7: Prueba e2e (opcional, requiere backend)**

Run: `pnpm exec playwright test e2e/auth.spec.ts`
Expected: los tests de login encuentran un único campo `/Correo/i` y un único campo `/Contraseña/i`.
