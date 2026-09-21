# Rediseño de las gráficas del Análisis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar las cinco gráficas del análisis con Tailwind: una tarjeta común, alturas fijas sin estilos inline, barras delgadas, colores validados y descripciones accesibles.

**Architecture:** Utilidades y constantes compartidas primero (`chartHeightClass`, `describeSeries`/`describeMatrix`, ampliación de `chartTheme`), luego un componente `ChartCard`, y después se migra cada gráfica a `ChartCard` sin tocar sus datos, hooks ni opciones de Chart.js. Cada tarea deja `tsc` y los tests en verde.

**Tech Stack:** React 18, TypeScript, Tailwind v4 (tokens `brand-deep`, `brand-violet`, `brand-magenta`), Chart.js 4 con `react-chartjs-2`, Vitest + Testing Library.

Spec: `docs/superpowers/specs/2026-09-20-analisis-graficas-redesign-design.md`

**Todos los comandos se ejecutan desde `frontend/maternanalytics`.**

**Convenciones del proyecto**
- Los tests empiezan importando de `vitest` los nombres que usen (`import { describe, expect, it } from 'vitest'`). El `tsconfig` no tiene los tipos globales.
- Con la suite completa hay timeouts esporádicos a 5 s en esta máquina: usar `pnpm exec vitest run --testTimeout=30000`.
- Los commits terminan con `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- jsdom no aplica Tailwind; `vitest-canvas-mock` permite renderizar `<canvas>` de Chart.js en los tests.

**Restricciones existentes que no se deben romper**
- Los tests actuales de `TrendChartsRow`, `DistribucionEdadRiesgo`, `DistribucionEdadGestacional`, `CruceVariablesSection` y `ChartAiInsight` deben pasar sin cambios (salvo el añadido indicado en la Tarea 3). `SociodemographicChartsSection.test.tsx` cambia solo el selector de la rejilla (Tarea 5).
- `CruceVariablesSection.test.tsx` mockea `react-chartjs-2` y lee `options` (`plugins.title.text`, `plugins.legend.title.text`, `scales.x.title.text`, `scales.y.title.text`): esas opciones no pueden cambiar.
- `chartTheme.test.ts` fija `CHART_COLORS.mortalidad` = `#c0392b` y `CHART_COLORS.morbilidad` = `#2ca02c`: esos exports no cambian.
- Los datos, hooks (`useDashboardCharts`, `useCruceVariables`), utilidades de lectura de IA, `wrapLabel`, `calculateChartHeight`, los márgenes del eje Y y todas las `options` de Chart.js se conservan tal cual.

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `src/utils/chartHeight.ts` (+ `.test.ts`) | Crear | Clase de altura fija para el contenedor de una gráfica |
| `src/utils/chartA11y.ts` (+ `.test.ts`) | Crear | Texto accesible con los datos de la gráfica |
| `src/constants/chartTheme.ts` (+ `.test.ts`) | Modificar | Color de marca, paleta categórica y estilos de barra |
| `src/components/dashboard/ChartCard.tsx` (+ `.test.tsx`) | Crear | Tarjeta común de gráfica |
| `src/components/dashboard/TrendChartsRow.tsx` (+ `.test.tsx`) | Reescribir | Causas principales |
| `src/components/dashboard/DistribucionEdadRiesgo.tsx` | Reescribir | Edad y riesgo obstétrico |
| `src/components/dashboard/DistribucionEdadGestacional.tsx` | Reescribir | Edad gestacional |
| `src/components/dashboard/SociodemographicChartsSection.tsx` (+ `.test.tsx`) | Reescribir | Factores sociodemográficos |
| `src/components/dashboard/CruceVariablesSection.tsx` | Reescribir | Cruce de variables |

---

### Task 1: Utilidades y tema de las gráficas

**Files:**
- Create: `src/utils/chartHeight.ts`, `src/utils/chartHeight.test.ts`
- Create: `src/utils/chartA11y.ts`, `src/utils/chartA11y.test.ts`
- Modify: `src/constants/chartTheme.ts`, `src/constants/chartTheme.test.ts`

- [ ] **Step 1: Escribir los tests (fallan)**

Crear `src/utils/chartHeight.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { CHART_HEIGHT_FIXED, chartHeightClass } from './chartHeight'

describe('chartHeightClass', () => {
  it('devuelve el mínimo (320 px) para alturas pequeñas', () => {
    expect(chartHeightClass(0)).toBe('h-80')
    expect(chartHeightClass(320)).toBe('h-80')
  })

  it('sube al siguiente paso cuando la altura lo supera', () => {
    expect(chartHeightClass(321)).toBe('h-[400px]')
    expect(chartHeightClass(400)).toBe('h-[400px]')
  })

  it('elige el primer paso que cubre la altura pedida', () => {
    expect(chartHeightClass(940)).toBe('h-[960px]')
  })

  it('no pasa de la altura máxima (1280 px)', () => {
    expect(chartHeightClass(1281)).toBe('h-[1280px]')
    expect(chartHeightClass(5000)).toBe('h-[1280px]')
  })

  it('expone la altura fija de las gráficas de edad (280 px)', () => {
    expect(CHART_HEIGHT_FIXED).toBe('h-[280px]')
  })
})
```

Crear `src/utils/chartA11y.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { describeMatrix, describeSeries } from './chartA11y'

describe('describeSeries', () => {
  it('lista cada categoría con su valor detrás del título', () => {
    expect(describeSeries('Zona de Residencia', ['Urbana', 'Rural'], [12, 5])).toBe(
      'Zona de Residencia. Urbana: 12; Rural: 5',
    )
  })

  it('con listas vacías devuelve solo el título', () => {
    expect(describeSeries('Etnia', [], [])).toBe('Etnia')
  })

  it('usa 0 cuando falta el valor de una categoría', () => {
    expect(describeSeries('Etnia', ['A', 'B'], [3])).toBe('Etnia. A: 3; B: 0')
  })
})

describe('describeMatrix', () => {
  it('describe cada fila con el valor de cada columna', () => {
    expect(
      describeMatrix('Cruce', ['Urbana', 'Rural'], ['0', '1'], [
        [3, 1],
        [2, 4],
      ]),
    ).toBe('Cruce. Urbana (0: 3, 1: 1); Rural (0: 2, 1: 4)')
  })

  it('sin filas devuelve solo el título', () => {
    expect(describeMatrix('Cruce', [], [], [])).toBe('Cruce')
  })
})
```

En `src/constants/chartTheme.test.ts`, cambiar la línea de imports de `./chartTheme` por:

```ts
import {
  CHART_FONT_FAMILY,
  CHART_COLORS,
  echartsBaseTextStyle,
  BRAND_COLOR,
  CATEGORICAL_PALETTE,
  BAR_STYLE_HORIZONTAL,
  BAR_STYLE_VERTICAL,
} from './chartTheme'
```

y añadir este test dentro del `describe('chartTheme', ...)`, al final:

```ts
  it('expone el color de marca, la paleta categórica y los estilos de barra delgada', () => {
    expect(BRAND_COLOR).toBe('#89005e')
    expect(CATEGORICAL_PALETTE).toHaveLength(8)
    expect(new Set(CATEGORICAL_PALETTE).size).toBe(8)
    expect(BAR_STYLE_HORIZONTAL).toMatchObject({ borderWidth: 0, maxBarThickness: 16, barPercentage: 0.6 })
    expect(BAR_STYLE_VERTICAL).toMatchObject({ borderWidth: 0, maxBarThickness: 40 })
  })
```

- [ ] **Step 2: Ejecutar y comprobar que fallan**

Run: `pnpm exec vitest run src/utils/chartHeight.test.ts src/utils/chartA11y.test.ts src/constants/chartTheme.test.ts`
Expected: FAIL (no se resuelven `./chartHeight` ni `./chartA11y`; `chartTheme` no exporta las constantes nuevas).

- [ ] **Step 3: Crear chartHeight**

Crear `src/utils/chartHeight.ts`:

```ts
// Tailwind no puede generar una clase a partir de un número calculado: se usa una tabla de
// clases literales (para que el escaneo las encuentre) y se elige el primer paso que cubre la altura.
const HEIGHT_STEPS: { px: number; className: string }[] = [
  { px: 320, className: 'h-80' },
  { px: 400, className: 'h-[400px]' },
  { px: 480, className: 'h-[480px]' },
  { px: 560, className: 'h-[560px]' },
  { px: 640, className: 'h-[640px]' },
  { px: 720, className: 'h-[720px]' },
  { px: 800, className: 'h-[800px]' },
  { px: 880, className: 'h-[880px]' },
  { px: 960, className: 'h-[960px]' },
  { px: 1040, className: 'h-[1040px]' },
  { px: 1120, className: 'h-[1120px]' },
  { px: 1200, className: 'h-[1200px]' },
  { px: 1280, className: 'h-[1280px]' },
]

/** Altura fija de las gráficas de edad (pocas barras verticales). */
export const CHART_HEIGHT_FIXED = 'h-[280px]'

/** Clase de altura para una gráfica que necesita `pixels` px; por encima del máximo devuelve el máximo. */
export function chartHeightClass(pixels: number): string {
  const step = HEIGHT_STEPS.find((s) => s.px >= pixels)
  return (step ?? HEIGHT_STEPS[HEIGHT_STEPS.length - 1]).className
}
```

- [ ] **Step 4: Crear chartA11y**

Crear `src/utils/chartA11y.ts`:

```ts
/** Texto para el `aria-label` de un canvas: el título seguido de cada categoría y su valor. */
export function describeSeries(title: string, labels: string[], values: number[]): string {
  const pares = labels.map((label, i) => `${label}: ${values[i] ?? 0}`)
  return pares.length > 0 ? `${title}. ${pares.join('; ')}` : title
}

/** Igual que `describeSeries` para una matriz filas × columnas (cruce de variables). */
export function describeMatrix(title: string, filas: string[], columnas: string[], matriz: number[][]): string {
  const partes = filas.map((fila, i) => {
    const celdas = columnas.map((columna, j) => `${columna}: ${matriz[i]?.[j] ?? 0}`)
    return `${fila} (${celdas.join(', ')})`
  })
  return partes.length > 0 ? `${title}. ${partes.join('; ')}` : title
}
```

- [ ] **Step 5: Ampliar chartTheme**

En `src/constants/chartTheme.ts`, justo después del bloque de `STATUS_COLORS` (antes de `ChartJS.defaults.font.family = ...`), añadir:

```ts
/** Color de marca para gráficas de una sola serie sin significado propio (p. ej. las sociodemográficas). */
export const BRAND_COLOR = '#89005e'

/**
 * Paleta categórica para gráficas de varias series (cruce de variables), en orden fijo.
 * Validada con `validate_palette.js --mode light`: todos los controles pasan; el contraste bajo
 * de turquesa, amarillo y rosa (< 3:1) se compensa con la leyenda visible de la gráfica.
 */
export const CATEGORICAL_PALETTE = [
  '#2a78d6',
  '#eb6834',
  '#1baf7a',
  '#eda100',
  '#e87ba4',
  '#008300',
  '#4a3aa7',
  '#e34948',
]

/** Barras delgadas: horizontales (muchas categorías) y verticales (pocas barras). */
export const BAR_STYLE_HORIZONTAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 16, barPercentage: 0.6 }
export const BAR_STYLE_VERTICAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 40 }
```

Antes de editar, `cat` el archivo y comprobar que los exports existentes (`CHART_FONT_FAMILY`, `CHART_TEXT_COLOR`, `CHART_COLORS`, `STATUS_COLORS`, `echartsBaseTextStyle`) y el registro de Chart.js quedan intactos.

- [ ] **Step 6: Ejecutar y comprobar que pasan**

Run: `pnpm exec vitest run src/utils/chartHeight.test.ts src/utils/chartA11y.test.ts src/constants/chartTheme.test.ts`
Expected: PASS (5 + 5 + 4 tests).

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 7: Validar la paleta categórica con el script de la guía**

Run (ruta del script de la skill `dataviz`; si no existe en esta máquina, anotar que no se pudo ejecutar y seguir):

```bash
node "C:/Users/lopez/AppData/Local/Temp/claude/bundled-skills/2.1.278/cea9c7640acc801b0c12590c58b1e06e/dataviz/scripts/validate_palette.js" "#2a78d6,#eb6834,#1baf7a,#eda100,#e87ba4,#008300,#4a3aa7,#e34948" --mode light
```

Expected: `ALL CHECKS PASS`, con `[WARN] Contrast vs surface` solo para `#1baf7a`, `#eda100` y `#e87ba4` (compensado por la leyenda). Cualquier `[FAIL]` es un bloqueo: reportarlo.

- [ ] **Step 8: Commit**

```bash
git add src/utils/chartHeight.ts src/utils/chartHeight.test.ts src/utils/chartA11y.ts src/utils/chartA11y.test.ts src/constants/chartTheme.ts src/constants/chartTheme.test.ts
git commit -m "feat(charts): utilidades de altura y accesibilidad, y paleta de marca y categórica"
```

---

### Task 2: ChartCard

**Files:**
- Create: `src/components/dashboard/ChartCard.tsx`
- Test: `src/components/dashboard/ChartCard.test.tsx`

- [ ] **Step 1: Escribir el test (falla)**

Crear `src/components/dashboard/ChartCard.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ChartCard } from './ChartCard'

describe('ChartCard', () => {
  it('muestra el título como h3 y el contenido', () => {
    render(
      <ChartCard title="Etnia">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByRole('heading', { level: 3, name: 'Etnia' })).toBeInTheDocument()
    expect(screen.getByText('contenido')).toBeInTheDocument()
  })

  it('muestra la etiqueta y la descripción cuando se indican', () => {
    render(
      <ChartCard title="Top 10" eyebrow="Evento 550" description="Total: 4 casos">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByText('Evento 550')).toBeInTheDocument()
    expect(screen.getByText('Total: 4 casos')).toBeInTheDocument()
  })

  it('muestra la lectura automatizada solo si hay insight', () => {
    const { rerender } = render(
      <ChartCard title="Etnia" insight="Predomina el grupo A.">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.getByText('Lectura automatizada')).toBeInTheDocument()
    expect(screen.getByText('Predomina el grupo A.')).toBeInTheDocument()

    rerender(
      <ChartCard title="Etnia" insight={null}>
        <p>contenido</p>
      </ChartCard>,
    )
    expect(screen.queryByText('Lectura automatizada')).not.toBeInTheDocument()
  })

  it('sin etiqueta ni descripción no renderiza nada extra', () => {
    const { container } = render(
      <ChartCard title="Etnia">
        <p>contenido</p>
      </ChartCard>,
    )
    expect(container.querySelector('article > div > span')).toBeNull()
    expect(container.querySelector('article > div > p')).toBeNull()
  })
})
```

- [ ] **Step 2: Ejecutar y comprobar que falla**

Run: `pnpm exec vitest run src/components/dashboard/ChartCard.test.tsx`
Expected: FAIL, no se resuelve `./ChartCard`.

- [ ] **Step 3: Crear ChartCard**

Crear `src/components/dashboard/ChartCard.tsx`:

```tsx
import type { ReactNode } from 'react'
import { ChartAiInsight } from './ChartAiInsight'

export interface ChartCardProps {
  title: string
  eyebrow?: string
  description?: string
  /** Lectura automatizada bajo la gráfica; sin texto no se muestra nada. */
  insight?: string | null
  children: ReactNode
}

export function ChartCard({ title, eyebrow, description, insight, children }: ChartCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        {eyebrow && (
          <span className="block text-xs font-semibold uppercase tracking-wider text-brand-magenta">{eyebrow}</span>
        )}
        <h3 className="text-lg font-semibold text-brand-deep">{title}</h3>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {children}
      <ChartAiInsight insight={insight} />
    </article>
  )
}
```

- [ ] **Step 4: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/ChartCard.test.tsx`
Expected: PASS, 4 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/ChartCard.tsx src/components/dashboard/ChartCard.test.tsx
git commit -m "feat(charts): ChartCard, tarjeta común de las gráficas"
```

---

### Task 3: TrendChartsRow (causas principales)

**Files:**
- Modify (reescribir): `src/components/dashboard/TrendChartsRow.tsx`
- Modify (añadir un test): `src/components/dashboard/TrendChartsRow.test.tsx`

- [ ] **Step 1: Añadir el test de accesibilidad (falla)**

En `src/components/dashboard/TrendChartsRow.test.tsx`, dentro del `describe('TrendChartsRow', ...)`, añadir al final:

```tsx
  it('cada gráfica expone una descripción accesible con sus datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(
      screen.getByRole('img', { name: 'Top 10 Causas de Mortalidad. Preeclampsia Severa: 5' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Top 10 Causas de Morbilidad. Eclampsia: 3' })).toBeInTheDocument()
  })
```

Run: `pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: FAIL solo en el test nuevo (el canvas no tiene `role="img"` ni `aria-label`); los 2 tests existentes pasan.

- [ ] **Step 2: Reescribir TrendChartsRow**

Antes, `cat src/components/dashboard/TrendChartsRow.tsx` y comprobar que las `options` de Chart.js (`indexAxis: 'y'`, tooltip `title`, ejes `x` e `y`, `afterFit` con `Y_AXIS_WIDTH_SAFETY_MARGIN`), los `insight` con `getTopCausasAiInsight` y las cadenas de texto coinciden con lo que conserva el archivo nuevo. Reemplazar todo su contenido:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale, TooltipItem } from 'chart.js'
import { BAR_STYLE_HORIZONTAL } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'
import { calculateChartHeight, wrapLabel } from '../../utils/causasChartLabels'
import { chartHeightClass } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
}

// Empíricamente, el ancho automático que Chart.js calcula para el eje Y
// queda corto para etiquetas largas envueltas en varias líneas y recorta
// el borde izquierdo del texto (verificado visualmente con datos reales;
// no es una causa raíz confirmada en el código fuente de Chart.js). Se
// agrega un margen fijo tras el cálculo automático como workaround.
// Verificado sin recorte a 1600px y 1920px (anchos de escritorio
// habituales); a ~1280px puede seguir quedando un recorte residual menor
// — pendiente si se necesita soportar pantallas más angostas.
const Y_AXIS_WIDTH_SAFETY_MARGIN = 70

interface CausasBarChartProps {
  title: string
  eyebrow: string
  data: TopCausasChartData
  emptyMessage: string
  insight: string | null
}

function CausasBarChart({ title, eyebrow, data, emptyMessage, insight }: CausasBarChartProps) {
  return (
    <ChartCard title={title} eyebrow={eyebrow} insight={insight}>
      {data.values.length > 0 ? (
        <div className={chartHeightClass(calculateChartHeight(data.labels))}>
          <Bar
            role="img"
            aria-label={describeSeries(title, data.labels, data.values)}
            data={{
              labels: data.labels.map((l) => wrapLabel(l)),
              datasets: [
                {
                  data: data.values,
                  backgroundColor: data.colors,
                  ...BAR_STYLE_HORIZONTAL,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y' as const,
              plugins: {
                legend: { display: false },
                tooltip: {
                  callbacks: {
                    title: (items: TooltipItem<'bar'>[]) => {
                      const idx = items[0]?.dataIndex
                      return idx !== undefined ? wrapLabel(data.labels[idx]) : ''
                    },
                  },
                },
              },
              scales: {
                x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: {
                  grid: { display: false },
                  afterFit: (scale: Scale) => {
                    scale.width += Y_AXIS_WIDTH_SAFETY_MARGIN
                  },
                },
              },
            }}
          />
        </div>
      ) : (
        <p className="text-sm text-slate-500">{emptyMessage}</p>
      )}
    </ChartCard>
  )
}

export function TrendChartsRow({ topCausasMortalidad, topCausasMorbilidad }: TrendChartsRowProps) {
  const topCausasMortalidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMortalidad.labels, topCausasMortalidad.values, false),
    [topCausasMortalidad],
  )

  const topCausasMorbilidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMorbilidad.labels, topCausasMorbilidad.values, true),
    [topCausasMorbilidad],
  )

  return (
    <section className="flex flex-col gap-4" aria-label="Análisis de causas principales">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wider text-brand-magenta">Priorización clínica</span>
        <h2 className="text-xl font-bold text-brand-deep">Causas principales notificadas</h2>
        <p className="text-sm text-slate-500">
          Compare los diagnósticos líderes por evento antes de pasar a variables sociodemográficas o clínicas.
        </p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <CausasBarChart
          eyebrow="Evento 550"
          title="Top 10 Causas de Mortalidad"
          data={topCausasMortalidad}
          emptyMessage="Sin registros de causas de mortalidad"
          insight={topCausasMortalidadInsight}
        />
        <CausasBarChart
          eyebrow="Evento 549"
          title="Top 10 Causas de Morbilidad"
          data={topCausasMorbilidad}
          emptyMessage="Sin registros de causas de morbilidad"
          insight={topCausasMorbilidadInsight}
        />
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS, 3 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/TrendChartsRow.tsx src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "feat(charts): rediseñar las gráficas de causas principales"
```

---

### Task 4: DistribucionEdadRiesgo y DistribucionEdadGestacional

**Files:**
- Modify (reescribir): `src/components/dashboard/DistribucionEdadRiesgo.tsx`
- Modify (reescribir): `src/components/dashboard/DistribucionEdadGestacional.tsx`
- Sus tests actuales (`DistribucionEdadRiesgo.test.tsx`, `DistribucionEdadGestacional.test.tsx`) deben pasar **sin modificarse**.

- [ ] **Step 1: Ejecutar los tests actuales como línea base**

Run: `pnpm exec vitest run src/components/dashboard/DistribucionEdadRiesgo.test.tsx src/components/dashboard/DistribucionEdadGestacional.test.tsx`
Expected: PASS (son tests de caracterización: fijan los títulos y los mensajes que no deben cambiar). Anotar el recuento.

- [ ] **Step 2: Reescribir DistribucionEdadRiesgo**

Antes, `cat` el archivo actual y comprobar que las `options` de Chart.js, `RISK_COLORS`, el `useMemo` del insight y los textos (título con y sin evento, descripción, mensaje de datos insuficientes) coinciden con lo que conserva el nuevo. Reemplazar todo su contenido:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_VERTICAL, CHART_FONT_FAMILY, STATUS_COLORS } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getEdadRiesgoAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel } from '../../utils/causasChartLabels'
import { CHART_HEIGHT_FIXED } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

export interface DistribucionEdadRiesgoData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadRiesgoProps {
  data: DistribucionEdadRiesgoData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const RISK_COLORS = [STATUS_COLORS.risk, STATUS_COLORS.safe, STATUS_COLORS.risk]

export function DistribucionEdadRiesgo({ data, evento }: DistribucionEdadRiesgoProps) {
  const insight = useMemo(() => getEdadRiesgoAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <ChartCard title="Distribución por Edad y Riesgo Obstétrico">
        <p className="text-sm text-slate-500">No hay datos suficientes de edad para generar esta gráfica.</p>
      </ChartCard>
    )
  }

  const title = `Distribución por Edad y Riesgo Obstétrico (${evento})`

  return (
    <ChartCard
      title={title}
      description="Las mujeres menores de 19 años o de 35 años en adelante tienen mayor riesgo de morbilidad y mortalidad materna."
      insight={insight}
    >
      <div className={CHART_HEIGHT_FIXED}>
        <Bar
          role="img"
          aria-label={describeSeries(title, data.labels, data.valores)}
          data={{
            labels: data.labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: data.valores,
                backgroundColor: RISK_COLORS,
                ...BAR_STYLE_VERTICAL,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                grid: { display: false },
                ticks: {
                  font: { family: CHART_FONT_FAMILY, size: 11 },
                  maxRotation: 0,
                },
              },
              y: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                ticks: { precision: 0 },
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
    </ChartCard>
  )
}
```

- [ ] **Step 3: Reescribir DistribucionEdadGestacional**

Igual: `cat` primero y comprobar `GESTACIONAL_COLORS`, las `options`, el insight (`getEdadGestacionalAiInsight`) y los textos. Reemplazar todo su contenido:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_VERTICAL, CHART_FONT_FAMILY, STATUS_COLORS } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { getEdadGestacionalAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel } from '../../utils/causasChartLabels'
import { CHART_HEIGHT_FIXED } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

export interface DistribucionEdadGestacionalData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadGestacionalProps {
  data: DistribucionEdadGestacionalData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const GESTACIONAL_COLORS = [STATUS_COLORS.risk, STATUS_COLORS.risk, STATUS_COLORS.safe, STATUS_COLORS.risk]

export function DistribucionEdadGestacional({ data, evento }: DistribucionEdadGestacionalProps) {
  const insight = useMemo(() => getEdadGestacionalAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <ChartCard title="Distribución por Edad Gestacional">
        <p className="text-sm text-slate-500">No hay datos suficientes de edad gestacional para generar esta gráfica.</p>
      </ChartCard>
    )
  }

  const title = `Distribución por Edad Gestacional (${evento})`

  return (
    <ChartCard
      title={title}
      description="Los partos pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante) tienen mayor riesgo de morbilidad y mortalidad materna. El rango a término (37-41 semanas) es el de menor riesgo."
      insight={insight}
    >
      <div className={CHART_HEIGHT_FIXED}>
        <Bar
          role="img"
          aria-label={describeSeries(title, data.labels, data.valores)}
          data={{
            labels: data.labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: data.valores,
                backgroundColor: GESTACIONAL_COLORS,
                ...BAR_STYLE_VERTICAL,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                grid: { display: false },
                ticks: {
                  font: { family: CHART_FONT_FAMILY, size: 11 },
                  maxRotation: 0,
                },
              },
              y: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                ticks: { precision: 0 },
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
    </ChartCard>
  )
}
```

- [ ] **Step 4: Ejecutar y comprobar que pasan**

Run: `pnpm exec vitest run src/components/dashboard/DistribucionEdadRiesgo.test.tsx src/components/dashboard/DistribucionEdadGestacional.test.tsx`
Expected: PASS, mismos tests que en la línea base, sin modificar ninguno.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/DistribucionEdadRiesgo.tsx src/components/dashboard/DistribucionEdadGestacional.tsx
git commit -m "feat(charts): rediseñar las gráficas de edad y edad gestacional"
```

---

### Task 5: SociodemographicChartsSection

**Files:**
- Modify (reescribir): `src/components/dashboard/SociodemographicChartsSection.tsx`
- Modify: `src/components/dashboard/SociodemographicChartsSection.test.tsx`

- [ ] **Step 1: Actualizar el test (falla)**

En `src/components/dashboard/SociodemographicChartsSection.test.tsx`, dentro del primer test, reemplazar las dos líneas

```tsx
    const grid = container.querySelector('.sociodemographic-grid')
    expect(grid).not.toBeNull()
```

por

```tsx
    const grid = container.querySelector('[data-testid="sociodemographic-grid"]')
    expect(grid).not.toBeNull()
```

(El resto del archivo no cambia.)

Run: `pnpm exec vitest run src/components/dashboard/SociodemographicChartsSection.test.tsx`
Expected: FAIL solo en ese test (el componente actual no tiene `data-testid`).

- [ ] **Step 2: Reescribir SociodemographicChartsSection**

Antes, `cat` el archivo actual y comprobar que `TITLES`, `INSIGHTS` (los cuatro textos), las variables, las `options` de Chart.js (incluido `afterFit` con `scale.width += 70`) y los mensajes coinciden. Reemplazar todo su contenido:

```tsx
import { Bar } from 'react-chartjs-2'
import { BAR_STYLE_HORIZONTAL, BRAND_COLOR, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { calculateChartHeight, wrapLabel } from '../../utils/causasChartLabels'
import { chartHeightClass } from '../../utils/chartHeight'
import { describeSeries } from '../../utils/chartA11y'

const TITLES: Record<string, string> = {
  zona_residencia: 'Zona de Residencia',
  poblacion_vulnerable: 'Población Vulnerable',
  etnia: 'Etnia',
  tipo_afiliacion: 'Tipo de Afiliación',
}

const INSIGHTS: Record<string, (labels: string[], valores: number[]) => string> = {
  zona_residencia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de zona de residencia.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `La zona ${max} concentra la mayor parte de los casos. Revise si hay correlación con tiempos de remisión y acceso a controles prenatales.`
  },
  poblacion_vulnerable: (labels, valores) => {
    if (!labels.length) return 'Sin datos de población vulnerable.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `La categoría "${max}" es la más frecuente. Considere barreras de acceso diferenciadas para este grupo.`
  },
  etnia: (labels, valores) => {
    if (!labels.length) return 'Sin datos de etnia.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `El grupo "${max}" predomina en los registros. Verifique si hay subregistro en comunidades con menor acceso a servicios.`
  },
  tipo_afiliacion: (labels, valores) => {
    if (!labels.length) return 'Sin datos de tipo de afiliación.'
    const max = labels[valores.indexOf(Math.max(...valores))]
    return `El régimen "${max}" es el más reportado. Analice posibles diferencias en oportunidad y calidad de atención por tipo de afiliación.`
  },
}

function SociodemographicBarChart({
  title,
  insightKey,
  labels,
  valores,
  total,
}: {
  title: string
  insightKey: string
  labels: string[]
  valores: number[]
  total: number
}) {
  if (!labels.length || total === 0) {
    return (
      <ChartCard title={title}>
        <p className="text-sm text-slate-500">Sin datos suficientes para esta gráfica.</p>
      </ChartCard>
    )
  }

  const insightText = INSIGHTS[insightKey]?.(labels, valores) ?? null

  return (
    <ChartCard title={title} description={`Total: ${total} casos con dato registrado`} insight={insightText}>
      <div className={chartHeightClass(calculateChartHeight(labels))}>
        <Bar
          role="img"
          aria-label={describeSeries(title, labels, valores)}
          data={{
            labels: labels.map((l) => wrapLabel(l)),
            datasets: [
              {
                data: valores,
                backgroundColor: BRAND_COLOR,
                ...BAR_STYLE_HORIZONTAL,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y' as const,
            plugins: { legend: { display: false } },
            scales: {
              x: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                ticks: { precision: 0 },
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
              y: {
                grid: { display: false },
                afterFit: (scale: import('chart.js').Scale) => {
                  scale.width += 70
                },
              },
            },
          }}
        />
      </div>
    </ChartCard>
  )
}

export interface SociodemographicChartsSectionProps {
  data: Record<string, { labels: string[]; valores: number[]; total: number; evento?: string }>
  evento: 'Mortalidad' | 'Morbilidad'
}

export function SociodemographicChartsSection({ data, evento }: SociodemographicChartsSectionProps) {
  const variables: { key: string; label: string }[] = [
    { key: 'zona_residencia', label: TITLES.zona_residencia },
    { key: 'poblacion_vulnerable', label: TITLES.poblacion_vulnerable },
    { key: 'etnia', label: TITLES.etnia },
    { key: 'tipo_afiliacion', label: TITLES.tipo_afiliacion },
  ]

  const hasAnyData = variables.some((v) => data[v.key] && data[v.key].total > 0)

  if (!hasAnyData) {
    return (
      <ChartCard title={`Factores Sociodemográficos (${evento})`}>
        <p className="text-sm text-slate-500">
          No hay datos sociodemográficos disponibles. Suba archivos con las columnas de zona, población vulnerable, etnia y tipo de afiliación.
        </p>
      </ChartCard>
    )
  }

  return (
    <section className="flex flex-col gap-4">
      <h3 className="text-lg font-semibold text-brand-deep">Factores Sociodemográficos ({evento})</h3>
      <div data-testid="sociodemographic-grid" className="grid gap-6 lg:grid-cols-2">
        {variables.map((v) => {
          const item = data[v.key]
          if (!item || item.total === 0) return null
          return (
            <SociodemographicBarChart
              key={v.key}
              title={v.label}
              insightKey={v.key}
              labels={item.labels}
              valores={item.valores}
              total={item.total}
            />
          )
        })}
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/SociodemographicChartsSection.test.tsx`
Expected: PASS, 2 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/SociodemographicChartsSection.tsx src/components/dashboard/SociodemographicChartsSection.test.tsx
git commit -m "feat(charts): rediseñar las gráficas sociodemográficas con un solo color de marca"
```

---

### Task 6: CruceVariablesSection

**Files:**
- Modify (reescribir): `src/components/dashboard/CruceVariablesSection.tsx`
- Su test actual (`CruceVariablesSection.test.tsx`) debe pasar **sin modificarse**.

- [ ] **Step 1: Ejecutar el test actual como línea base**

Run: `pnpm exec vitest run src/components/dashboard/CruceVariablesSection.test.tsx`
Expected: PASS (1 test). Anotar el resultado.

- [ ] **Step 2: Reescribir CruceVariablesSection**

Antes, `cat` el archivo actual y comprobar que `VARIABLES_SOCIO`, `VARIABLES_CLINICAS_MORTALIDAD`, `VARIABLES_CLINICAS_MORBILIDAD`, el uso de `useCruceVariables`, los `id` de los selectores (`cruce-socio-${evento}`, `cruce-clinica-${evento}`), las etiquetas, y **todas las `options` de Chart.js** (especialmente `plugins.title.text`, `plugins.legend.title.text`, `scales.x.title.text`, `scales.y.title.text` con `labels.*`) coinciden con lo que conserva el archivo nuevo. Reemplazar todo su contenido:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { Scale } from 'chart.js'
import { BAR_STYLE_HORIZONTAL, CATEGORICAL_PALETTE, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartCard } from './ChartCard'
import { calculateChartHeight, wrapLabel } from '../../utils/causasChartLabels'
import { chartHeightClass } from '../../utils/chartHeight'
import { describeMatrix } from '../../utils/chartA11y'
import { getCruceAiInsight } from '../../utils/aiChartInsights'
import { getCruceLabels } from '../../utils/cruceLabels'
import { useCruceVariables } from '../../hooks/dashboard/useCruceVariables'

const LABEL_CLASS = 'mb-1 block text-xs font-medium text-slate-500'
const SELECT_CLASS =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-brand-magenta focus:ring-2 focus:ring-brand-magenta/30'

const VARIABLES_SOCIO = [
  { key: 'zona_residencia', label: 'Zona de residencia' },
  { key: 'poblacion_vulnerable', label: 'Población vulnerable' },
  { key: 'etnia', label: 'Etnia' },
  { key: 'tipo_afiliacion', label: 'Tipo de afiliación' },
]

const VARIABLES_CLINICAS_MORTALIDAD = [
  { key: 'gestaciones', label: 'N° de gestaciones' },
  { key: 'partos_vaginales', label: 'Partos vaginales' },
  { key: 'cesareas', label: 'Cesáreas' },
  { key: 'tipo_parto', label: 'Tipo de parto' },
  { key: 'semana_gestacion_muerte', label: 'Semana de gestación (al momento del evento)' },
]

const VARIABLES_CLINICAS_MORBILIDAD = [
  { key: 'num_gestaciones', label: 'N° de gestaciones' },
  { key: 'partos_vaginales', label: 'Partos vaginales' },
  { key: 'cesareas', label: 'Cesáreas' },
  { key: 'terminacion_gestacion', label: 'Terminación de la gestación' },
  { key: 'edad_gestacional_sem', label: 'Edad gestacional (semanas)' },
  { key: 'falla_hepatica', label: 'Falla hepática' },
  { key: 'falla_renal', label: 'Falla renal' },
  { key: 'falla_coagulacion', label: 'Falla de coagulación' },
]

export interface CruceVariablesSectionProps {
  analisisId: number | null
  evento: 'Mortalidad' | 'Morbilidad'
}

export function CruceVariablesSection({ analisisId, evento }: CruceVariablesSectionProps) {
  const variablesClinicas = evento === 'Mortalidad' ? VARIABLES_CLINICAS_MORTALIDAD : VARIABLES_CLINICAS_MORBILIDAD

  const { varSocio, varClinica, setVarSocio, setVarClinica, data, loading, error } = useCruceVariables(
    analisisId,
    VARIABLES_SOCIO[0].key,
    variablesClinicas[0].key,
  )

  const varSocioLabel = VARIABLES_SOCIO.find((v) => v.key === varSocio)?.label ?? varSocio
  const varClinicaLabel = variablesClinicas.find((v) => v.key === varClinica)?.label ?? varClinica

  const insight = useMemo(
    () => getCruceAiInsight(data ?? undefined, varSocioLabel, varClinicaLabel),
    [data, varSocioLabel, varClinicaLabel],
  )

  const labels = useMemo(() => getCruceLabels(varSocioLabel, varClinicaLabel), [varSocioLabel, varClinicaLabel])

  return (
    <ChartCard
      title={`Cruce de Variables (${evento})`}
      description="Compare una variable sociodemográfica con una clínica para identificar combinaciones de mayor riesgo."
      insight={!loading && !error && data && data.total > 0 ? insight : null}
    >
      <div className="mb-4 grid gap-4 sm:grid-cols-2">
        <div>
          <label className={LABEL_CLASS} htmlFor={`cruce-socio-${evento}`}>
            Variable sociodemográfica
          </label>
          <select
            id={`cruce-socio-${evento}`}
            className={SELECT_CLASS}
            value={varSocio}
            onChange={(e) => setVarSocio(e.target.value)}
          >
            {VARIABLES_SOCIO.map((v) => (
              <option key={v.key} value={v.key}>
                {v.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={LABEL_CLASS} htmlFor={`cruce-clinica-${evento}`}>
            Variable clínica
          </label>
          <select
            id={`cruce-clinica-${evento}`}
            className={SELECT_CLASS}
            value={varClinica}
            onChange={(e) => setVarClinica(e.target.value)}
          >
            {variablesClinicas.map((v) => (
              <option key={v.key} value={v.key}>
                {v.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && (
        <p role="status" className="text-sm text-slate-500">
          Calculando cruce…
        </p>
      )}

      {!loading && error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && (!data || data.total === 0) && (
        <p className="text-sm text-slate-500">
          No hay suficientes datos con ambas variables registradas para este cruce.
        </p>
      )}

      {!loading && !error && data && data.total > 0 && (
        <div className={chartHeightClass(calculateChartHeight(data.categorias_socio))}>
          <Bar
            role="img"
            aria-label={describeMatrix(labels.title, data.categorias_socio, data.categorias_clinica, data.matriz)}
            data={{
              labels: data.categorias_socio.map((l) => wrapLabel(l)),
              datasets: data.categorias_clinica.map((cat, j) => ({
                label: cat,
                data: data.categorias_socio.map((_, i) => data.matriz[i][j]),
                backgroundColor: CATEGORICAL_PALETTE[j % CATEGORICAL_PALETTE.length],
                ...BAR_STYLE_HORIZONTAL,
              })),
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              indexAxis: 'y' as const,
              plugins: {
                title: { display: true, text: labels.title, font: { family: CHART_FONT_FAMILY } },
                legend: {
                  display: true,
                  position: 'bottom',
                  title: { display: true, text: labels.legend, font: { family: CHART_FONT_FAMILY } },
                  labels: { font: { family: CHART_FONT_FAMILY } },
                },
              },
              scales: {
                x: {
                  title: { display: true, text: labels.xAxis, font: { family: CHART_FONT_FAMILY } },
                  beginAtZero: true,
                  ticks: { precision: 0 },
                  grid: { color: 'rgba(0,0,0,0.05)' },
                },
                y: {
                  title: { display: true, text: labels.yAxis, font: { family: CHART_FONT_FAMILY } },
                  grid: { display: false },
                  afterFit: (scale: Scale) => {
                    scale.width += 70
                  },
                },
              },
            }}
          />
        </div>
      )}
    </ChartCard>
  )
}
```

Nota conocida: con más de 8 series los colores se repiten (`j % CATEGORICAL_PALETTE.length`), igual que hoy; agruparlas en "Otras" queda para un cambio aparte y no forma parte de este plan.

- [ ] **Step 3: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/CruceVariablesSection.test.tsx`
Expected: PASS, mismo test que en la línea base, sin modificarlo.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 4: Commit**

```bash
git add src/components/dashboard/CruceVariablesSection.tsx
git commit -m "feat(charts): rediseñar el cruce de variables con paleta validada"
```

---

### Task 7: Verificación final

**Files:** ninguno (solo comprobaciones).

- [ ] **Step 1: Tipos**

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 2: Build**

Run: `pnpm exec vite build`
Expected: línea `✓ built in …`.

- [ ] **Step 3: Suite completa**

Run: `pnpm exec vitest run --testTimeout=30000`
Expected: todos pasan. Referencia: antes de este plan había 168 tests en 36 archivos; se añaden 16 (5 de `chartHeight`, 5 de `chartA11y`, 1 de `chartTheme`, 4 de `ChartCard`, 1 de `TrendChartsRow`), es decir, 184 tests en 39 archivos. Si el recuento difiere, explicar por qué.

- [ ] **Step 4: Lint de los archivos tocados**

Run: `pnpm exec eslint src/utils/chartHeight.ts src/utils/chartA11y.ts src/constants/chartTheme.ts src/components/dashboard/ChartCard.tsx src/components/dashboard/TrendChartsRow.tsx src/components/dashboard/DistribucionEdadRiesgo.tsx src/components/dashboard/DistribucionEdadGestacional.tsx src/components/dashboard/SociodemographicChartsSection.tsx src/components/dashboard/CruceVariablesSection.tsx`
Expected: sin errores.

- [ ] **Step 5: Comprobar restos**

Run: `grep -rnE "chart-card-col-12|chart-card-title|epidemiology-chart-card|chart-card-heading|chart-card-eyebrow|causes-section|causes-analysis|charts-grid-row|sociodemographic-section|custom-select-wrapper|sidebar-select|field-label|SOCIO_PALETTE|CRUCE_PALETTE|className=\"sociodemographic" src --include=*.ts --include=*.tsx`
Expected: sin coincidencias. (El `data-testid="sociodemographic-grid"` que añade la Tarea 5 no es una clase y no debe aparecer aquí.)

Run: `grep -rn "style={" src --include=*.tsx | grep -v test`
Expected: sin coincidencias (no se han reintroducido estilos inline).

- [ ] **Step 6: Revisión visual**

Run: `pnpm dev`, iniciar sesión y abrir `/dashboard` con datos cargados. Comprobar:
- **Generalidades:** dos tarjetas lado a lado en pantalla ancha (una encima de otra en móvil), cada una con su altura propia y las barras horizontales delgadas: mortalidad en rojo y morbilidad en verde.
- **Morbilidad o Mortalidad, Factores Sociodemográficos:** cuatro tarjetas en 2×2 con las barras en magenta de marca (todas del mismo color dentro de cada gráfica).
- **Factores Clínicos:** la gráfica de edad gestacional con barras verticales finas (rojo = riesgo, gris = resto) y el cruce de variables con sus dos selectores en fila y la leyenda con los colores de la paleta nueva.
- Las gráficas no se ven recortadas ni con altura mínima, y bajo cada una aparece la "Lectura automatizada" cuando hay texto.
- Con un lector de pantalla o inspeccionando el DOM: cada `<canvas>` tiene `role="img"` y un `aria-label` con sus datos.
