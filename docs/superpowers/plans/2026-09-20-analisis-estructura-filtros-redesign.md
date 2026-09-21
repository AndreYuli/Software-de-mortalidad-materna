# Rediseño de la estructura del Análisis y de la barra de filtros Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar la pantalla de Análisis con una sola columna, pestañas subrayadas y en píldoras, una barra de filtros horizontal (plegable en móvil) y los estados de carga, error y bienvenida, con Tailwind y lucide-react.

**Architecture:** Componentes pequeños y con un solo propósito: `MainTabs` (nuevo), `SubTabs`, `FiltersBar` (renombre de `FiltersSidebar`), `WelcomeState`, `DashboardLoadingState` y `DashboardErrorState`. Al final se recompone el JSX de `AnalysisHomeSection`, cuya lógica y props no cambian. Cada tarea deja `tsc` y los tests en verde.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (tokens `brand-deep`, `brand-violet`, `brand-magenta`), lucide-react, Vitest + Testing Library.

Spec: `docs/superpowers/specs/2026-09-20-analisis-estructura-filtros-redesign-design.md`

**Todos los comandos se ejecutan desde `frontend/maternanalytics`.**

**Convenciones del proyecto**
- Los tests empiezan importando de `vitest` los nombres que usen (`import { describe, expect, it, vi } from 'vitest'`). El `tsconfig` no tiene los tipos globales.
- Con la suite completa hay timeouts esporádicos a 5 s en esta máquina: usar `pnpm exec vitest run --testTimeout=30000`.
- Los commits terminan con `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- Los íconos decorativos de lucide llevan `aria-hidden="true"`.
- jsdom no aplica Tailwind: `hidden`, `sr-only`, etc. no ocultan nada en los tests; por eso los tests de visibilidad comprueban clases o atributos ARIA, no `toBeVisible()`.

**Restricciones existentes**
- `e2e/dashboard.spec.ts` usa `page.getByRole('combobox').first()`: el selector de Evento debe seguir siendo el primer `combobox` del DOM.
- `AnalysisHomeSection` conserva sus props y su lógica; solo cambia su JSX.

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/components/dashboard/MainTabs.tsx` | Crear | Pestañas principales subrayadas |
| `src/components/dashboard/MainTabs.test.tsx` | Crear | Test de las pestañas principales |
| `src/components/dashboard/SubTabs.tsx` | Reescribir | Subpestañas en píldoras |
| `src/components/dashboard/SubTabs.test.tsx` | Modificar | Comprobar `aria-selected` en vez de la clase `active` |
| `src/components/dashboard/FiltersSidebar.tsx` → `FiltersBar.tsx` | Renombrar y reescribir | Barra de filtros horizontal, plegable en móvil |
| `src/components/dashboard/FiltersSidebar.test.tsx` → `FiltersBar.test.tsx` | Renombrar y ampliar | Test de la barra |
| `src/components/dashboard/WelcomeState.tsx` | Reescribir | Estado sin datos |
| `src/components/dashboard/WelcomeState.test.tsx` | Crear | Test de bienvenida |
| `src/components/dashboard/DashboardLoadingState.tsx` | Reescribir | Estado de carga |
| `src/components/dashboard/DashboardErrorState.tsx` | Reescribir | Estado de error |
| `src/components/dashboard/DashboardStates.test.tsx` | Crear | Test de carga y error |
| `src/components/icons/{BloodDropIcon,HospitalIcon,DocumentIcon}.tsx` + `index.ts` | Borrar (sin usos tras la Tarea 3) | Iconos propios sustituidos |
| `src/components/dashboard/AnalysisHomeSection.tsx` | Modificar (renombre en la Tarea 2; JSX en la Tarea 4) | Composición de la pantalla |
| `src/components/NarrativaIA.tsx` | Modificar (quitar `mt-4`) | El espacio lo pone el contenedor |
| `src/components/dashboard/DashControlBar.tsx` | Borrar | Código muerto |

---

### Task 1: MainTabs y SubTabs

**Files:**
- Create: `src/components/dashboard/MainTabs.tsx`
- Test: `src/components/dashboard/MainTabs.test.tsx`
- Modify (reescribir): `src/components/dashboard/SubTabs.tsx`
- Modify: `src/components/dashboard/SubTabs.test.tsx`

- [ ] **Step 1: Escribir el test de MainTabs (falla)**

Crear `src/components/dashboard/MainTabs.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MainTabs } from './MainTabs'

describe('MainTabs', () => {
  it('muestra las tres pestañas, en orden, dentro de un tablist', () => {
    render(<MainTabs active="generalidades" onChange={vi.fn()} />)
    expect(screen.getByRole('tablist', { name: 'Secciones del análisis' })).toBeInTheDocument()
    const tabs = screen.getAllByRole('tab')
    expect(tabs.map((t) => t.textContent)).toEqual([
      'Generalidades',
      'Morbilidad (Ev. 549)',
      'Mortalidad (Ev. 550)',
    ])
  })

  it('marca solo la pestaña activa con aria-selected', () => {
    render(<MainTabs active="morbilidad" onChange={vi.fn()} />)
    expect(screen.getByRole('tab', { name: 'Morbilidad (Ev. 549)' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Generalidades' })).toHaveAttribute('aria-selected', 'false')
    expect(screen.getByRole('tab', { name: 'Mortalidad (Ev. 550)' })).toHaveAttribute('aria-selected', 'false')
  })

  it('llama a onChange con la clave de la pestaña pulsada', async () => {
    const onChange = vi.fn()
    render(<MainTabs active="generalidades" onChange={onChange} />)
    await userEvent.click(screen.getByRole('tab', { name: 'Mortalidad (Ev. 550)' }))
    expect(onChange).toHaveBeenCalledWith('mortalidad')
  })
})
```

- [ ] **Step 2: Ejecutar y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/MainTabs.test.tsx`
Expected: FAIL, no se resuelve `./MainTabs`.

- [ ] **Step 3: Crear MainTabs**

Crear `src/components/dashboard/MainTabs.tsx`:

```tsx
import type { MainTab } from '../../hooks/navigation/useDashboardTabs'

export interface MainTabsProps {
  active: MainTab
  onChange: (tab: MainTab) => void
}

const TABS: { key: MainTab; label: string }[] = [
  { key: 'generalidades', label: 'Generalidades' },
  { key: 'morbilidad', label: 'Morbilidad (Ev. 549)' },
  { key: 'mortalidad', label: 'Mortalidad (Ev. 550)' },
]

export function MainTabs({ active, onChange }: MainTabsProps) {
  return (
    <div role="tablist" aria-label="Secciones del análisis" className="flex gap-6 overflow-x-auto border-b border-slate-200">
      {TABS.map(({ key, label }) => {
        const selected = active === key
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(key)}
            className={`-mb-px shrink-0 whitespace-nowrap border-b-2 px-1 pb-3 text-sm font-medium transition ${
              selected
                ? 'border-brand-magenta text-brand-magenta'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 4: Actualizar el test de SubTabs**

En `src/components/dashboard/SubTabs.test.tsx`, reemplazar el segundo test por:

```tsx
  it('marca como activo el botón correspondiente a `active`', () => {
    render(<SubTabs active="sociodemografico" onChange={() => {}} />)
    expect(screen.getByRole('tab', { name: 'Factores Sociodemográficos' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Factores Clínicos' })).toHaveAttribute('aria-selected', 'false')
  })
```

(Los otros dos tests de ese archivo no cambian.)

- [ ] **Step 5: Ejecutar SubTabs y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/SubTabs.test.tsx`
Expected: FAIL solo en el test modificado (el `SubTabs` actual no tiene `role="tab"`).

- [ ] **Step 6: Reescribir SubTabs**

Reemplazar todo el contenido de `src/components/dashboard/SubTabs.tsx`:

```tsx
import type { SubTab } from '../../hooks/navigation/useDashboardTabs'

export interface SubTabsProps {
  active: SubTab
  onChange: (tab: SubTab) => void
}

const SUBTAB_LABELS: Record<SubTab, string> = {
  sociodemografico: 'Factores Sociodemográficos',
  clinico: 'Factores Clínicos',
}

const SUBTAB_ORDER: SubTab[] = ['sociodemografico', 'clinico']

export function SubTabs({ active, onChange }: SubTabsProps) {
  return (
    <div role="tablist" aria-label="Factores" className="flex flex-wrap gap-2">
      {SUBTAB_ORDER.map((key) => {
        const selected = active === key
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              selected ? 'bg-brand-magenta text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {SUBTAB_LABELS[key]}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 7: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/MainTabs.test.tsx src/components/dashboard/SubTabs.test.tsx`
Expected: PASS, 3 + 3 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 8: Commit**

```bash
git add src/components/dashboard/MainTabs.tsx src/components/dashboard/MainTabs.test.tsx src/components/dashboard/SubTabs.tsx src/components/dashboard/SubTabs.test.tsx
git commit -m "feat(dashboard): pestañas principales subrayadas y subpestañas en píldoras"
```

---

### Task 2: FiltersBar (renombre de FiltersSidebar)

**Files:**
- Rename + rewrite: `src/components/dashboard/FiltersSidebar.tsx` → `src/components/dashboard/FiltersBar.tsx`
- Rename + extend: `src/components/dashboard/FiltersSidebar.test.tsx` → `src/components/dashboard/FiltersBar.test.tsx`
- Modify (solo import y etiqueta): `src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Renombrar los archivos con git**

```bash
git mv src/components/dashboard/FiltersSidebar.tsx src/components/dashboard/FiltersBar.tsx
git mv src/components/dashboard/FiltersSidebar.test.tsx src/components/dashboard/FiltersBar.test.tsx
```

- [ ] **Step 2: Escribir el test (falla)**

Reemplazar todo el contenido de `src/components/dashboard/FiltersBar.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FiltersBar } from './FiltersBar'

const baseProps = {
  filterYear: '',
  onYearChange: vi.fn(),
  availableYears: [2026, 2025],
  filterMonth: '',
  onMonthChange: vi.fn(),
  filterWeek: '',
  onWeekChange: vi.fn(),
  filterDay: '',
  onDayChange: vi.fn(),
  onExport: vi.fn(),
}

describe('FiltersBar', () => {
  it('deshabilita semana y día cuando no hay año/mes seleccionados', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.getByLabelText('Semana de Reporte')).toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).toBeDisabled()
  })

  it('habilita semana al seleccionar año, y día al seleccionar mes', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByLabelText('Semana de Reporte')).not.toBeDisabled()
    expect(screen.getByLabelText('Día de Reporte')).not.toBeDisabled()
  })

  it('renderiza las 53 semanas ISO y los 31 días', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByText('Semana 53')).toBeInTheDocument()
    expect(screen.getByLabelText('Día de Reporte').querySelectorAll('option')).toHaveLength(32) // 31 + "Todos los días"
  })

  it('el botón Limpiar resetea los 4 filtros', () => {
    const onYearChange = vi.fn()
    const onMonthChange = vi.fn()
    const onWeekChange = vi.fn()
    const onDayChange = vi.fn()
    render(
      <FiltersBar
        {...baseProps}
        filterYear="2026"
        onYearChange={onYearChange}
        filterMonth="3"
        onMonthChange={onMonthChange}
        filterWeek="11"
        onWeekChange={onWeekChange}
        filterDay="15"
        onDayChange={onDayChange}
      />,
    )
    fireEvent.click(screen.getByText('Limpiar'))
    expect(onYearChange).toHaveBeenCalledWith('')
    expect(onMonthChange).toHaveBeenCalledWith('')
    expect(onWeekChange).toHaveBeenCalledWith('')
    expect(onDayChange).toHaveBeenCalledWith('')
  })

  it('no muestra Limpiar cuando no hay ningún filtro activo', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.queryByText('Limpiar')).not.toBeInTheDocument()
  })

  it('el botón Filtros despliega y pliega el panel (aria-expanded)', () => {
    render(<FiltersBar {...baseProps} />)
    const toggle = screen.getByRole('button', { name: /^Filtros/ })
    const panel = document.getElementById(toggle.getAttribute('aria-controls') as string) as HTMLElement
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(panel).toHaveClass('hidden')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(panel).not.toHaveClass('hidden')

    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(panel).toHaveClass('hidden')
  })

  it('avisa de que hay filtros activos solo cuando alguno lo está', () => {
    const { rerender } = render(<FiltersBar {...baseProps} />)
    expect(screen.queryByText('(hay filtros activos)')).not.toBeInTheDocument()

    rerender(<FiltersBar {...baseProps} filterYear="2026" />)
    expect(screen.getByText('(hay filtros activos)')).toBeInTheDocument()
  })

  it('el botón Exportar Reporte llama a onExport', () => {
    const onExport = vi.fn()
    render(<FiltersBar {...baseProps} onExport={onExport} />)
    fireEvent.click(screen.getByRole('button', { name: 'Exportar Reporte' }))
    expect(onExport).toHaveBeenCalledTimes(1)
  })

  it('el selector de Evento es el primer combobox y cambia el segmento', () => {
    const onSegmentoChange = vi.fn()
    render(
      <FiltersBar
        {...baseProps}
        segmento="ambos"
        onSegmentoChange={onSegmentoChange}
        latestMortalidad={{ id: 1 }}
        latestMorbilidad={{ id: 2 }}
      />,
    )
    expect(screen.getAllByRole('combobox')[0]).toHaveAttribute('id', 'filter-segmento')
    fireEvent.change(screen.getByLabelText('Evento'), { target: { value: 'mortalidad' } })
    expect(onSegmentoChange).toHaveBeenCalledWith('mortalidad')
  })

  it('sin segmento no muestra el selector de Evento', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.queryByLabelText('Evento')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Ejecutar y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/FiltersBar.test.tsx`
Expected: FAIL, `./FiltersBar` exporta `FiltersSidebar`, no `FiltersBar`.

- [ ] **Step 4: Reescribir FiltersBar**

Reemplazar todo el contenido de `src/components/dashboard/FiltersBar.tsx`:

```tsx
import { useState, type ReactNode } from 'react'
import { Download, SlidersHorizontal } from 'lucide-react'
import { MESES_ES } from '../../constants/dashboardConstants'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

const SEMANAS_ISO = Array.from({ length: 53 }, (_, i) => i + 1)
const DIAS_MES = Array.from({ length: 31 }, (_, i) => i + 1)

const LABEL_CLASS = 'mb-1 block text-xs font-medium text-slate-500'
const SELECT_CLASS =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400'

export interface FiltersBarProps {
  segmento?: Segmento
  onSegmentoChange?: (segmento: Segmento) => void
  latestMortalidad?: { id: number } | null
  latestMorbilidad?: { id: number } | null
  filterYear: string
  onYearChange: (year: string) => void
  availableYears: number[]
  filterMonth: string
  onMonthChange: (month: string) => void
  filterWeek: string
  onWeekChange: (week: string) => void
  filterDay: string
  onDayChange: (day: string) => void
  onExport: () => void
}

interface SelectFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  /** Ayuda para cuando el campo está deshabilitado: va en `title` y como texto para lectores de pantalla. */
  hint?: string
  children: ReactNode
}

function SelectField({ id, label, value, onChange, disabled, hint, children }: SelectFieldProps) {
  const hintId = `${id}-hint`
  return (
    <div>
      <label htmlFor={id} className={LABEL_CLASS}>
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        title={hint}
        aria-describedby={hint ? hintId : undefined}
        className={SELECT_CLASS}
      >
        {children}
      </select>
      {hint && (
        <span id={hintId} className="sr-only">
          {hint}
        </span>
      )}
    </div>
  )
}

export function FiltersBar({
  segmento,
  onSegmentoChange,
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  onYearChange,
  availableYears,
  filterMonth,
  onMonthChange,
  filterWeek,
  onWeekChange,
  filterDay,
  onDayChange,
  onExport,
}: FiltersBarProps) {
  const [open, setOpen] = useState(false)
  const hasActiveFilters = Boolean(filterYear || filterMonth || filterWeek || filterDay)

  const handleClearFilters = () => {
    onYearChange('')
    onMonthChange('')
    onWeekChange('')
    onDayChange('')
  }

  return (
    <section
      aria-label="Filtros del análisis"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-0 lg:z-10"
    >
      <div className="flex flex-wrap items-end gap-3">
        <button
          type="button"
          aria-expanded={open}
          aria-controls="filters-panel"
          onClick={() => setOpen((value) => !value)}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 lg:hidden"
        >
          <SlidersHorizontal className="size-4" aria-hidden="true" />
          Filtros
          {hasActiveFilters && (
            <>
              <span className="size-2 rounded-full bg-brand-magenta" aria-hidden="true" />
              <span className="sr-only">(hay filtros activos)</span>
            </>
          )}
        </button>

        <div
          id="filters-panel"
          className={`${
            open ? 'grid' : 'hidden'
          } w-full grid-cols-1 gap-3 sm:grid-cols-2 lg:grid lg:w-auto lg:flex-1 lg:grid-cols-[repeat(auto-fit,minmax(9rem,1fr))]`}
        >
          {segmento && onSegmentoChange && (
            <SelectField
              id="filter-segmento"
              label="Evento"
              value={segmento}
              onChange={(value) => onSegmentoChange(value as Segmento)}
            >
              <option value="ambos">549 + 550 integrados</option>
              {latestMortalidad && <option value="mortalidad">Solo mortalidad 550</option>}
              {latestMorbilidad && <option value="morbilidad">Solo morbilidad 549</option>}
            </SelectField>
          )}

          <SelectField
            id="filter-year"
            label="Año de Reporte"
            value={filterYear}
            onChange={onYearChange}
            disabled={availableYears.length === 0}
          >
            <option value="">Todos los años</option>
            {availableYears.map((y) => (
              <option key={y} value={String(y)}>
                {y}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-month"
            label="Mes de Reporte"
            value={filterMonth}
            onChange={onMonthChange}
            disabled={!filterYear}
            hint={!filterYear ? 'Selecciona un año primero para habilitar meses.' : undefined}
          >
            <option value="">Todos los meses</option>
            {MESES_ES.map((m, i) => (
              <option key={i + 1} value={String(i + 1)}>
                {m}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-week"
            label="Semana de Reporte"
            value={filterWeek}
            onChange={onWeekChange}
            disabled={!filterYear}
            hint={!filterYear ? 'Selecciona un año primero para habilitar semanas.' : undefined}
          >
            <option value="">Todas las semanas</option>
            {SEMANAS_ISO.map((w) => (
              <option key={w} value={String(w)}>
                Semana {w}
              </option>
            ))}
          </SelectField>

          <SelectField
            id="filter-day"
            label="Día de Reporte"
            value={filterDay}
            onChange={onDayChange}
            disabled={!filterMonth}
            hint={!filterMonth ? 'Selecciona un mes primero para habilitar días.' : undefined}
          >
            <option value="">Todos los días</option>
            {DIAS_MES.map((d) => (
              <option key={d} value={String(d)}>
                {d}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleClearFilters}
              title="Limpiar todos los filtros"
              className="rounded-lg px-3 py-2 text-sm font-medium text-brand-violet hover:underline"
            >
              Limpiar
            </button>
          )}
          <button
            type="button"
            onClick={onExport}
            className="inline-flex items-center gap-2 rounded-lg bg-brand-magenta px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
          >
            <Download className="size-4" aria-hidden="true" />
            Exportar Reporte
          </button>
        </div>
      </div>
    </section>
  )
}
```

Antes de sobrescribir, `cat` el `FiltersBar.tsx` actual (ex `FiltersSidebar`) y comprobar que las props, las opciones, las reglas de deshabilitado (año sin años disponibles; mes y semana sin año; día sin mes), los ids de los selectores y la acción de `Limpiar` coinciden con lo que conserva el archivo nuevo.

- [ ] **Step 5: Actualizar el único consumidor (solo el nombre)**

En `src/components/dashboard/AnalysisHomeSection.tsx` hacer exactamente estas dos sustituciones (nada más):

1. `import { FiltersSidebar } from './FiltersSidebar'` → `import { FiltersBar } from './FiltersBar'`
2. La etiqueta de apertura `<FiltersSidebar` → `<FiltersBar` (sus props no cambian; es la única aparición en el JSX).

Comprobar con `git diff` que solo cambian esas dos líneas.

- [ ] **Step 6: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/FiltersBar.test.tsx`
Expected: PASS, 10 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 7: Commit**

```bash
git add src/components/dashboard/FiltersBar.tsx src/components/dashboard/FiltersBar.test.tsx src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat(dashboard): FiltersBar, barra de filtros horizontal plegable en móvil"
```

(Los archivos renombrados con `git mv` ya están en el índice; el `git add` de los nuevos nombres es suficiente. `git status --short` debe quedar limpio.)

---

### Task 3: Estados de carga, error y bienvenida

**Files:**
- Modify (reescribir): `src/components/dashboard/WelcomeState.tsx`
- Modify (reescribir): `src/components/dashboard/DashboardLoadingState.tsx`
- Modify (reescribir): `src/components/dashboard/DashboardErrorState.tsx`
- Test: `src/components/dashboard/WelcomeState.test.tsx`, `src/components/dashboard/DashboardStates.test.tsx`
- Delete: `src/components/icons/BloodDropIcon.tsx`, `HospitalIcon.tsx`, `DocumentIcon.tsx` y sus líneas en `src/components/icons/index.ts`

- [ ] **Step 1: Escribir los tests (fallan)**

Crear `src/components/dashboard/WelcomeState.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WelcomeState } from './WelcomeState'

describe('WelcomeState', () => {
  it('muestra el título y el botón de importar, sin las opciones todavía', () => {
    render(<WelcomeState onGoToUpload={vi.fn()} />)
    expect(screen.getByRole('heading', { name: 'Análisis Epidemiológico' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Mortalidad/ })).not.toBeInTheDocument()
  })

  it('al pulsar Importar muestra las dos opciones y oculta el botón', async () => {
    render(<WelcomeState onGoToUpload={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    expect(screen.getByRole('button', { name: /Mortalidad/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Morbilidad Extrema/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Importar Datos Epidemiológicos' })).not.toBeInTheDocument()
  })

  it('Mortalidad lleva a la carga de mortalidad', async () => {
    const onGoToUpload = vi.fn()
    render(<WelcomeState onGoToUpload={onGoToUpload} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    await userEvent.click(screen.getByRole('button', { name: /Mortalidad/ }))
    expect(onGoToUpload).toHaveBeenCalledWith('mortalidad')
  })

  it('Morbilidad Extrema lleva a la carga de morbilidad', async () => {
    const onGoToUpload = vi.fn()
    render(<WelcomeState onGoToUpload={onGoToUpload} />)
    await userEvent.click(screen.getByRole('button', { name: 'Importar Datos Epidemiológicos' }))
    await userEvent.click(screen.getByRole('button', { name: /Morbilidad Extrema/ }))
    expect(onGoToUpload).toHaveBeenCalledWith('morbilidad')
  })
})
```

Crear `src/components/dashboard/DashboardStates.test.tsx`:

```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DashboardLoadingState } from './DashboardLoadingState'
import { DashboardErrorState } from './DashboardErrorState'

describe('DashboardLoadingState', () => {
  it('anuncia la carga con role="status"', () => {
    render(<DashboardLoadingState />)
    expect(screen.getByRole('status')).toHaveTextContent('Generando panel estratégico...')
  })
})

describe('DashboardErrorState', () => {
  it('muestra el mensaje con role="alert" y sin emoji', () => {
    render(<DashboardErrorState message="No se pudo cargar el análisis" onRetry={vi.fn()} />)
    const alerta = screen.getByRole('alert')
    expect(alerta).toHaveTextContent('No se pudo cargar el análisis')
    expect(alerta.textContent).not.toContain('❌')
  })

  it('Reintentar llama a onRetry', async () => {
    const onRetry = vi.fn()
    render(<DashboardErrorState message="Falla" onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
```

(Sin `onRetry` el botón recarga la página con `window.location.reload()`, que jsdom no permite sustituir; ese camino no se prueba, igual que hoy.)

- [ ] **Step 2: Ejecutar y ver el resultado contra el código actual**

Run: `pnpm exec vitest run src/components/dashboard/WelcomeState.test.tsx src/components/dashboard/DashboardStates.test.tsx`
Expected: algunos FAIL (sin `role="status"` en carga, el mensaje de error lleva el emoji). Anotar cuáles fallan y cuáles ya pasan.

- [ ] **Step 3: Reescribir WelcomeState**

Antes, `cat` el `WelcomeState.tsx` actual y confirmar que el texto del párrafo y la lógica (`showChoices`, `onGoToUpload('mortalidad' | 'morbilidad')`) coinciden. Reemplazar todo su contenido:

```tsx
import { useState } from 'react'
import { Droplet, FileText, Hospital, type LucideIcon } from 'lucide-react'

export interface WelcomeStateProps {
  onGoToUpload: (view: 'mortalidad' | 'morbilidad') => void
}

const PRIMARY_BUTTON_CLASS =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-brand-magenta px-5 py-2.5 font-semibold text-white transition hover:opacity-90'

interface ChoiceButtonProps {
  icon: LucideIcon
  label: string
  sublabel: string
  onClick: () => void
}

function ChoiceButton({ icon: Icon, label, sublabel, onClick }: ChoiceButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-1 rounded-xl border border-slate-200 p-4 transition hover:border-brand-magenta hover:bg-brand-magenta/5"
    >
      <span className="mb-1 flex size-10 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <span className="font-semibold text-brand-deep">{label}</span>
      <span className="text-xs text-slate-500">{sublabel}</span>
    </button>
  )
}

export function WelcomeState({ onGoToUpload }: WelcomeStateProps) {
  const [showChoices, setShowChoices] = useState(false)

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
          <FileText className="size-7" aria-hidden="true" />
        </div>
        <h2 className="text-xl font-semibold text-brand-deep">Análisis Epidemiológico</h2>
        <p className="mx-auto mb-6 mt-2 max-w-md text-sm text-slate-500">
          Aún no hay datos para analizar. Carga los registros de los Eventos 549 (Morbilidad) y 550 (Mortalidad) del
          SIVIGILA para generar el panel de control y los modelos de clustering.
        </p>

        {!showChoices ? (
          <button type="button" className={PRIMARY_BUTTON_CLASS} onClick={() => setShowChoices(true)}>
            Importar Datos Epidemiológicos
          </button>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <ChoiceButton
              icon={Droplet}
              label="Mortalidad"
              sublabel="Evento 550"
              onClick={() => onGoToUpload('mortalidad')}
            />
            <ChoiceButton
              icon={Hospital}
              label="Morbilidad Extrema"
              sublabel="Evento 549"
              onClick={() => onGoToUpload('morbilidad')}
            />
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Reescribir DashboardLoadingState**

Reemplazar todo el contenido de `src/components/dashboard/DashboardLoadingState.tsx`:

```tsx
import { Loader2 } from 'lucide-react'

export function DashboardLoadingState() {
  return (
    <div role="status" className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-slate-600">
      <Loader2 className="size-8 animate-spin text-brand-magenta" aria-hidden="true" />
      <p>Generando panel estratégico...</p>
    </div>
  )
}
```

- [ ] **Step 5: Reescribir DashboardErrorState**

Reemplazar todo el contenido de `src/components/dashboard/DashboardErrorState.tsx`:

```tsx
import { AlertCircle } from 'lucide-react'

export interface DashboardErrorStateProps {
  message: string
  /** Si se omite, «Reintentar» recarga la página completa. */
  onRetry?: () => void
}

export function DashboardErrorState({ message, onRetry }: DashboardErrorStateProps) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
      <AlertCircle className="size-8 text-red-600" aria-hidden="true" />
      <p role="alert" className="text-sm text-red-700">
        {message}
      </p>
      <button
        type="button"
        onClick={onRetry ?? (() => window.location.reload())}
        className="inline-flex items-center justify-center rounded-lg bg-brand-magenta px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
      >
        Reintentar
      </button>
    </div>
  )
}
```

- [ ] **Step 6: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/WelcomeState.test.tsx src/components/dashboard/DashboardStates.test.tsx`
Expected: PASS, 4 + 3 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 7: Borrar los tres iconos que quedan sin uso**

Run: `grep -rnE "BloodDropIcon|HospitalIcon|DocumentIcon" src e2e --include=*.ts --include=*.tsx | grep -v "src/components/icons/"`
Expected: sin coincidencias. **Si aparece alguna, NO borrar nada y reportarlo.**

Si no hay coincidencias:

```bash
rm src/components/icons/BloodDropIcon.tsx src/components/icons/HospitalIcon.tsx src/components/icons/DocumentIcon.tsx
sed -i -E "/export \{ (BloodDropIcon|HospitalIcon|DocumentIcon) \}/d" src/components/icons/index.ts
```

Run: `grep -rnE "BloodDropIcon|HospitalIcon|DocumentIcon" src e2e` — Expected: sin coincidencias.
Run: `pnpm exec tsc -b` — Expected: sin salida.

- [ ] **Step 8: Commit**

```bash
git add -A src/components/dashboard/WelcomeState.tsx src/components/dashboard/WelcomeState.test.tsx src/components/dashboard/DashboardLoadingState.tsx src/components/dashboard/DashboardErrorState.tsx src/components/dashboard/DashboardStates.test.tsx src/components/icons
git commit -m "feat(dashboard): rediseñar los estados de carga, error y bienvenida"
```

---

### Task 4: Recomponer AnalysisHomeSection, quitar el margen de NarrativaIA y borrar DashControlBar

**Files:**
- Modify: `src/components/dashboard/AnalysisHomeSection.tsx` (imports y el JSX del `return` final; la lógica no cambia)
- Modify: `src/components/NarrativaIA.tsx` (quitar `mt-4`)
- Delete: `src/components/dashboard/DashControlBar.tsx`

`AnalysisHomeSection` no tiene tests; se protege con `tsc`, el build y la suite.

- [ ] **Step 1: Confirmar que DashControlBar no tiene usos**

Run: `grep -rn "DashControlBar" src e2e --include=*.ts --include=*.tsx | grep -v "src/components/dashboard/DashControlBar.tsx"`
Expected: sin coincidencias. **Si aparece alguna, NO borrarlo y reportarlo.**

- [ ] **Step 2: Ajustar los imports de AnalysisHomeSection**

En `src/components/dashboard/AnalysisHomeSection.tsx`:

1. Añadir, junto a los demás imports de la parte superior:

```tsx
import { CalendarClock } from 'lucide-react'
import { MainTabs } from './MainTabs'
```

2. La línea `import { FiltersBar } from './FiltersBar'` ya existe desde la Tarea 2. `SubTabs` se sigue importando y usando.

- [ ] **Step 3: Reemplazar el `return` final**

En el mismo archivo, reemplazar **todo** el bloque desde `  return (\n    <div className="dashboard-strategic-container">` hasta el final de la función (el `)` y `}` que la cierran) por:

```tsx
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-magenta">
          Vigilancia materna SIVIGILA
        </span>
        <h1 className="text-2xl font-bold text-brand-deep">Sistema de análisis epidemiológico</h1>
        <p className="text-sm text-slate-500">
          Lectura técnica de mortalidad materna 550 y morbilidad materna extrema 549
        </p>
        {ultimaSemanaReportada && (
          <p className="inline-flex w-fit items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
            <CalendarClock className="size-4" aria-hidden="true" />
            Última carga: Semana {ultimaSemanaReportada.semana} de {ultimaSemanaReportada.anio}
          </p>
        )}
      </div>

      <MainTabs active={activeTab} onChange={setActiveTab} />

      <FiltersBar
        segmento={segmento}
        onSegmentoChange={onSegmentoChange}
        latestMortalidad={latestMortalidad}
        latestMorbilidad={latestMorbilidad}
        filterYear={filterYear}
        onYearChange={onYearChange}
        availableYears={availableYears}
        filterMonth={filterMonth}
        onMonthChange={onMonthChange}
        filterWeek={filterWeek}
        onWeekChange={onWeekChange}
        filterDay={filterDay}
        onDayChange={onDayChange}
        onExport={handleExportReport}
      />

      <KpiRow
        totalCasos={metrics.totalCasos}
        totalMortalidad={metrics.totalMortalidad}
        totalMorbilidad={metrics.totalMorbilidad}
        tasaLetalidad={metrics.tasaLetalidad}
        curTot={metrics.curTot}
        prevTot={metrics.prevTot}
        yearCompareMort={metrics.yearCompareMort}
        yearCompareMorb={metrics.yearCompareMorb}
        periodo={filterMonth ? 'mes' : 'año'}
      />

      <NarrativasResumen
        latestMortalidad={latestMortalidad}
        latestMorbilidad={latestMorbilidad}
        segmento={segmento}
        filterYear={filterYear}
        filterMonth={filterMonth}
      />

      {activeTab === 'generalidades' && (
        <TrendChartsRow topCausasMortalidad={topCausasMortalidad} topCausasMorbilidad={topCausasMorbilidad} />
      )}

      {activeTab === 'morbilidad' && (
        <>
          <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

          {activeSubTab === 'sociodemografico' && (
            <>
              <DistribucionEdadRiesgo data={edadRiesgoMorbilidad} evento="Morbilidad" />
              <SociodemographicChartsSection data={sociodemograficaMorbilidad} evento="Morbilidad" />
            </>
          )}

          {activeSubTab === 'clinico' && (
            <>
              <DistribucionEdadGestacional data={edadGestacionalMorbilidad} evento="Morbilidad" />
              <CruceVariablesSection analisisId={latestMorbilidad?.id ?? null} evento="Morbilidad" />
            </>
          )}
        </>
      )}

      {activeTab === 'mortalidad' && (
        <>
          <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

          {activeSubTab === 'sociodemografico' && (
            <>
              <DistribucionEdadRiesgo data={edadRiesgoMortalidad} evento="Mortalidad" />
              <SociodemographicChartsSection data={sociodemograficaMortalidad} evento="Mortalidad" />
            </>
          )}

          {activeSubTab === 'clinico' && (
            <>
              <DistribucionEdadGestacional data={edadGestacionalMortalidad} evento="Mortalidad" />
              <CruceVariablesSection analisisId={latestMortalidad?.id ?? null} evento="Mortalidad" />
            </>
          )}
        </>
      )}

      <ExportReportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        reportData={reportExportData}
      />
    </div>
  )
}
```

Antes de reemplazar, `cat` el `return` actual y comprobar que este bloque conserva **exactamente** las mismas props en `KpiRow`, `NarrativasResumen`, `TrendChartsRow`, `DistribucionEdadRiesgo`, `SociodemographicChartsSection`, `DistribucionEdadGestacional`, `CruceVariablesSection`, `FiltersBar` (ex `FiltersSidebar`) y `ExportReportModal`, y el mismo orden condicional por pestaña y subpestaña. Usar `git diff` después para confirmar que todo lo anterior al `return` (hooks, memos, estados de carga/error/bienvenida) queda intacto.

- [ ] **Step 4: Quitar el margen de NarrativaIA**

En `src/components/NarrativaIA.tsx`, en el `div` raíz del `return`, cambiar

```tsx
    <div className="mt-4 rounded-xl border border-brand-magenta/30 bg-brand-magenta/5 p-4">
```

por

```tsx
    <div className="rounded-xl border border-brand-magenta/30 bg-brand-magenta/5 p-4">
```

- [ ] **Step 5: Borrar DashControlBar**

```bash
git rm src/components/dashboard/DashControlBar.tsx
```

- [ ] **Step 6: Comprobar**

Run: `pnpm exec tsc -b`
Expected: sin salida (sin imports sobrantes ni variables sin usar).

Run: `pnpm exec vitest run src/components/dashboard src/App.test.tsx src/components/DashboardOKD.test.tsx --testTimeout=30000`
Expected: todo pasa (incluidos los 6 de `NarrativasResumen.test.tsx`, que no se modifica).

- [ ] **Step 7: Commit**

```bash
git add src/components/dashboard/AnalysisHomeSection.tsx src/components/NarrativaIA.tsx
git commit -m "feat(dashboard): recomponer la pantalla de análisis en una columna con barra de filtros"
```

(El borrado de `DashControlBar.tsx` con `git rm` ya está en el índice y entra en este commit.)

---

### Task 5: Verificación final

**Files:** ninguno (solo comprobaciones).

- [ ] **Step 1: Tipos**

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 2: Build**

Run: `pnpm exec vite build`
Expected: línea `✓ built in …`.

- [ ] **Step 3: Suite completa**

Run: `pnpm exec vitest run --testTimeout=30000`
Expected: todos pasan. Referencia: antes de este plan había 152 tests en 33 archivos; se añaden 16 (3 de `MainTabs`, 6 netos de `FiltersBar`, 4 de `WelcomeState`, 3 de `DashboardStates`), es decir, 168 tests en 36 archivos. Si el recuento difiere, explicar por qué.

- [ ] **Step 4: Lint de los archivos tocados**

Run: `pnpm exec eslint src/components/dashboard/MainTabs.tsx src/components/dashboard/SubTabs.tsx src/components/dashboard/FiltersBar.tsx src/components/dashboard/WelcomeState.tsx src/components/dashboard/DashboardLoadingState.tsx src/components/dashboard/DashboardErrorState.tsx src/components/dashboard/AnalysisHomeSection.tsx src/components/NarrativaIA.tsx`
Expected: ningún error nuevo; solo el aviso previo de `AnalysisHomeSection.tsx` (`react-hooks/exhaustive-deps` sobre `morbKpis.edadPromedio`).

- [ ] **Step 5: Comprobar restos**

Run: `grep -rnE "filters-sidebar-okd|dashboard-strategic-container|dashboard-analysis|dash-control|tab-button|subtab-button|welcome-|btn-welcome|upload-choices|btn-choice|dashboard-loading-state|dashboard-error-state|primary-action-btn|FiltersSidebar|DashControlBar" src e2e --include=*.ts --include=*.tsx`
Expected: sin coincidencias.

Run: `grep -rnE "BloodDropIcon|HospitalIcon|DocumentIcon" src e2e`
Expected: sin coincidencias.

- [ ] **Step 6: Revisión visual**

Run: `pnpm dev`, iniciar sesión y abrir `/dashboard`.

Con datos cargados, en pantalla ancha:
- Se ve el encabezado, las pestañas subrayadas y, debajo, la barra de filtros en una fila con "Exportar Reporte" a la derecha. Al hacer scroll, la barra queda fija arriba.
- Cambiar de pestaña subraya la activa en magenta. En Morbilidad y Mortalidad aparecen las subpestañas como píldoras.
- Sin año elegido, mes y semana aparecen deshabilitados; al pasar el ratón se ve la ayuda.

En ancho móvil (~375 px):
- Solo se ven el botón "Filtros" y "Exportar Reporte" en la misma fila. Al pulsar "Filtros" se despliegan los selectores en una columna. Con algún filtro activo aparece el puntito magenta.
- La barra no queda fija.

Sin datos: la tarjeta de bienvenida con "Importar Datos Epidemiológicos", que al pulsarla ofrece Mortalidad y Morbilidad Extrema. Con el backend detenido: la tarjeta de error con "Reintentar".
