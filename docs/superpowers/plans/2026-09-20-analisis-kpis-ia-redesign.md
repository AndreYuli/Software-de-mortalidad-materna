# Rediseño de KPIs y resumen de IA del análisis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar la franja de KPIs, sus tendencias y los bloques de IA del análisis con Tailwind y lucide-react, y hacer que la tendencia diga si compara contra el mes o el año anterior.

**Architecture:** Se reescribe el JSX y las clases de `TrendBadge`, `KpiRow`, `NarrativaIA` y `ChartAiInsight`. La lógica de cada uno se conserva. `TrendBadge` y `KpiRow` ganan una prop opcional `periodo` que `AnalysisHomeSection` calcula a partir del filtro de mes. Cada componente sin test gana el suyo.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (tokens `brand-deep`, `brand-violet`, `brand-magenta`), lucide-react, Vitest + Testing Library.

Spec: `docs/superpowers/specs/2026-09-20-analisis-kpis-ia-redesign-design.md`

**Todos los comandos se ejecutan desde `frontend/maternanalytics`.**

**Convenciones del proyecto**
- Los tests empiezan importando de `vitest` los nombres que usen (`import { describe, expect, it } from 'vitest'`). El `tsconfig` no tiene los tipos globales y `pnpm exec tsc -b` falla si faltan.
- Con la suite completa hay timeouts esporádicos a 5 s en esta máquina: usar `pnpm exec vitest run --testTimeout=30000`.
- Los commits terminan con `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- Los íconos de lucide decorativos llevan `aria-hidden="true"`.

**Restricción existente:** `src/components/dashboard/NarrativasResumen.test.tsx` (6 tests) protege a `NarrativaIA` y debe pasar **sin modificarse**. Usa estos textos y roles, que no pueden cambiar: `Generar resumen IA`, `Regenerar`, `Reintentar`, `Resumen ejecutivo · Mortalidad/Morbilidad`, `role="alert"`, y que el bloque devuelva `null` (sin ningún nodo) cuando el servicio de IA no está disponible.

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/components/dashboard/TrendBadge.tsx` | Reescribir | Píldora de tendencia con ícono y base de comparación |
| `src/components/dashboard/TrendBadge.test.tsx` | Crear | Test de la píldora |
| `src/components/dashboard/KpiRow.tsx` | Reescribir | Franja de 4 KPIs |
| `src/components/dashboard/KpiRow.test.tsx` | Crear | Test de la franja |
| `src/components/dashboard/AnalysisHomeSection.tsx` | Modificar (1 línea) | Pasar `periodo` a `KpiRow` |
| `src/components/NarrativaIA.tsx` | Reescribir el JSX | Tarjeta del resumen de IA |
| `src/components/dashboard/ChartAiInsight.tsx` | Reescribir | Lectura automatizada bajo las gráficas |
| `src/components/dashboard/ChartAiInsight.test.tsx` | Crear | Test de la lectura |

---

### Task 1: TrendBadge

**Files:**
- Modify (reescribir): `src/components/dashboard/TrendBadge.tsx`
- Test: `src/components/dashboard/TrendBadge.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/dashboard/TrendBadge.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendBadge } from './TrendBadge'

describe('TrendBadge', () => {
  it('sin comparación muestra "Histórico"', () => {
    render(<TrendBadge compare={null} />)
    expect(screen.getByText('Histórico')).toBeInTheDocument()
  })

  it('con base previa 0 y casos actuales muestra "Sin base previa"', () => {
    render(<TrendBadge compare={{ cur: 4, prev: 0 }} />)
    expect(screen.getByText('Sin base previa')).toBeInTheDocument()
  })

  it('con base previa 0 y sin casos muestra "Estable"', () => {
    render(<TrendBadge compare={{ cur: 0, prev: 0 }} />)
    expect(screen.getByText('Estable')).toBeInTheDocument()
  })

  it('una subida se muestra en verde con signo y compara con el mes anterior', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} periodo="mes" />)
    const badge = screen.getByText('+50% vs mes anterior')
    expect(badge).toHaveClass('text-green-700')
  })

  it('una bajada se muestra en rojo y compara con el año anterior', () => {
    render(<TrendBadge compare={{ cur: 8, prev: 10 }} periodo="año" />)
    const badge = screen.getByText('-20% vs año anterior')
    expect(badge).toHaveClass('text-red-700')
  })

  it('sin indicar el periodo compara con "periodo anterior"', () => {
    render(<TrendBadge compare={{ cur: 15, prev: 10 }} />)
    expect(screen.getByText('+50% vs periodo anterior')).toBeInTheDocument()
  })

  it('una variación exactamente 0 mantiene la regla actual (signo + y estilo de bajada)', () => {
    render(<TrendBadge compare={{ cur: 5, prev: 5 }} periodo="mes" />)
    const badge = screen.getByText('+0% vs mes anterior')
    expect(badge).toHaveClass('text-red-700')
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/TrendBadge.test.tsx`
Expected: FAIL. El componente actual no acepta `periodo`, escribe `vs ant.` y usa clases CSS en vez de `text-green-700`/`text-red-700`. Anotar cuáles fallan.

- [ ] **Step 3: Reescribir TrendBadge**

Reemplazar todo el contenido de `src/components/dashboard/TrendBadge.tsx`:

```tsx
import { TrendingDown, TrendingUp } from 'lucide-react'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export type TrendPeriodo = 'mes' | 'año'

export interface TrendBadgeProps {
  compare: CompareResult | null
  periodo?: TrendPeriodo
}

const SUFIJOS: Record<TrendPeriodo, string> = {
  mes: 'vs mes anterior',
  año: 'vs año anterior',
}
const SUFIJO_POR_DEFECTO = 'vs periodo anterior'

const PILL_CLASS = 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium'

export function TrendBadge({ compare, periodo }: TrendBadgeProps) {
  if (!compare) return <span className="text-xs text-slate-400">Histórico</span>

  const { cur, prev } = compare
  if (prev === 0) {
    // 0 → N no es «estable»: no hay base de comparación.
    return (
      <span className={`${PILL_CLASS} bg-slate-100 text-slate-600`}>
        {cur > 0 ? 'Sin base previa' : 'Estable'}
      </span>
    )
  }

  const pct = ((cur - prev) / prev) * 100
  const sign = pct >= 0 ? '+' : ''
  const sufijo = periodo ? SUFIJOS[periodo] : SUFIJO_POR_DEFECTO
  const texto = `${sign}${pct.toFixed(0)}% ${sufijo}`

  // Más casos = verde, menos = rojo. Un 0 exacto sigue la regla anterior (estilo de bajada).
  if (pct > 0) {
    return (
      <span className={`${PILL_CLASS} bg-green-50 text-green-700`}>
        <TrendingUp className="size-3.5" aria-hidden="true" />
        {texto}
      </span>
    )
  }
  return (
    <span className={`${PILL_CLASS} bg-red-50 text-red-700`}>
      <TrendingDown className="size-3.5" aria-hidden="true" />
      {texto}
    </span>
  )
}
```

Antes de sobrescribir, `cat` el `TrendBadge.tsx` actual y comprobar que la lógica de cálculo (`prev === 0`, `pct`, `sign`, `toFixed(0)`, `pct > 0`) es la misma. El export `TrendBadge` y `TrendBadgeProps` se mantienen.

- [ ] **Step 4: Ejecutar el test y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/TrendBadge.test.tsx`
Expected: PASS, 7 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida. (`KpiRow` sigue llamando a `TrendBadge` sin `periodo`, que es opcional.)

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/TrendBadge.tsx src/components/dashboard/TrendBadge.test.tsx
git commit -m "feat(dashboard): rediseñar TrendBadge indicando si compara con mes o año anterior"
```

---

### Task 2: KpiRow y periodo en AnalysisHomeSection

**Files:**
- Modify (reescribir): `src/components/dashboard/KpiRow.tsx`
- Modify (1 línea): `src/components/dashboard/AnalysisHomeSection.tsx`
- Test: `src/components/dashboard/KpiRow.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/dashboard/KpiRow.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiRow, type KpiRowProps } from './KpiRow'

const base: KpiRowProps = {
  totalCasos: 120,
  totalMortalidad: 15,
  totalMorbilidad: 105,
  tasaLetalidad: '12.5',
  curTot: 120,
  prevTot: 100,
  yearCompareMort: { cur: 15, prev: 10 },
  yearCompareMorb: { cur: 105, prev: 117 },
}

describe('KpiRow', () => {
  it('muestra la región, las cuatro etiquetas y las cuatro cifras', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByRole('region', { name: 'Resumen epidemiológico' })).toBeInTheDocument()
    expect(screen.getByText('Casos analizados')).toBeInTheDocument()
    expect(screen.getByText('Mortalidad materna 550')).toBeInTheDocument()
    expect(screen.getByText('Morbilidad materna extrema 549')).toBeInTheDocument()
    expect(screen.getByText('Tasa de letalidad')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('105')).toBeInTheDocument()
    expect(screen.getByText('12.5%')).toBeInTheDocument()
  })

  it('muestra las tendencias con la base de comparación indicada', () => {
    render(<KpiRow {...base} periodo="mes" />)
    expect(screen.getByText('+20% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('+50% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('-10% vs mes anterior')).toBeInTheDocument()
  })

  it('usa "año anterior" cuando el periodo es el año', () => {
    render(<KpiRow {...base} periodo="año" />)
    expect(screen.getAllByText(/vs año anterior/)).toHaveLength(3)
  })

  it('sin comparación muestra "Histórico" en las tres tendencias', () => {
    render(<KpiRow {...base} yearCompareMort={null} yearCompareMorb={null} />)
    // La de casos usa curTot/prevTot, que siempre existen; las otras dos son null.
    expect(screen.getAllByText('Histórico')).toHaveLength(2)
  })

  it('con letalidad menor de 50 no muestra la alerta', () => {
    render(<KpiRow {...base} tasaLetalidad="49.9" />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })

  it('con letalidad de 50 o más muestra la alerta accesible', () => {
    render(<KpiRow {...base} tasaLetalidad="62.5" />)
    expect(screen.getByText('Valor atípicamente alto')).toBeInTheDocument()
    expect(screen.getByTitle('Valor atípicamente alto')).toBeInTheDocument()
  })

  it('con una tasa no numérica no muestra la alerta', () => {
    render(<KpiRow {...base} tasaLetalidad="N/A" />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/KpiRow.test.tsx`
Expected: FAIL (etiquetas y estructura distintas, sin prop `periodo`, sin alerta accesible). Anotar cuáles fallan.

- [ ] **Step 3: Reescribir KpiRow**

Reemplazar todo el contenido de `src/components/dashboard/KpiRow.tsx`:

```tsx
import type { ReactNode } from 'react'
import { Activity, Droplet, Hospital, Percent, TriangleAlert, type LucideIcon } from 'lucide-react'
import { TrendBadge, type TrendPeriodo } from './TrendBadge'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'

export interface KpiRowProps {
  totalCasos: number
  totalMortalidad: number
  totalMorbilidad: number
  tasaLetalidad: string
  curTot: number
  prevTot: number
  yearCompareMort: CompareResult | null
  yearCompareMorb: CompareResult | null
  periodo?: TrendPeriodo
}

const LETALIDAD_ALTA_TEXTO = 'Valor atípicamente alto'

interface KpiCellProps {
  icon: LucideIcon
  label: string
  value: string | number
  trend?: ReactNode
  alert?: boolean
}

function KpiCell({ icon: Icon, label, value, trend, alert = false }: KpiCellProps) {
  return (
    <div
      className={`flex flex-col gap-2 p-5 ${alert ? 'bg-amber-50' : 'bg-white'}`}
      title={alert ? LETALIDAD_ALTA_TEXTO : undefined}
    >
      <div className="flex items-center gap-3">
        <span
          className={`flex size-9 shrink-0 items-center justify-center rounded-full ${
            alert ? 'bg-amber-100 text-amber-700' : 'bg-brand-magenta/10 text-brand-magenta'
          }`}
        >
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="text-sm font-medium text-slate-500">{label}</span>
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <strong className={`text-3xl font-bold ${alert ? 'text-amber-700' : 'text-brand-deep'}`}>{value}</strong>
        {alert && <TriangleAlert className="size-5 text-amber-600" aria-hidden="true" />}
        {alert && <span className="sr-only">{LETALIDAD_ALTA_TEXTO}</span>}
        {trend}
      </div>
    </div>
  )
}

export function KpiRow({
  totalCasos,
  totalMortalidad,
  totalMorbilidad,
  tasaLetalidad,
  curTot,
  prevTot,
  yearCompareMort,
  yearCompareMorb,
  periodo,
}: KpiRowProps) {
  const letalidadNumerica = Number.parseFloat(tasaLetalidad)
  const shouldReviewLetalidad = Number.isFinite(letalidadNumerica) && letalidadNumerica >= 50

  return (
    <section
      className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 shadow-sm sm:grid-cols-2 lg:grid-cols-4"
      aria-label="Resumen epidemiológico"
    >
      <KpiCell
        icon={Activity}
        label="Casos analizados"
        value={totalCasos}
        trend={<TrendBadge compare={{ cur: curTot, prev: prevTot }} periodo={periodo} />}
      />
      <KpiCell
        icon={Droplet}
        label="Mortalidad materna 550"
        value={totalMortalidad}
        trend={<TrendBadge compare={yearCompareMort} periodo={periodo} />}
      />
      <KpiCell
        icon={Hospital}
        label="Morbilidad materna extrema 549"
        value={totalMorbilidad}
        trend={<TrendBadge compare={yearCompareMorb} periodo={periodo} />}
      />
      <KpiCell icon={Percent} label="Tasa de letalidad" value={`${tasaLetalidad}%`} alert={shouldReviewLetalidad} />
    </section>
  )
}
```

Antes de sobrescribir, `cat` el `KpiRow.tsx` actual y comprobar que las props existentes (`totalCasos`, `totalMortalidad`, `totalMorbilidad`, `tasaLetalidad`, `curTot`, `prevTot`, `yearCompareMort`, `yearCompareMorb`) y el umbral `>= 50` son los mismos.

- [ ] **Step 4: Pasar `periodo` desde AnalysisHomeSection**

En `src/components/dashboard/AnalysisHomeSection.tsx`, dentro del `<KpiRow ... />`, añadir una línea después de `yearCompareMorb`:

```tsx
            yearCompareMort={metrics.yearCompareMort}
            yearCompareMorb={metrics.yearCompareMorb}
            periodo={filterMonth ? 'mes' : 'año'}
          />
```

(Solo esa línea; el resto del archivo no se toca.)

- [ ] **Step 5: Ejecutar los tests y comprobar que pasan**

Run: `pnpm exec vitest run src/components/dashboard/KpiRow.test.tsx src/components/dashboard/TrendBadge.test.tsx`
Expected: PASS, 7 + 7 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 6: Commit**

```bash
git add src/components/dashboard/KpiRow.tsx src/components/dashboard/KpiRow.test.tsx src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat(dashboard): franja compacta de KPIs con tendencia mes/año"
```

---

### Task 3: NarrativaIA y ChartAiInsight

**Files:**
- Modify (reescribir el JSX): `src/components/NarrativaIA.tsx`
- Modify (reescribir): `src/components/dashboard/ChartAiInsight.tsx`
- Test: `src/components/dashboard/ChartAiInsight.test.tsx`
- Protege a `NarrativaIA` (sin modificarlo): `src/components/dashboard/NarrativasResumen.test.tsx`

- [ ] **Step 1: Escribir el test de ChartAiInsight**

Crear `src/components/dashboard/ChartAiInsight.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartAiInsight } from './ChartAiInsight'

describe('ChartAiInsight', () => {
  it('no renderiza nada sin lectura', () => {
    const { container } = render(<ChartAiInsight insight={null} />)
    expect(container.innerHTML).toBe('')
  })

  it('no renderiza nada con una lectura vacía', () => {
    const { container } = render(<ChartAiInsight insight="" />)
    expect(container.innerHTML).toBe('')
  })

  it('muestra la etiqueta y el texto de la lectura', () => {
    render(<ChartAiInsight insight="La tendencia sube en el segundo trimestre." />)
    expect(screen.getByText('Lectura automatizada')).toBeInTheDocument()
    expect(screen.getByText('La tendencia sube en el segundo trimestre.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar los tests de esta tarea contra el código actual**

Run: `pnpm exec vitest run src/components/dashboard/ChartAiInsight.test.tsx src/components/dashboard/NarrativasResumen.test.tsx`
Expected: PASS (3 + 6). Son tests de caracterización: fijan el comportamiento actual, que el rediseño no debe cambiar. Anotar el resultado.

- [ ] **Step 3: Reescribir ChartAiInsight**

Reemplazar todo el contenido de `src/components/dashboard/ChartAiInsight.tsx`:

```tsx
import { Sparkles } from 'lucide-react'

export interface ChartAiInsightProps {
  insight: string | null | undefined
}

export function ChartAiInsight({ insight }: ChartAiInsightProps) {
  if (!insight) return null

  return (
    <div className="mt-4 rounded-lg border border-brand-magenta/20 bg-brand-magenta/5 p-3">
      <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-brand-magenta">
        <Sparkles className="size-4" aria-hidden="true" />
        Lectura automatizada
      </span>
      <p className="mt-1 text-sm text-slate-700">{insight}</p>
    </div>
  )
}
```

- [ ] **Step 4: Reescribir el JSX de NarrativaIA**

En `src/components/NarrativaIA.tsx`:

1. Sustituir la línea de imports `import { useState } from 'react'` por:

```tsx
import { useState } from 'react'
import { Loader2, RefreshCw, Sparkles } from 'lucide-react'
```

2. Justo debajo de `type Estado = ...`, añadir la constante:

```tsx
const BUTTON_CLASS =
  'inline-flex items-center gap-2 rounded-lg bg-brand-magenta px-3 py-1.5 text-sm font-semibold text-white transition hover:opacity-90'
```

3. Reemplazar todo desde `if (estado === 'unavailable') return null` hasta el final del componente por:

```tsx
  if (estado === 'unavailable') return null

  return (
    <div className="mt-4 rounded-xl border border-brand-magenta/30 bg-brand-magenta/5 p-4">
      <div className="mb-3 flex items-center gap-2 font-semibold text-brand-deep">
        <Sparkles className="size-5 text-brand-magenta" aria-hidden="true" />
        <span>{titulo}</span>
      </div>

      {estado === 'idle' && (
        <button type="button" className={BUTTON_CLASS} onClick={() => generar(false)}>
          Generar resumen IA
        </button>
      )}

      {estado === 'loading' && (
        <p role="status" className="flex items-center gap-2 text-sm text-slate-600">
          <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          Generando narrativa...
        </p>
      )}

      {estado === 'success' && (
        <>
          <p className="text-sm leading-relaxed text-slate-700">{narrativa}</p>
          <div className="mt-3 flex justify-end">
            <button type="button" className={BUTTON_CLASS} onClick={() => generar(true)}>
              <RefreshCw className="size-4" aria-hidden="true" />
              Regenerar
            </button>
          </div>
        </>
      )}

      {estado === 'error' && (
        <>
          <p role="alert" className="text-sm text-red-700">
            No se pudo generar la narrativa. Intenta de nuevo.
          </p>
          <div className="mt-3">
            <button type="button" className={BUTTON_CLASS} onClick={() => generar(false)}>
              <RefreshCw className="size-4" aria-hidden="true" />
              Reintentar
            </button>
          </div>
        </>
      )}
    </div>
  )
}
```

La lógica (`useState`, `generar`, los tipos, la interfaz `NarrativaIAProps` y el comentario sobre que es opcional y asíncrona) no se toca. Usar `git diff` para confirmar que solo cambian los imports, la constante y el `return`.

- [ ] **Step 5: Ejecutar los tests y comprobar que pasan**

Run: `pnpm exec vitest run src/components/dashboard/ChartAiInsight.test.tsx src/components/dashboard/NarrativasResumen.test.tsx`
Expected: PASS, 3 + 6 tests. `NarrativasResumen.test.tsx` no se ha modificado.

Run: `pnpm exec tsc -b`
Expected: sin salida (en particular, sin errores por el tipo de `ChartAiInsight` en sus 5 consumidores: `CruceVariablesSection`, `DistribucionEdadGestacional`, `DistribucionEdadRiesgo`, `SociodemographicChartsSection`, `TrendChartsRow`).

- [ ] **Step 6: Commit**

```bash
git add src/components/NarrativaIA.tsx src/components/dashboard/ChartAiInsight.tsx src/components/dashboard/ChartAiInsight.test.tsx
git commit -m "feat(dashboard): rediseñar el resumen de IA y la lectura automatizada"
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
Expected: todos pasan: los 134 previos más 17 nuevos (7 + 7 + 3), es decir, 151 tests en 33 archivos.

- [ ] **Step 4: Lint de los archivos tocados**

Run: `pnpm exec eslint src/components/dashboard/TrendBadge.tsx src/components/dashboard/KpiRow.tsx src/components/dashboard/ChartAiInsight.tsx src/components/NarrativaIA.tsx src/components/dashboard/AnalysisHomeSection.tsx`
Expected: solo el aviso que ya existía en `AnalysisHomeSection.tsx` (`react-hooks/exhaustive-deps` sobre `morbKpis.edadPromedio`); ningún error nuevo.

- [ ] **Step 5: Comprobar restos**

Run: `grep -rnE "epidemiology-summary|summary-priority|surveillance-register|register-metric|case-fatality|kpi-trend-period|trend-badge|narrativa-ia|btn-mini-toggle|vs ant\." src --include=*.tsx --include=*.ts`
Expected: sin coincidencias.

Run: `grep -rn "BloodDropIcon\|HospitalIcon" src --include=*.tsx | grep -v "components/icons/"`
Expected: solo `WelcomeState.tsx` (sigue usándolos; sus archivos no se borran).

- [ ] **Step 6: Revisión visual**

Run: `pnpm dev`, iniciar sesión y abrir `/dashboard` con datos cargados. Comprobar:
- La franja de 4 celdas: en pantalla ancha, una fila con líneas finas entre celdas; en tablet, 2×2; en móvil, apiladas.
- Con "Todos los años": las tendencias de mortalidad y morbilidad dicen "Histórico". Con un año elegido: `vs año anterior`. Con año y mes: `vs mes anterior`.
- Una subida se ve en verde con flecha hacia arriba y una bajada en rojo.
- La tarjeta de resumen de IA en magenta suave: "Generar resumen IA" → "Generando narrativa..." → texto con botón "Regenerar".
- Bajo una gráfica con lectura: el bloque "Lectura automatizada" con la estrella.
