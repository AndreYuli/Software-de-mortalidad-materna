# Corrección de nombres en gráficas "Top Causas" — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el nombre completo de cada causa CIE-10 sea siempre legible junto a su barra en "Top 10 Causas de Mortalidad" y "Top 10 Causas de Morbilidad", sin recortes ni `"..."`, tanto en el eje como en el tooltip.

**Architecture:** Se quita el límite de 2 líneas de `wrapLabel` y se agrega una función pura `calculateChartHeight` (Tasks 1-2, inicialmente ambas dentro de `TrendChartsRow.tsx`). En el Task 3 se extrae un subcomponente `CausasBarChart` que unifica la config de Chart.js (antes duplicada dos veces) con un callback de tooltip que siempre muestra el texto original completo, y — por un hallazgo de la revisión de calidad del Task 2 (`react-refresh/only-export-components`: un archivo de componente no puede exportar también funciones/constantes sueltas sin romper Fast Refresh) — `wrapLabel` y `calculateChartHeight` se mueven a un módulo de utilidades nuevo, `src/utils/causasChartLabels.ts`, siguiendo el patrón ya usado en el proyecto para helpers puros (`src/utils/aiChartInsights.ts`, `src/utils/excelValidation.ts`). `TrendChartsRow.tsx` queda como archivo de componente puro (solo `CausasBarChart` interno y `TrendChartsRow` exportado).

**Tech Stack:** React + TypeScript, Chart.js v4 vía `react-chartjs-2`, Vitest + Testing Library.

**Spec:** `docs/historico/specs/2026-09-14-nombres-graficas-top-causas-design.md`

---

## Task 1: `wrapLabel` — exportar y quitar el truncado con "..."

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`
- Test: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Abre `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx` y agrega este bloque al final del archivo (después del `describe('TrendChartsRow', ...)` que ya existe), y agrega `wrapLabel` al import existente:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow, wrapLabel } from './TrendChartsRow'
```

```tsx
describe('wrapLabel', () => {
  it('devuelve el texto tal cual si es corto', () => {
    expect(wrapLabel('Eclampsia')).toBe('Eclampsia')
  })

  it('envuelve texto largo en varias líneas sin truncar ni agregar "..."', () => {
    const texto =
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre'
    const resultado = wrapLabel(texto)
    expect(Array.isArray(resultado)).toBe(true)
    const lineas = resultado as string[]
    expect(lineas.length).toBeGreaterThan(2)
    expect(lineas.some((linea) => linea.includes('...'))).toBe(false)
    expect(lineas.join(' ')).toBe(texto)
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: FAIL — `wrapLabel` no está exportado desde `TrendChartsRow.tsx` (el import es `undefined`, la llamada `wrapLabel('Eclampsia')` lanza `TypeError: wrapLabel is not a function`).

- [ ] **Step 3: Exportar `wrapLabel` y quitar el truncado**

En `TrendChartsRow.tsx`, reemplaza:

```tsx
const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  if (lines.length > 2) return [lines[0], lines[1] + '...']
  return lines
}
```

por:

```tsx
export const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  return lines
}
```

(Único cambio real: se agrega `export` y se elimina la línea `if (lines.length > 2) return [lines[0], lines[1] + '...']`.)

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (los 4 tests: los 2 originales de `TrendChartsRow` + los 2 nuevos de `wrapLabel`).

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "fix: no truncar nombres de causas CIE-10 en wrapLabel"
```

---

## Task 2: `calculateChartHeight` — alto dinámico según líneas de etiqueta

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`
- Test: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Agrega `calculateChartHeight` al import de `TrendChartsRow.test.tsx`:

```tsx
import { TrendChartsRow, wrapLabel, calculateChartHeight } from './TrendChartsRow'
```

Agrega este bloque al final del archivo:

```tsx
describe('calculateChartHeight', () => {
  it('devuelve el mínimo (320) cuando no hay etiquetas', () => {
    expect(calculateChartHeight([])).toBe(320)
  })

  it('devuelve el mínimo (320) con pocas etiquetas cortas', () => {
    expect(calculateChartHeight(['Eclampsia', 'Sepsis'])).toBe(320)
  })

  it('crece cuando las etiquetas ocupan más líneas', () => {
    const etiquetasCortas = ['Eclampsia', 'Sepsis', 'Hemorragia']
    const etiquetasLargas = [
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre',
      'O72.1 Hemorragia postparto inmediata secundaria a atonía uterina severa con compromiso hemodinámico',
      'O99.4 Enfermedades del sistema circulatorio que complican el embarazo, el parto y el puerperio',
    ]
    expect(calculateChartHeight(etiquetasLargas)).toBeGreaterThan(calculateChartHeight(etiquetasCortas))
  })
})
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: FAIL — `calculateChartHeight` no está definido (`TypeError: calculateChartHeight is not a function`).

- [ ] **Step 3: Implementar `calculateChartHeight`**

En `TrendChartsRow.tsx`, justo después de la constante `TrendChartsRowProps` (antes de `wrapLabel`), agrega las constantes de tamaño:

```tsx
const LINE_HEIGHT = 28
const MIN_BAR_HEIGHT = 32
const AXIS_PADDING = 60
const MIN_CHART_HEIGHT = 320
```

Justo después de la función `wrapLabel` (que ya quedó exportada en el Task 1), agrega:

```tsx
export const calculateChartHeight = (labels: string[]): number => {
  if (labels.length === 0) return MIN_CHART_HEIGHT
  const totalBarsHeight = labels.reduce((sum, label) => {
    const wrapped = wrapLabel(label)
    const lineCount = Array.isArray(wrapped) ? wrapped.length : 1
    return sum + MIN_BAR_HEIGHT + lineCount * LINE_HEIGHT
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
}
```

**Nota (corregido durante la implementación):** la fórmula por etiqueta es aditiva (`MIN_BAR_HEIGHT + lineCount * LINE_HEIGHT`), no `Math.max(MIN_BAR_HEIGHT, lineCount * LINE_HEIGHT)` — con `Math.max` las etiquetas cortas y las largas de 3 líneas redondean ambas al mismo mínimo (320) con los datos del test de abajo, así que el test `toBeGreaterThan` nunca pasaría. La forma aditiva sí coincide con la redacción del spec ("28px por línea de texto + espacio mínimo por barra") y hace que el alto crezca de forma monótona con más líneas.

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (7 tests: los 2 originales + los 2 de `wrapLabel` + los 3 de `calculateChartHeight`).

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "feat: alto dinamico de grafica segun lineas de etiqueta"
```

---

## Task 3: Mover `wrapLabel`/`calculateChartHeight` a un módulo de utilidades, extraer `CausasBarChart` y usar tooltip con el texto completo

**Contexto añadido tras la revisión de calidad del Task 2:** `pnpm run lint` ya falla hoy con 2 errores `react-refresh/only-export-components` en `TrendChartsRow.tsx` (uno por `wrapLabel`, otro por `calculateChartHeight`) — un archivo de componente de React no puede exportar también funciones/constantes sueltas sin romper Fast Refresh. Este task, además de extraer `CausasBarChart`, mueve `wrapLabel` y `calculateChartHeight` a un módulo de utilidades nuevo (`src/utils/causasChartLabels.ts`), siguiendo el mismo patrón que ya usa el proyecto para helpers puros de gráficas (`src/utils/aiChartInsights.ts`). Así `TrendChartsRow.tsx` queda como archivo de componente puro y el lint pasa limpio.

**Files:**
- Create: `FRONTED/maternanalytics/src/utils/causasChartLabels.ts`
- Create: `FRONTED/maternanalytics/src/utils/causasChartLabels.test.ts`
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`

- [ ] **Step 1: Confirmar que los tests de renderizado pasan antes del refactor**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (7 tests, mismo resultado que al final del Task 2).

- [ ] **Step 2: Escribir el test que falla para el nuevo módulo de utilidades**

Crea `FRONTED/maternanalytics/src/utils/causasChartLabels.test.ts` con este contenido (son los mismos 5 tests de `wrapLabel`/`calculateChartHeight` que hoy viven en `TrendChartsRow.test.tsx`, movidos aquí):

```ts
import { describe, it, expect } from 'vitest'
import { wrapLabel, calculateChartHeight } from './causasChartLabels'

describe('wrapLabel', () => {
  it('devuelve el texto tal cual si es corto', () => {
    expect(wrapLabel('Eclampsia')).toBe('Eclampsia')
  })

  it('envuelve texto largo en varias líneas sin truncar ni agregar "..."', () => {
    const texto =
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre'
    const resultado = wrapLabel(texto)
    expect(Array.isArray(resultado)).toBe(true)
    const lineas = resultado as string[]
    expect(lineas.length).toBeGreaterThan(2)
    expect(lineas.some((linea) => linea.includes('...'))).toBe(false)
    expect(lineas.join(' ')).toBe(texto)
  })
})

describe('calculateChartHeight', () => {
  it('devuelve el mínimo (320) cuando no hay etiquetas', () => {
    expect(calculateChartHeight([])).toBe(320)
  })

  it('devuelve el mínimo (320) con pocas etiquetas cortas', () => {
    expect(calculateChartHeight(['Eclampsia', 'Sepsis'])).toBe(320)
  })

  it('crece cuando las etiquetas ocupan más líneas', () => {
    const etiquetasCortas = ['Eclampsia', 'Sepsis', 'Hemorragia']
    const etiquetasLargas = [
      'O14.9 Preeclampsia no especificada con complicaciones hepáticas y renales graves durante el tercer trimestre',
      'O72.1 Hemorragia postparto inmediata secundaria a atonía uterina severa con compromiso hemodinámico',
      'O99.4 Enfermedades del sistema circulatorio que complican el embarazo, el parto y el puerperio',
    ]
    expect(calculateChartHeight(etiquetasLargas)).toBeGreaterThan(calculateChartHeight(etiquetasCortas))
  })
})
```

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/utils/causasChartLabels.test.ts`
Expected: FAIL — `src/utils/causasChartLabels.ts` no existe todavía (error de módulo no encontrado).

- [ ] **Step 3: Crear el módulo de utilidades**

Crea `FRONTED/maternanalytics/src/utils/causasChartLabels.ts` con este contenido (idéntico a la lógica que hoy vive en `TrendChartsRow.tsx`, solo movida de archivo):

```ts
const LINE_HEIGHT = 28
const MIN_BAR_HEIGHT = 32
const AXIS_PADDING = 60
const MIN_CHART_HEIGHT = 320

export const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  return lines
}

export const calculateChartHeight = (labels: string[]): number => {
  if (labels.length === 0) return MIN_CHART_HEIGHT
  const totalBarsHeight = labels.reduce((sum, label) => {
    const wrapped = wrapLabel(label)
    const lineCount = Array.isArray(wrapped) ? wrapped.length : 1
    return sum + MIN_BAR_HEIGHT + lineCount * LINE_HEIGHT
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
}
```

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/utils/causasChartLabels.test.ts`
Expected: PASS (5 tests).

- [ ] **Step 4: Reescribir `TrendChartsRow.tsx` como archivo de componente puro, con `CausasBarChart` y el tooltip completo**

Reemplaza **todo el contenido** de `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx` por:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { TooltipItem } from 'chart.js'
import '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'
import { wrapLabel, calculateChartHeight } from '../../utils/causasChartLabels'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
}

interface CausasBarChartProps {
  title: string
  data: TopCausasChartData
  emptyMessage: string
  insight: string | null
}

function CausasBarChart({ title, data, emptyMessage, insight }: CausasBarChartProps) {
  const chartHeight = useMemo(() => calculateChartHeight(data.labels), [data.labels])

  return (
    <div className="chart-card-col-6">
      <h3 className="chart-card-title">{title}</h3>
      <div style={{ height: `${chartHeight}px` }}>
        {data.values.length > 0 ? (
          <Bar
            data={{
              labels: data.labels.map((l) => wrapLabel(l)),
              datasets: [
                {
                  data: data.values,
                  backgroundColor: data.colors,
                  borderColor: '#475569',
                  borderWidth: 1,
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
                      return idx !== undefined ? data.labels[idx] : ''
                    },
                  },
                },
              },
              scales: {
                x: { title: { display: true, text: 'Casos' }, ticks: { precision: 0 }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { grid: { display: false } },
              },
            }}
          />
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
            {emptyMessage}
          </div>
        )}
      </div>
      <ChartAiInsight insight={insight} />
    </div>
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="charts-grid-row">
        <CausasBarChart
          title="Top 10 Causas de Mortalidad"
          data={topCausasMortalidad}
          emptyMessage="Sin registros de causas de mortalidad"
          insight={topCausasMortalidadInsight}
        />
        <CausasBarChart
          title="Top 10 Causas de Morbilidad"
          data={topCausasMorbilidad}
          emptyMessage="Sin registros de causas de morbilidad"
          insight={topCausasMorbilidadInsight}
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Reescribir `TrendChartsRow.test.tsx` de vuelta a solo los 2 tests de renderizado**

`wrapLabel` y `calculateChartHeight` ya no viven en `TrendChartsRow.tsx`, así que sus tests (movidos al Step 2) salen de este archivo. Reemplaza **todo el contenido** de `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx` por:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow } from './TrendChartsRow'

const sampleProps = {
  topCausasMortalidad: { labels: ['Preeclampsia Severa'], values: [5], colors: ['#c0392b'] },
  topCausasMorbilidad: { labels: ['Eclampsia'], values: [3], colors: ['#2ca02c'] },
}

const emptyProps = {
  topCausasMortalidad: { labels: [], values: [], colors: [] },
  topCausasMorbilidad: { labels: [], values: [], colors: [] },
}

describe('TrendChartsRow', () => {
  it('renderiza los gráficos sin lanzar excepciones cuando hay datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(screen.getByText('Top 10 Causas de Mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Top 10 Causas de Morbilidad')).toBeInTheDocument()
  })

  it('muestra los mensajes de estado vacío cuando no hay datos', () => {
    render(<TrendChartsRow {...emptyProps} />)
    expect(screen.getByText('Sin registros de causas de mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas de morbilidad')).toBeInTheDocument()
  })
})
```

(Esto es exactamente el contenido original del archivo, antes de los Tasks 1 y 2 — vuelve a su forma original porque las funciones que probaba se mudaron de archivo.)

- [ ] **Step 6: Correr toda la suite, tipos y lint**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx src/utils/causasChartLabels.test.ts`
Expected: PASS — 2 tests en `TrendChartsRow.test.tsx` + 5 tests en `causasChartLabels.test.ts` = 7 en total (el mismo conteo que al final del Task 2, ahora repartido en dos archivos).

Run: `cd FRONTED/maternanalytics && pnpm exec tsc -b`
Expected: sin errores.

Run: `cd FRONTED/maternanalytics && pnpm run lint`
Expected: sin errores — en particular, ya NO deben aparecer los errores `react-refresh/only-export-components` que existían en `TrendChartsRow.tsx` antes de este task.

Run: `cd FRONTED/maternanalytics && pnpm run test`
Expected: PASS — toda la suite (no solo estos archivos), confirmando que el refactor no rompió otros componentes.

- [ ] **Step 7: Commit**

```bash
git add FRONTED/maternanalytics/src/utils/causasChartLabels.ts FRONTED/maternanalytics/src/utils/causasChartLabels.test.ts FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "refactor: mover wrapLabel/calculateChartHeight a utils y extraer CausasBarChart con tooltip completo"
```

---

## Task 4: Verificación visual manual

**Files:** ninguno (solo verificación, sin cambios de código).

- [ ] **Step 1: Levantar el frontend**

Run: `cd FRONTED/maternanalytics && pnpm dev`
Expected: servidor Vite arriba en `http://localhost:5173`.

- [ ] **Step 2: Abrir el dashboard con un análisis que tenga causas CIE-10 de nombre largo**

Inicia sesión, ve a la pestaña "Generalidades" del análisis (mortalidad y/o morbilidad ya cargados con datos reales, o usa uno de los Excel de prueba en `ayudas/prueba_mortalidad_550.xlsx` / `ayudas/prueba_morbilidad_549.xlsx`).

- [ ] **Step 3: Confirmar visualmente**

- En "Top 10 Causas de Mortalidad" y "Top 10 Causas de Morbilidad", cada nombre de causa se lee completo junto a su barra (sin `"..."` ni corte).
- Si una barra tiene un nombre muy largo, la gráfica se ve más alta que las demás (alto dinámico) pero sin barras amontonadas.
- Al pasar el mouse sobre una barra, el tooltip muestra el nombre completo de la causa.

- [ ] **Step 4: Detener el servidor**

Cierra el proceso de `pnpm dev` (Ctrl+C en la terminal donde corre).

No hay commit en este task — es solo verificación de que el resultado final cumple el objetivo del spec.
