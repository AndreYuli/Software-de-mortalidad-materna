# Corrección de nombres en gráficas "Top Causas" — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el nombre completo de cada causa CIE-10 sea siempre legible junto a su barra en "Top 10 Causas de Mortalidad" y "Top 10 Causas de Morbilidad", sin recortes ni `"..."`, tanto en el eje como en el tooltip.

**Architecture:** Todo el cambio vive en un solo archivo, `TrendChartsRow.tsx`. Se quita el límite de 2 líneas de `wrapLabel`, se agrega una función pura `calculateChartHeight` que calcula el alto del contenedor según cuántas líneas ocupan las etiquetas, y se extrae un subcomponente `CausasBarChart` que unifica la config de Chart.js (antes duplicada dos veces) agregando un callback de tooltip que siempre muestra el texto original completo.

**Tech Stack:** React + TypeScript, Chart.js v4 vía `react-chartjs-2`, Vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-09-14-nombres-graficas-top-causas-design.md`

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
    return sum + Math.max(MIN_BAR_HEIGHT, lineCount * LINE_HEIGHT)
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
}
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (7 tests: los 2 originales + los 2 de `wrapLabel` + los 3 de `calculateChartHeight`).

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "feat: alto dinamico de grafica segun lineas de etiqueta"
```

---

## Task 3: Extraer `CausasBarChart` y usar tooltip con el texto completo

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`

Este task no agrega tests nuevos: reutiliza los 2 tests de renderizado que ya existen (`TrendChartsRow` con datos / estado vacío) como red de seguridad del refactor — deben seguir pasando exactamente igual después del cambio.

- [ ] **Step 1: Confirmar que los tests de renderizado pasan antes del refactor**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (7 tests, mismo resultado que al final del Task 2).

- [ ] **Step 2: Reescribir `TrendChartsRow.tsx` completo con el subcomponente `CausasBarChart`**

Reemplaza **todo el contenido** de `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx` por:

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import type { TooltipItem } from 'chart.js'
import '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getTopCausasAiInsight } from '../../utils/aiChartInsights'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
}

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
    return sum + Math.max(MIN_BAR_HEIGHT, lineCount * LINE_HEIGHT)
  }, 0)
  return Math.max(MIN_CHART_HEIGHT, AXIS_PADDING + totalBarsHeight)
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

- [ ] **Step 3: Correr los tests y verificar que todo sigue en verde**

Run: `cd FRONTED/maternanalytics && pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (los mismos 7 tests que al final del Task 2 — el refactor no cambió comportamiento observable).

- [ ] **Step 4: Verificar tipos, lint y la suite completa de tests**

Run: `cd FRONTED/maternanalytics && pnpm exec tsc -b`
Expected: sin errores.

Run: `cd FRONTED/maternanalytics && pnpm run lint`
Expected: sin errores.

Run: `cd FRONTED/maternanalytics && pnpm run test`
Expected: PASS — toda la suite (no solo `TrendChartsRow.test.tsx`), confirmando que el refactor no rompió otros componentes que puedan importar algo de este archivo.

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx
git commit -m "refactor: extraer CausasBarChart y mostrar nombre completo en el tooltip"
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
