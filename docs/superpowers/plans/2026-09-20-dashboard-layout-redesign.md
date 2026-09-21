# Rediseño del layout del dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar el marco del dashboard (barra lateral clara, navegación, avatar, menú móvil y contenedor) con Tailwind y lucide-react.

**Architecture:** Se reescribe solo el JSX y las clases de cuatro componentes existentes (`Avatar`, `NavItem`, `Sidebar`, `DashboardOKD`). Las props, la lógica de rutas y el contexto del `Outlet` no cambian. Cada componente gana su test, porque hoy el layout no tiene ninguno.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (tokens `brand-deep`, `brand-violet`, `brand-magenta`), lucide-react, react-router-dom v7, Vitest + Testing Library.

Spec: `docs/superpowers/specs/2026-09-20-dashboard-layout-redesign-design.md`

**Todos los comandos se ejecutan desde `frontend/maternanalytics`.**

**Convenciones del proyecto (aprendidas en la parte de Login/Register):**
- Los tests deben empezar importando desde `vitest` los nombres que usen (`import { describe, expect, it, vi } from 'vitest'`). El `tsconfig` no tiene los tipos globales y `pnpm exec tsc -b` falla si faltan.
- Con la suite completa hay timeouts esporádicos a 5 s en esta máquina. Si ocurren, repetir con `pnpm exec vitest run --testTimeout=30000`.
- Los mensajes de commit terminan con `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

**Restricciones existentes que no se deben romper**
- `src/App.test.tsx` mockea `./components/dashboard/Sidebar` (exporta `Sidebar`) y `./hooks/useDashboardData`. La exportación con nombre `Sidebar` y su ruta deben seguir igual.
- `e2e/dashboard.spec.ts` usa `page.getByRole('main')`: debe seguir habiendo un único `<main>`.

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/components/dashboard/Avatar.tsx` | Reescribir | Círculo con la inicial |
| `src/components/dashboard/NavItem.tsx` | Reescribir | Ítem de navegación con indicador de archivo |
| `src/components/dashboard/NavItem.test.tsx` | Crear | Test del ítem |
| `src/components/dashboard/Sidebar.tsx` | Reescribir | Barra lateral / cajón móvil |
| `src/components/dashboard/Sidebar.test.tsx` | Crear | Test de la barra |
| `src/components/DashboardOKD.tsx` | Modificar (solo el JSX del `return` y los imports) | Marco, barra móvil y overlay |
| `src/components/DashboardOKD.test.tsx` | Crear | Test del marco y del menú móvil |

---

### Task 1: Avatar y NavItem

**Files:**
- Modify (reescribir): `src/components/dashboard/Avatar.tsx`
- Modify (reescribir): `src/components/dashboard/NavItem.tsx`
- Test: `src/components/dashboard/NavItem.test.tsx`

- [ ] **Step 1: Escribir el test de NavItem que falla**

Crear `src/components/dashboard/NavItem.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NavItem } from './NavItem'

const icon = <svg data-testid="icono" />

describe('NavItem', () => {
  it('muestra el icono y la etiqueta y llama a onClick', async () => {
    const onClick = vi.fn()
    render(<NavItem icon={icon} label="Historial" active={false} onClick={onClick} />)
    expect(screen.getByTestId('icono')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Historial' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('marca el ítem activo con aria-current', () => {
    render(<NavItem icon={icon} label="Historial" active onClick={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Historial' })).toHaveAttribute('aria-current', 'page')
  })

  it('no marca aria-current en un ítem inactivo', () => {
    render(<NavItem icon={icon} label="Historial" active={false} onClick={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Historial' })).not.toHaveAttribute('aria-current')
  })

  it('no muestra indicadores sin status', () => {
    render(<NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} />)
    expect(screen.queryByLabelText('Archivo cargado correctamente')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Error en el archivo cargado')).not.toBeInTheDocument()
  })

  it('muestra el indicador de archivo cargado', () => {
    render(<NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} status={{ hasFile: true }} />)
    expect(screen.getByLabelText('Archivo cargado correctamente')).toBeInTheDocument()
    expect(screen.queryByLabelText('Error en el archivo cargado')).not.toBeInTheDocument()
  })

  it('el indicador de error tiene prioridad sobre el de archivo cargado', () => {
    render(
      <NavItem icon={icon} label="Mortalidad" active={false} onClick={vi.fn()} status={{ hasFile: true, hasError: true }} />,
    )
    expect(screen.getByLabelText('Error en el archivo cargado')).toBeInTheDocument()
    expect(screen.queryByLabelText('Archivo cargado correctamente')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/NavItem.test.tsx`
Expected: FAIL en los tests de indicadores (el `NavItem` actual usa `<span aria-label>` sin rol y estilos por clase, y el botón no tiene `type`); puede que alguno pase. Anotar cuáles fallan.

- [ ] **Step 3: Reescribir Avatar**

Reemplazar todo el contenido de `src/components/dashboard/Avatar.tsx`:

```tsx
interface AvatarProps {
  letter: string
  className?: string
}

export function Avatar({ letter, className = '' }: AvatarProps) {
  return (
    <div
      className={`flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-deep text-sm font-semibold text-white ${className}`.trim()}
      aria-hidden="true"
    >
      {letter}
    </div>
  )
}
```

- [ ] **Step 4: Reescribir NavItem**

Reemplazar todo el contenido de `src/components/dashboard/NavItem.tsx`:

```tsx
import type { ReactNode } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'

export interface NavItemStatus {
  hasFile?: boolean
  hasError?: boolean
}

export interface NavItemProps {
  icon: ReactNode
  label: string
  active: boolean
  onClick: () => void
  status?: NavItemStatus
  ariaLabel?: string
}

export function NavItem({
  icon,
  label,
  active,
  onClick,
  status,
  ariaLabel,
}: NavItemProps) {
  const isError = Boolean(status?.hasError)
  const isSuccess = Boolean(status?.hasFile) && !isError

  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? 'page' : undefined}
      aria-label={ariaLabel}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
        active ? 'bg-brand-magenta/10 text-brand-magenta' : 'text-slate-600 hover:bg-slate-100'
      }`}
    >
      {icon}
      <span className="flex-1">{label}</span>
      {isSuccess && (
        <CheckCircle
          role="img"
          aria-label="Archivo cargado correctamente"
          className="size-4 shrink-0 text-green-600"
        />
      )}
      {isError && (
        <AlertCircle
          role="img"
          aria-label="Error en el archivo cargado"
          className="size-4 shrink-0 text-red-600"
        />
      )}
    </button>
  )
}
```

- [ ] **Step 5: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/NavItem.test.tsx`
Expected: PASS, 6 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 6: Commit**

```bash
git add src/components/dashboard/Avatar.tsx src/components/dashboard/NavItem.tsx src/components/dashboard/NavItem.test.tsx
git commit -m "feat(dashboard): rediseñar Avatar y NavItem con Tailwind y lucide-react"
```

---

### Task 2: Sidebar

**Files:**
- Modify (reescribir): `src/components/dashboard/Sidebar.tsx`
- Test: `src/components/dashboard/Sidebar.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/dashboard/Sidebar.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar, type SidebarProps } from './Sidebar'

function renderSidebar(overrides: Partial<SidebarProps> = {}) {
  const props: SidebarProps = {
    user: { username: 'Ana Pérez', email: 'ana@test.com', avatarLetter: 'A' },
    activeView: 'analisis',
    onNavigate: vi.fn(),
    fileStatus: {},
    onLogout: vi.fn(),
    ...overrides,
  }
  render(<Sidebar {...props} />)
  return props
}

describe('Sidebar', () => {
  it('muestra la marca, la navegación y los tres grupos', () => {
    renderSidebar()
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).toBeInTheDocument()
    expect(screen.getByText('Carga de Datos')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Mortalidad Materna/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Morbilidad Extrema/ })).toBeInTheDocument()
    expect(screen.getByText('Administración')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toBeInTheDocument()
  })

  it('marca solo la vista activa con aria-current', () => {
    renderSidebar({ activeView: 'historial' })
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).not.toHaveAttribute('aria-current')
  })

  it('llama a onNavigate con la vista de cada ítem', async () => {
    const { onNavigate } = renderSidebar()
    await userEvent.click(screen.getByRole('button', { name: /Dashboard Analítico/ }))
    await userEvent.click(screen.getByRole('button', { name: /Mortalidad Materna/ }))
    await userEvent.click(screen.getByRole('button', { name: /Morbilidad Extrema/ }))
    await userEvent.click(screen.getByRole('button', { name: /Historial de Cargas/ }))
    expect(onNavigate).toHaveBeenNthCalledWith(1, 'analisis')
    expect(onNavigate).toHaveBeenNthCalledWith(2, 'mortalidad')
    expect(onNavigate).toHaveBeenNthCalledWith(3, 'morbilidad')
    expect(onNavigate).toHaveBeenNthCalledWith(4, 'historial')
  })

  it('muestra los indicadores de archivo cargado y de error', () => {
    renderSidebar({
      fileStatus: { mortalidad: { hasFile: true }, morbilidad: { hasFile: true, hasError: true } },
    })
    expect(screen.getByLabelText('Archivo cargado correctamente')).toBeInTheDocument()
    expect(screen.getByLabelText('Error en el archivo cargado')).toBeInTheDocument()
  })

  it('muestra el usuario y su correo', () => {
    renderSidebar()
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('ana@test.com')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
  })

  it('muestra un texto por defecto si no hay correo', () => {
    renderSidebar({ user: { username: 'Ana Pérez', avatarLetter: 'A' } })
    expect(screen.getByText('VidaMaterna Analytics')).toBeInTheDocument()
  })

  it('llama a onLogout al cerrar sesión', async () => {
    const { onLogout } = renderSidebar()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(onLogout).toHaveBeenCalledTimes(1)
  })

  it('llama a onMobileClose con el botón de cerrar menú', async () => {
    const onMobileClose = vi.fn()
    renderSidebar({ onMobileClose })
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar menú' }))
    expect(onMobileClose).toHaveBeenCalledTimes(1)
  })

  it('oculta el cajón en móvil cuando está cerrado y lo muestra cuando está abierto', () => {
    const { rerender } = render(
      <Sidebar
        user={{ username: 'Ana', avatarLetter: 'A' }}
        activeView="analisis"
        onNavigate={vi.fn()}
        fileStatus={{}}
        onLogout={vi.fn()}
      />,
    )
    expect(screen.getByRole('complementary')).toHaveClass('-translate-x-full')

    rerender(
      <Sidebar
        user={{ username: 'Ana', avatarLetter: 'A' }}
        activeView="analisis"
        onNavigate={vi.fn()}
        fileStatus={{}}
        onLogout={vi.fn()}
        isMobileOpen
      />,
    )
    expect(screen.getByRole('complementary')).toHaveClass('translate-x-0')
    expect(screen.getByRole('complementary')).not.toHaveClass('-translate-x-full')
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/Sidebar.test.tsx`
Expected: FAIL (no hay `nav` con nombre "Navegación principal" y no existen las clases `-translate-x-full`); anotar cuáles fallan.

- [ ] **Step 3: Reescribir Sidebar**

Reemplazar todo el contenido de `src/components/dashboard/Sidebar.tsx`:

```tsx
import { Heart, History, LayoutDashboard, LogOut, Upload, X } from 'lucide-react'
import type { ActiveView } from '../../hooks/navigation/useActiveView'
import { NavItem } from './NavItem'
import { Avatar } from './Avatar'

export interface FileIndicator {
  hasFile?: boolean
  hasError?: boolean
}

export interface DashboardFileStatus {
  mortalidad?: FileIndicator
  morbilidad?: FileIndicator
}

export interface SidebarProps {
  user: {
    username: string
    email?: string
    avatarLetter: string
  }
  activeView: ActiveView
  onNavigate: (view: ActiveView) => void
  fileStatus: DashboardFileStatus
  onLogout: () => void
  isMobileOpen?: boolean
  onMobileClose?: () => void
}

const ICON_CLASS = 'size-5 shrink-0'
const SECTION_TITLE_CLASS =
  'px-3 pb-1 pt-5 text-xs font-semibold uppercase tracking-wider text-slate-400'

export function Sidebar({
  user,
  activeView,
  onNavigate,
  fileStatus,
  onLogout,
  isMobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
        isMobileOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-magenta text-white">
          <Heart className="size-5" aria-hidden="true" />
        </div>
        <h2 className="flex-1 text-lg font-bold text-brand-deep">
          Vida<span className="text-brand-magenta">Materna</span>
        </h2>
        <button
          type="button"
          onClick={onMobileClose}
          title="Cerrar menú"
          aria-label="Cerrar menú"
          className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <X className="size-5" aria-hidden="true" />
        </button>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 space-y-1 overflow-y-auto px-3">
        <NavItem
          icon={<LayoutDashboard className={ICON_CLASS} aria-hidden="true" />}
          label="Dashboard Analítico"
          active={activeView === 'analisis'}
          onClick={() => onNavigate('analisis')}
        />

        <h3 className={SECTION_TITLE_CLASS}>Carga de Datos</h3>

        <NavItem
          icon={<Upload className={ICON_CLASS} aria-hidden="true" />}
          label="Mortalidad Materna"
          active={activeView === 'mortalidad'}
          status={fileStatus.mortalidad}
          onClick={() => onNavigate('mortalidad')}
        />

        <NavItem
          icon={<Upload className={ICON_CLASS} aria-hidden="true" />}
          label="Morbilidad Extrema"
          active={activeView === 'morbilidad'}
          status={fileStatus.morbilidad}
          onClick={() => onNavigate('morbilidad')}
        />

        <h3 className={SECTION_TITLE_CLASS}>Administración</h3>

        <NavItem
          icon={<History className={ICON_CLASS} aria-hidden="true" />}
          label="Historial de Cargas"
          active={activeView === 'historial'}
          onClick={() => onNavigate('historial')}
        />
      </nav>

      <div className="flex items-center gap-3 border-t border-slate-200 p-4">
        <Avatar letter={user.avatarLetter} />
        <div className="min-w-0 flex-1">
          <strong className="block truncate text-sm text-slate-900" title={user.username}>
            {user.username}
          </strong>
          <small className="block truncate text-xs text-slate-500" title={user.email || 'VidaMaterna Analytics'}>
            {user.email || 'VidaMaterna Analytics'}
          </small>
        </div>
        <button
          type="button"
          onClick={onLogout}
          title="Cerrar sesión"
          aria-label="Cerrar sesión"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-brand-magenta"
        >
          <LogOut className="size-5" aria-hidden="true" />
        </button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 4: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/Sidebar.test.tsx`
Expected: PASS, 9 tests.

Run: `pnpm exec vitest run src/App.test.tsx`
Expected: PASS, 3 tests (mockea `Sidebar`; debe seguir exportándose con ese nombre).

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/Sidebar.tsx src/components/dashboard/Sidebar.test.tsx
git commit -m "feat(dashboard): rediseñar Sidebar clara con lucide-react"
```

---

### Task 3: DashboardOKD

**Files:**
- Modify: `src/components/DashboardOKD.tsx` (imports y el JSX del `return`; la lógica no cambia)
- Test: `src/components/DashboardOKD.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/DashboardOKD.test.tsx`:

```tsx
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DashboardOKD from './DashboardOKD'

vi.mock('../hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    username: 'Ana Pérez',
    email: 'ana@test.com',
    avatarLetter: 'A',
    mortalidadFile: null,
    mortalidadError: null,
    morbilidadFile: null,
    morbilidadError: null,
  }),
}))

function renderLayout(path = '/dashboard') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<DashboardOKD />}>
          <Route path="dashboard" element={<p>vista analisis</p>} />
          <Route path="historial" element={<p>vista historial</p>} />
        </Route>
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('DashboardOKD', () => {
  beforeEach(() => localStorage.clear())

  it('muestra la vista hija dentro de un único main y los datos del usuario', () => {
    renderLayout()
    expect(screen.getAllByRole('main')).toHaveLength(1)
    expect(screen.getByRole('main')).toHaveTextContent('vista analisis')
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('ana@test.com')).toBeInTheDocument()
  })

  it('marca como activa la vista de la URL actual', () => {
    renderLayout('/historial')
    expect(screen.getByRole('button', { name: /Historial de Cargas/ })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: /Dashboard Analítico/ })).not.toHaveAttribute('aria-current')
  })

  it('abre el menú móvil con "Abrir menú" y lo cierra al pulsar el fondo', async () => {
    renderLayout()
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    expect(screen.getByTestId('sidebar-overlay')).toBeInTheDocument()
    expect(screen.getByRole('complementary')).toHaveClass('translate-x-0')

    await userEvent.click(screen.getByTestId('sidebar-overlay'))
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
    expect(screen.getByRole('complementary')).toHaveClass('-translate-x-full')
  })

  it('cierra el menú móvil con el botón "Cerrar menú"', async () => {
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar menú' }))
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
  })

  it('navegar desde el menú cambia de vista y cierra el menú', async () => {
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Abrir menú' }))
    await userEvent.click(screen.getByRole('button', { name: /Historial de Cargas/ }))
    expect(await screen.findByText('vista historial')).toBeInTheDocument()
    expect(screen.queryByTestId('sidebar-overlay')).not.toBeInTheDocument()
  })

  it('cerrar sesión borra la sesión y lleva al login', async () => {
    localStorage.setItem('token', 'tok')
    renderLayout()
    await userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }))
    expect(await screen.findByText('pantalla login')).toBeInTheDocument()
    expect(localStorage.getItem('token')).toBeNull()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/DashboardOKD.test.tsx`
Expected: FAIL (no existe `data-testid="sidebar-overlay"` ni las clases `translate-x-*` en el `aside`, y `getByRole('main')` puede coincidir mal); anotar cuáles fallan.

- [ ] **Step 3: Cambiar los imports**

En `src/components/DashboardOKD.tsx`, sustituir la línea

```tsx
import { MenuIcon } from './icons'
```

por

```tsx
import { Menu } from 'lucide-react'
```

- [ ] **Step 4: Reemplazar el JSX del return**

En `src/components/DashboardOKD.tsx`, reemplazar todo el bloque `return ( ... )` de la función por (la lógica de arriba —`activeView`, `handleNavigate`, `handleLogout`, el estado— no se toca):

```tsx
  return (
    <div className="flex min-h-screen bg-slate-50">
      {isMobileNavOpen && (
        <div
          data-testid="sidebar-overlay"
          aria-hidden="true"
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
          onClick={() => setIsMobileNavOpen(false)}
        />
      )}

      <Sidebar
        user={{ username: data.username, email: data.email, avatarLetter: data.avatarLetter }}
        activeView={activeView}
        onNavigate={handleNavigate}
        fileStatus={{
          mortalidad: {
            hasFile: Boolean(data.mortalidadFile),
            hasError: Boolean(data.mortalidadError),
          },
          morbilidad: {
            hasFile: Boolean(data.morbilidadFile),
            hasError: Boolean(data.morbilidadError),
          },
        }}
        onLogout={handleLogout}
        isMobileOpen={isMobileNavOpen}
        onMobileClose={() => setIsMobileNavOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
          <button
            type="button"
            onClick={() => setIsMobileNavOpen(true)}
            title="Abrir menú"
            aria-label="Abrir menú"
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          >
            <Menu className="size-5" aria-hidden="true" />
          </button>
          <span className="text-lg font-bold text-brand-deep">
            Vida<span className="text-brand-magenta">Materna</span>
          </span>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-7xl p-4 lg:p-8">
            <Outlet context={{ data, onNavigate: handleNavigate } satisfies DashboardOutletContext} />
          </div>
        </main>
      </div>
    </div>
  )
```

- [ ] **Step 5: Ejecutar los tests y comprobar que pasan**

Run: `pnpm exec vitest run src/components/DashboardOKD.test.tsx src/App.test.tsx`
Expected: PASS, 6 + 3 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida (en particular, sin "declared but never read" por imports sobrantes).

- [ ] **Step 6: Commit**

```bash
git add src/components/DashboardOKD.tsx src/components/DashboardOKD.test.tsx
git commit -m "feat(dashboard): rediseñar el marco del dashboard con barra móvil y overlay"
```

---

### Task 4: Verificación final

**Files:** ninguno (solo comprobaciones).

- [ ] **Step 1: Tipos**

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 2: Build**

Run: `pnpm exec vite build`
Expected: línea `✓ built in …`.

- [ ] **Step 3: Suite completa**

Run: `pnpm exec vitest run --testTimeout=30000`
Expected: todos pasan (los 113 previos más 21 nuevos: 6 + 9 + 6).

- [ ] **Step 4: Lint de los archivos tocados**

Run: `pnpm exec eslint src/components/DashboardOKD.tsx src/components/dashboard/Sidebar.tsx src/components/dashboard/NavItem.tsx src/components/dashboard/Avatar.tsx`
Expected: sin errores.

- [ ] **Step 5: Comprobar restos**

Run: `grep -rn "sidebar-okd\|nav-item-okd\|main-content-okd\|LogoIcon\|MenuIcon\|CloseIcon\|DashboardIcon\|UploadIcon\|LogoutIcon" src --include=*.tsx | grep -v "components/icons/"`
Expected: sin coincidencias. Los seis iconos propios (`LogoIcon`, `MenuIcon`, `CloseIcon`, `DashboardIcon`, `UploadIcon`, `LogoutIcon`) quedan sin ningún uso; sus archivos en `src/components/icons/` siguen ahí y no se borran en este plan.

- [ ] **Step 6: Revisión visual**

Run: `pnpm dev` y abrir `/dashboard`. Comprobar:
- Pantalla ancha: barra lateral blanca fija a la izquierda con la marca, los tres grupos y el pie con avatar.
- El ítem activo se ve en magenta suave y cambia al navegar entre vistas.
- Ancho móvil (~375 px): la barra desaparece, aparece la barra superior con el botón de menú; al pulsarlo entra el cajón con fondo oscuro, y se cierra al pulsar el fondo, la X o un ítem.
- Subir un archivo válido en Mortalidad muestra el ✓ verde junto a su ítem; uno inválido muestra el ! rojo.
