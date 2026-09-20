# Migración de dashboards Plotly → Chart.js + ECharts — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar Plotly (`plotly.js` / `react-plotly.js`) por Chart.js (`react-chartjs-2`) en los gráficos simples y Apache ECharts (`echarts-for-react` + `echarts-gl`) en los gráficos exóticos (Sankey, Heatmap, Boxplot, scatter 3D) de los 7 componentes de dashboard que hoy usan Plotly, sin cambiar la forma en que el backend expone los datos.

**Architecture:** Migración incremental componente por componente (del más simple al más riesgoso). Cada componente conserva su interfaz de props visible desde `AnalysisHomeSection.tsx` en la medida de lo posible; donde la forma de los datos es específica de Plotly (trazas), se reescribe la porción correspondiente de `useDashboardCharts.ts` para devolver una forma agnóstica de librería. Se centraliza fuente/colores/registro de Chart.js en `src/constants/chartTheme.ts`, importado por todo componente que use Chart.js o ECharts.

**Tech Stack:** React 18 + TypeScript, Vite, Vitest + Testing Library, `chart.js` + `react-chartjs-2`, `echarts` + `echarts-for-react` + `echarts-gl`. Gestor de paquetes: **pnpm** (ya usado en el proyecto — existe `pnpm-lock.yaml`).

**Spec de referencia:** `docs/historico/specs/2026-08-23-migracion-chartjs-echarts-design.md`

---

## Notas para quien ejecute este plan

- Todos los comandos de instalación/build/test usan `pnpm`, nunca `npm` ni `yarn`.
- El paquete `echarts` (el "full bundle", no `echarts/core`) incluye de fábrica todos los tipos de serie usados aquí (`bar`, `pie`, `heatmap`, `sankey`, `boxplot`, `scatter`) sin necesidad de registrar nada manualmente — a diferencia de Chart.js, que requiere registro explícito de cada elemento/escala que se use.
- jsdom no implementa `HTMLCanvasElement.getContext`. Sin un mock, cualquier render de un `<canvas>` real (Chart.js o el renderer por defecto de ECharts) lanza `Not implemented` en los tests. La Tarea 1 instala `vitest-canvas-mock` para resolver esto de forma global, una sola vez.
- **Limitación conocida:** `echarts-gl` usa WebGL para el scatter 3D. `vitest-canvas-mock` solo mockea el contexto `2d`, no `webgl`. El smoke test del modo 3D en `ClusteringSection` por lo tanto solo verifica que el componente **no lance una excepción de React** al montarse en modo 3D (ECharts/echarts-gl degradan sin crashear si no hay contexto WebGL disponible); no verifica el dibujo real del gráfico 3D. La verificación visual real de 3D se hace a mano en el navegador (ver paso de verificación manual en la Tarea 7).
- Cada tarea termina con `pnpm run build` (que ejecuta `tsc -b && vite build`) para detectar roturas de tipos entre el hook y los componentes que consumen sus datos.
- Deviaciones menores de UX aceptadas conscientemente (no requieren aprobación adicional, ya están decididas en este plan):
  - Los data-labels "siempre visibles" de `InstitucionReferenciaSection` (Chart.js) pasan a mostrarse solo en el tooltip al pasar el mouse, para no añadir la dependencia extra `chartjs-plugin-datalabels` (no estaba en el spec aprobado). ECharts sí soporta labels siempre visibles nativamente y se usa donde aplica (p. ej. `CriteriosInclusionSection`).
  - El boxplot de `TiempoRemisionSection` no dibuja la marca de "mean" (`boxmean: true` en Plotly) — ECharts boxplot no tiene un equivalente nativo directo. La mediana, Q1/Q3, min/max sí se preservan.

---

## Tarea 1: Instalar dependencias y crear el theme compartido

**Files:**
- Modify: `FRONTED/maternanalytics/package.json` (vía `pnpm add`)
- Modify: `FRONTED/maternanalytics/src/setupTests.ts`
- Create: `FRONTED/maternanalytics/src/constants/chartTheme.ts`
- Test: `FRONTED/maternanalytics/src/constants/chartTheme.test.ts`

- [ ] **Paso 1: Instalar las librerías nuevas**

```bash
cd FRONTED/maternanalytics
pnpm add chart.js react-chartjs-2 echarts echarts-for-react echarts-gl
pnpm add -D vitest-canvas-mock
```

- [ ] **Paso 2: Activar el mock de canvas globalmente para los tests**

Edita `src/setupTests.ts` para que quede así:

```ts
import '@testing-library/jest-dom/vitest'
import 'vitest-canvas-mock'
```

- [ ] **Paso 3: Escribir el test (fallará porque `chartTheme.ts` no existe)**

Crea `src/constants/chartTheme.test.ts`:

```ts
import { describe, it, expect } from 'vitest'
import { Chart as ChartJS } from 'chart.js'
import { CHART_FONT_FAMILY, CHART_COLORS, echartsBaseTextStyle } from './chartTheme'

describe('chartTheme', () => {
  it('expone la fuente y los colores base compartidos', () => {
    expect(CHART_FONT_FAMILY).toBe('Plus Jakarta Sans, sans-serif')
    expect(CHART_COLORS.mortalidad).toBe('#c0392b')
    expect(CHART_COLORS.morbilidad).toBe('#2ca02c')
  })

  it('registra los defaults globales de Chart.js al importarse', () => {
    expect(ChartJS.defaults.font.family).toBe(CHART_FONT_FAMILY)
  })

  it('arma el textStyle base para ECharts', () => {
    expect(echartsBaseTextStyle()).toEqual({
      fontFamily: CHART_FONT_FAMILY,
      color: '#1a202c',
    })
  })
})
```

- [ ] **Paso 4: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/constants/chartTheme.test.ts`
Expected: FAIL — `Failed to resolve import "./chartTheme"`

- [ ] **Paso 5: Crear `src/constants/chartTheme.ts`**

```ts
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
)

export const CHART_FONT_FAMILY = 'Plus Jakarta Sans, sans-serif'
export const CHART_TEXT_COLOR = '#1a202c'

export const CHART_COLORS = {
  mortalidad: '#c0392b',
  morbilidad: '#2ca02c',
}

ChartJS.defaults.font.family = CHART_FONT_FAMILY
ChartJS.defaults.color = CHART_TEXT_COLOR
ChartJS.defaults.plugins.legend.position = 'bottom'

export function echartsBaseTextStyle() {
  return { fontFamily: CHART_FONT_FAMILY, color: CHART_TEXT_COLOR }
}
```

- [ ] **Paso 6: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/constants/chartTheme.test.ts`
Expected: PASS (3 tests)

- [ ] **Paso 7: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 8: Commit**

```bash
git add package.json pnpm-lock.yaml src/setupTests.ts src/constants/chartTheme.ts src/constants/chartTheme.test.ts
git commit -m "feat: agregar chart.js y echarts, crear theme compartido para migración de dashboards"
```

---

## Tarea 2: Migrar `TrendChartsRow` a Chart.js (line, bar, pie)

**Files:**
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts:62-89` (forma de `lineChartData`)
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx` (reescritura completa)
- Test: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`

`barChartData`, `demorasChartData`, `edadChartData` y `momentoChartData` ya tienen una forma agnóstica de librería (`{labels, values, colors}` etc.) — no se tocan. Solo `lineChartData` está en formato de traza de Plotly y se reescribe.

- [ ] **Paso 1: Reescribir `lineChartData` en el hook**

En `src/hooks/dashboard/useDashboardCharts.ts`, reemplaza el bloque `lineChartData` (líneas 62-89) por:

```ts
  const lineChartData = useMemo(() => {
    const series: { name: string; color: string; data: number[] }[] = []

    if ((segmento === 'ambos' || segmento === 'mortalidad') && mortalidadData?.distribucion_mensual) {
      series.push({
        name: 'Mortalidad (550)',
        color: '#c0392b',
        data: getMonthly(mortalidadData.distribucion_mensual),
      })
    }

    if ((segmento === 'ambos' || segmento === 'morbilidad') && morbilidadData?.distribucion_mensual) {
      series.push({
        name: 'Morbilidad (549)',
        color: '#2ca02c',
        data: getMonthly(morbilidadData.distribucion_mensual),
      })
    }

    return { labels: MONTHS_LABEL, series }
  }, [segmento, mortalidadData, morbilidadData, getMonthly])
```

- [ ] **Paso 2: Escribir el test del componente (fallará: el componente todavía espera trazas de Plotly)**

Crea `src/components/dashboard/TrendChartsRow.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow } from './TrendChartsRow'

const sampleProps = {
  lineChartData: {
    labels: ['Ene', 'Feb', 'Mar'],
    series: [{ name: 'Mortalidad (550)', color: '#c0392b', data: [1, 2, 3] }],
  },
  barChartData: { labels: ['O26.6 - Trastornos del hígado'], values: [5], colors: ['#c0392b'] },
  demorasChartData: { labels: ['Demora 1'], values: [3] },
  edadChartData: { labels: ['20-29'], mortalidadValues: [2], morbilidadValues: [4] },
  momentoChartData: { labels: ['Parto'], mortalidadValues: [1], morbilidadValues: [2] },
}

const emptyProps = {
  lineChartData: { labels: [], series: [] },
  barChartData: { labels: [], values: [], colors: [] },
  demorasChartData: { labels: [], values: [] },
  edadChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
  momentoChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
}

describe('TrendChartsRow', () => {
  it('renderiza los 4 gráficos sin lanzar excepciones cuando hay datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(screen.getByText('Evolución Temporal de Casos')).toBeInTheDocument()
    expect(screen.getByText('Top 5 Causas / Criterios Principales')).toBeInTheDocument()
    expect(screen.getByText('Impacto: Modelo de las 4 Demoras')).toBeInTheDocument()
    expect(screen.getByText('Distribución por Edad Obstétrica')).toBeInTheDocument()
    expect(screen.getByText('Momento de Ocurrencia / Muerte')).toBeInTheDocument()
  })

  it('muestra los mensajes de estado vacío cuando no hay datos', () => {
    render(<TrendChartsRow {...emptyProps} />)
    expect(screen.getByText('Sin datos de evolución temporal')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de demoras (Aplica principalmente a Mortalidad)')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de distribución por edad')).toBeInTheDocument()
    expect(screen.getByText('Sin datos del momento del evento')).toBeInTheDocument()
  })
})
```

- [ ] **Paso 3: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: FAIL — `lineChartData.length` (o similar) no es una función válida sobre un objeto `{labels, series}`, o el título "Evolución Temporal de Casos" no se encuentra porque el componente actual espera `Record<string, unknown>[]`.

- [ ] **Paso 4: Reescribir `TrendChartsRow.tsx`**

```tsx
import { Line, Bar, Pie } from 'react-chartjs-2'
import { CHART_COLORS, CHART_FONT_FAMILY } from '../../constants/chartTheme'

export interface TrendChartsRowProps {
  lineChartData: { labels: string[]; series: { name: string; color: string; data: number[] }[] }
  barChartData: { labels: string[]; values: number[]; colors: string[] }
  demorasChartData: { labels: string[]; values: number[] }
  edadChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
  momentoChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
}

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

const legendBottom = {
  legend: { position: 'bottom' as const, labels: { font: { family: CHART_FONT_FAMILY } } },
}

export function TrendChartsRow({
  lineChartData,
  barChartData,
  demorasChartData,
  edadChartData,
  momentoChartData,
}: TrendChartsRowProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="charts-grid-row">
        <div className="chart-card-col-12">
          <h3 className="chart-card-title">Evolución Temporal de Casos</h3>
          <div style={{ height: '320px' }}>
            {lineChartData.series.length > 0 ? (
              <Line
                data={{
                  labels: lineChartData.labels,
                  datasets: lineChartData.series.map((s) => ({
                    label: s.name,
                    data: s.data,
                    borderColor: s.color,
                    backgroundColor: s.color,
                    tension: 0.4,
                    pointRadius: 4,
                  })),
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Meses' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: {
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de evolución temporal
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 5 Causas / Criterios Principales</h3>
          <div style={{ height: '320px' }}>
            {barChartData.values.length > 0 ? (
              <Bar
                data={{
                  labels: barChartData.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: barChartData.values,
                      backgroundColor: barChartData.colors,
                      borderColor: '#475569',
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  indexAxis: 'y' as const,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas
              </div>
            )}
          </div>
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Impacto: Modelo de las 4 Demoras</h3>
          <div style={{ height: '320px' }}>
            {demorasChartData.values.length > 0 ? (
              <Bar
                data={{
                  labels: demorasChartData.labels.map((l) => wrapLabel(l, 25)),
                  datasets: [
                    {
                      data: demorasChartData.values,
                      backgroundColor: ['#e74c3c', '#e67e22', '#f1c40f', '#3498db'],
                      borderColor: '#475569',
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { grid: { display: false } },
                    y: {
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de demoras (Aplica principalmente a Mortalidad)
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Distribución por Edad Obstétrica</h3>
          <div style={{ height: '320px' }}>
            {edadChartData.labels.length > 0 ? (
              <Bar
                data={{
                  labels: edadChartData.labels,
                  datasets: [
                    { label: 'Mortalidad', data: edadChartData.mortalidadValues, backgroundColor: CHART_COLORS.mortalidad },
                    { label: 'Morbilidad', data: edadChartData.morbilidadValues, backgroundColor: CHART_COLORS.morbilidad },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Rango de Edad' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de distribución por edad
              </div>
            )}
          </div>
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Momento de Ocurrencia / Muerte</h3>
          <div style={{ height: '320px' }}>
            {momentoChartData.labels.length > 0 ? (
              <Pie
                data={{
                  labels: momentoChartData.labels,
                  datasets: [
                    {
                      data: momentoChartData.labels.map(
                        (_, i) => momentoChartData.mortalidadValues[i] + momentoChartData.morbilidadValues[i],
                      ),
                      backgroundColor: ['#34495e', '#9b59b6', '#3498db', '#e74c3c', '#1abc9c'],
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  cutout: '40%',
                  plugins: legendBottom,
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos del momento del evento
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Paso 5: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (2 tests)

- [ ] **Paso 6: Build completo**

Run: `pnpm run build`
Expected: compila sin errores (confirma que `AnalysisHomeSection.tsx` sigue siendo compatible, ya que solo pasa `lineChartData` sin tocar su forma).

- [ ] **Paso 7: Commit**

```bash
git add src/hooks/dashboard/useDashboardCharts.ts src/components/dashboard/TrendChartsRow.tsx src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "feat: migrar TrendChartsRow de Plotly a Chart.js"
```

---

## Tarea 3: Migrar `AtencionOportunidad` a Chart.js (bar)

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AtencionOportunidad.tsx` (reescritura completa)
- Test: `FRONTED/maternanalytics/src/components/dashboard/AtencionOportunidad.test.tsx`

No requiere cambios en el hook: `atencionKpis`, `institucionReferenciaData` y `obstetricoEdadData` ya son objetos planos, no trazas de Plotly.

- [ ] **Paso 1: Escribir el test (fallará: el componente actual usa `react-plotly.js`, que no monta `<canvas>`)**

Crea `src/components/dashboard/AtencionOportunidad.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AtencionOportunidad } from './AtencionOportunidad'

const kpis = {
  cpnPromedio: 4.2,
  gestacionesPromedio: 2.1,
  estanciaHospitalaria: 3.5,
  estanciaUci: 1.2,
  totalMort: 10,
  totalMorb: 40,
}

const institucionReferencia = {
  instituciones: ['Hospital A', 'Hospital B'],
  conteos: [10, 6],
  con_uci: [2, 1],
  con_cirugia: [1, 0],
  totalConDato: 16,
  totalCasos: 20,
}

const obstetricoEdad = [
  {
    label: 'Gestaciones',
    mort: { nombre: '6.5 Gestaciones', valoresEje: [0, 1, 2], conteos: [1, 2, 3], porEdad: {}, promedio: 1.5, total: 6 },
    morb: null,
  },
]

describe('AtencionOportunidad', () => {
  it('renderiza KPIs, instituciones y variables obstétricas sin lanzar excepciones', () => {
    render(
      <AtencionOportunidad kpis={kpis} institucionReferencia={institucionReferencia} obstetricoEdad={obstetricoEdad} />,
    )
    expect(screen.getByText('Instituciones de Referencia (Morbilidad)')).toBeInTheDocument()
    expect(screen.getByText('Variables Obstétricas por Edad')).toBeInTheDocument()
    expect(screen.getByText('4.2', { exact: false })).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay nada', () => {
    render(<AtencionOportunidad kpis={null} institucionReferencia={null} obstetricoEdad={null} />)
    expect(screen.getByText('No hay datos suficientes para generar este análisis.')).toBeInTheDocument()
  })
})
```

- [ ] **Paso 2: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/AtencionOportunidad.test.tsx`
Expected: FAIL — jsdom lanza `Not implemented: HTMLCanvasElement.prototype.getContext` al montar `react-plotly.js`, o el `render` lanza una excepción no controlada.

- [ ] **Paso 3: Reescribir `AtencionOportunidad.tsx`**

```tsx
import React, { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import '../../constants/chartTheme'

/* ───── Types ───── */
export interface AtencionKpis {
  cpnPromedio: number | null
  gestacionesPromedio: number | null
  estanciaHospitalaria: number | null
  estanciaUci: number | null
  totalMort: number
  totalMorb: number
}

export interface InstitucionReferenciaData {
  instituciones: string[]
  conteos: number[]
  con_uci?: number[]
  con_cirugia?: number[]
  totalConDato: number
  totalCasos: number
}

export interface ObstetricoData {
  nombre: string
  valoresEje: number[]
  conteos: number[]
  porEdad: Record<string, number[]>
  promedio: number
  total: number
}

export interface AtencionOportunidadProps {
  kpis: AtencionKpis | null
  institucionReferencia: InstitucionReferenciaData | null
  obstetricoEdad: { label: string; mort: ObstetricoData | null; morb: ObstetricoData | null }[] | null
}

/* ───── Sub-components ───── */

const AtencionKpiRow: React.FC<{ kpis: AtencionKpis }> = ({ kpis }) => {
  const cards = [
    { title: 'Controles Prenatales Prom.', value: kpis.cpnPromedio, suffix: '', icon: '🩺', accent: '#0284c7' },
    { title: 'Gestaciones Promedio', value: kpis.gestacionesPromedio, suffix: '', icon: '🤰', accent: '#c026d3' },
    { title: 'Estancia Hospitalaria (Morbilidad)', value: kpis.estanciaHospitalaria, suffix: ' días', icon: '🛏️', accent: '#059669' },
    { title: 'Estancia UCI (Morbilidad)', value: kpis.estanciaUci, suffix: ' días', icon: '🏥', accent: '#dc2626' },
  ]

  return (
    <div className="atencion-kpi-row">
      {cards.map((c, i) => (
        <div className="atencion-kpi-card" key={i} style={{ '--accent': c.accent } as React.CSSProperties}>
          <div className="atencion-kpi-header">
            <span className="atencion-kpi-title">{c.title}</span>
            <span className="atencion-kpi-icon">{c.icon}</span>
          </div>
          <div className="atencion-kpi-value">
            {c.value != null ? `${c.value}${c.suffix}` : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

const InstitucionReferenciaSection: React.FC<{ data: InstitucionReferenciaData }> = ({ data }) => {
  const yLabels = useMemo(
    () => data.instituciones.map((inst) => (inst.length > 30 ? inst.substring(0, 27) + '...' : inst)),
    [data.instituciones],
  )

  const datasets = useMemo(() => {
    if (data.con_uci && data.con_cirugia) {
      return [
        { label: 'Total', data: data.conteos, backgroundColor: '#0ea5e9' },
        { label: 'UCI', data: data.con_uci, backgroundColor: '#dc2626' },
        { label: 'Cirugía', data: data.con_cirugia, backgroundColor: '#ea580c' },
      ]
    }
    return [{ label: 'Total Casos', data: data.conteos, backgroundColor: '#0ea5e9' }]
  }, [data])

  return (
    <div className="atencion-instituciones-section">
      <h3 className="chart-card-title">
        <span>Instituciones de Referencia (Morbilidad)</span>
        <span className="atencion-badge-inst">Top 15</span>
      </h3>
      <div style={{ height: `${Math.max(300, data.instituciones.length * 40)}px` }}>
        <Bar
          data={{ labels: yLabels, datasets }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y' as const,
            plugins: { legend: { position: 'bottom' as const } },
            scales: {
              x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
              y: { grid: { display: false } },
            },
          }}
        />
      </div>
      <div className="atencion-instituciones-stats">
        <span className="text-sm text-slate-500">Datos disponibles en {data.totalConDato} de {data.totalCasos} casos de morbilidad.</span>
      </div>
    </div>
  )
}

const ObstetricoEdadSection: React.FC<{ variables: NonNullable<AtencionOportunidadProps['obstetricoEdad']> }> = ({ variables }) => {
  return (
    <div className="atencion-obstetrico-section">
      <h3 className="chart-card-title">
        <span>Variables Obstétricas por Edad</span>
        <span className="atencion-badge-obs">Comparativa</span>
      </h3>

      <div className="atencion-obstetrico-grid">
        {variables.map((v, i) => {
          const labels = (v.mort?.valoresEje ?? v.morb?.valoresEje ?? []).map(String)
          const datasets = []

          if (v.mort) {
            datasets.push({
              label: `Mortalidad (${v.mort.promedio.toFixed(1)} prom)`,
              data: v.mort.conteos,
              backgroundColor: '#ef4444',
            })
          }
          if (v.morb) {
            datasets.push({
              label: `Morbilidad (${v.morb.promedio.toFixed(1)} prom)`,
              data: v.morb.conteos,
              backgroundColor: '#3b82f6',
            })
          }

          return (
            <div key={i} className="atencion-obs-chart-container" style={{ height: '250px' }}>
              <Bar
                data={{ labels, datasets }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    title: { display: true, text: v.label, font: { size: 14 } },
                    legend: { position: 'bottom' as const },
                  },
                  scales: {
                    x: { ticks: { autoSkip: false } },
                  },
                }}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ───── Main Component ───── */

export const AtencionOportunidad: React.FC<AtencionOportunidadProps> = ({
  kpis,
  institucionReferencia,
  obstetricoEdad,
}) => {
  const hasAnyData = kpis || institucionReferencia || obstetricoEdad

  if (!hasAnyData) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '60px 40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>🚑</div>
        <h3 className="chart-card-title" style={{ justifyContent: 'center' }}>Atención y Oportunidad</h3>
        <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
          No hay datos suficientes para generar este análisis.
        </p>
      </div>
    )
  }

  return (
    <div className="atencion-tab-container">
      {kpis && <AtencionKpiRow kpis={kpis} />}

      <div className="atencion-main-row">
        {institucionReferencia && institucionReferencia.instituciones.length > 0 && (
          <div className="atencion-left-col">
            <InstitucionReferenciaSection data={institucionReferencia} />
          </div>
        )}

        {obstetricoEdad && obstetricoEdad.length > 0 && (
          <div className="atencion-right-col">
            <ObstetricoEdadSection variables={obstetricoEdad} />
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Paso 4: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/AtencionOportunidad.test.tsx`
Expected: PASS (2 tests)

- [ ] **Paso 5: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 6: Commit**

```bash
git add src/components/dashboard/AtencionOportunidad.tsx src/components/dashboard/AtencionOportunidad.test.tsx
git commit -m "feat: migrar AtencionOportunidad de Plotly a Chart.js"
```

---

## Tarea 4: Migrar `HeatmapDemoras` a ECharts

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/HeatmapDemoras.tsx` (reescritura completa)
- Test: `FRONTED/maternanalytics/src/components/dashboard/HeatmapDemoras.test.tsx`

- [ ] **Paso 1: Escribir el test (fallará: el componente actual usa `react-plotly.js`)**

Crea `src/components/dashboard/HeatmapDemoras.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HeatmapDemoras } from './HeatmapDemoras'

const data = {
  causas: ['O26.6', 'O99.3'],
  demoras: ['Demora 1', 'Demora 2'],
  valores: [
    [3, 1],
    [0, 2],
  ],
}

describe('HeatmapDemoras', () => {
  it('renderiza el mapa de calor sin lanzar excepciones cuando hay datos', () => {
    render(<HeatmapDemoras data={data} />)
    expect(screen.getByText('Causas CIE-10 Asociadas a Demoras Obstétricas')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay datos', () => {
    render(<HeatmapDemoras data={undefined} />)
    expect(screen.getByText('No hay datos suficientes para generar el mapa de calor.')).toBeInTheDocument()
  })
})
```

- [ ] **Paso 2: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/HeatmapDemoras.test.tsx`
Expected: FAIL — error de `HTMLCanvasElement.prototype.getContext` no implementado por `react-plotly.js`, o excepción al montar.

- [ ] **Paso 3: Reescribir `HeatmapDemoras.tsx`**

```tsx
import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

export interface HeatmapDemorasProps {
  data: {
    causas: string[]
    demoras: string[]
    valores: number[][]
  } | undefined
}

export const HeatmapDemoras: React.FC<HeatmapDemorasProps> = ({ data }) => {
  const option = useMemo(() => {
    if (!data || !data.causas || data.causas.length === 0) return null

    const cells: [number, number, number][] = []
    let maxValue = 0
    data.demoras.forEach((_, yIdx) => {
      data.valores[yIdx].forEach((value, xIdx) => {
        cells.push([xIdx, yIdx, value])
        if (value > maxValue) maxValue = value
      })
    })

    return {
      textStyle: echartsBaseTextStyle(),
      grid: { top: 20, left: 200, right: 20, bottom: 150 },
      xAxis: {
        type: 'category' as const,
        data: data.causas,
        axisLabel: { rotate: 45, fontSize: 10 },
        splitArea: { show: true },
      },
      yAxis: {
        type: 'category' as const,
        data: data.demoras,
        axisLabel: { fontSize: 12, fontWeight: 600 },
        splitArea: { show: true },
      },
      visualMap: {
        min: 0,
        max: maxValue || 1,
        calculable: true,
        orient: 'horizontal' as const,
        left: 'center' as const,
        bottom: 0,
        inRange: { color: ['#fff5f0', '#fcbba1', '#fb6a4a', '#cb181d', '#67000d'] },
      },
      series: [
        {
          type: 'heatmap' as const,
          data: cells,
          tooltip: {
            formatter: (params: { data: [number, number, number] }) =>
              `Causa: ${data.causas[params.data[0]]}<br/>Demora: ${data.demoras[params.data[1]]}<br/>Casos: ${params.data[2]}`,
          },
        },
      ],
    }
  }, [data])

  if (!option) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Mapa de Calor: Causas vs Demoras</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes para generar el mapa de calor.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Causas CIE-10 Asociadas a Demoras Obstétricas</h3>
      <ReactECharts option={option} style={{ height: '550px', width: '100%' }} notMerge={true} />
    </div>
  )
}
```

- [ ] **Paso 4: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/HeatmapDemoras.test.tsx`
Expected: PASS (2 tests)

- [ ] **Paso 5: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 6: Commit**

```bash
git add src/components/dashboard/HeatmapDemoras.tsx src/components/dashboard/HeatmapDemoras.test.tsx
git commit -m "feat: migrar HeatmapDemoras de Plotly a ECharts"
```

---

## Tarea 5: Migrar `SankeyMortalidad` a ECharts

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/SankeyMortalidad.tsx` (reescritura completa)
- Test: `FRONTED/maternanalytics/src/components/dashboard/SankeyMortalidad.test.tsx`

Precondición asumida (ya cierta hoy, porque el color de cada nodo en Plotly se deriva del prefijo del nombre): los nombres en `data.nodos` son únicos — necesario porque el Sankey de ECharts referencia nodos por nombre en `links.source`/`links.target`.

- [ ] **Paso 1: Escribir el test (fallará: el componente actual usa `react-plotly.js`)**

Crea `src/components/dashboard/SankeyMortalidad.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SankeyMortalidad } from './SankeyMortalidad'

const data = {
  nodos: ['[Parto] Vaginal', '[Parto] Cesárea', '[Nivel] Nivel 1', '[Muerte] Intraparto'],
  links: {
    source: [0, 1],
    target: [2, 2],
    value: [5, 3],
  },
}

describe('SankeyMortalidad', () => {
  it('renderiza el diagrama Sankey sin lanzar excepciones cuando hay datos', () => {
    render(<SankeyMortalidad data={data} />)
    expect(screen.getByText('Flujo de Atención: Tipo de Parto → Nivel de Atención → Momento de Muerte')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay datos', () => {
    render(<SankeyMortalidad data={undefined} />)
    expect(screen.getByText('No hay datos suficientes para generar el diagrama Sankey.')).toBeInTheDocument()
  })
})
```

- [ ] **Paso 2: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/SankeyMortalidad.test.tsx`
Expected: FAIL — excepción al montar `react-plotly.js` sobre canvas no implementado.

- [ ] **Paso 3: Reescribir `SankeyMortalidad.tsx`**

```tsx
import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

export interface SankeyMortalidadProps {
  data: {
    nodos: string[]
    links: {
      source: number[]
      target: number[]
      value: number[]
    }
  } | undefined
}

function nodeColor(name: string): string {
  if (name.startsWith('[Parto]')) return '#3498db'
  if (name.startsWith('[Nivel]')) return '#f1c40f'
  if (name.startsWith('[Muerte]')) return '#e74c3c'
  return '#3498db'
}

export const SankeyMortalidad: React.FC<SankeyMortalidadProps> = ({ data }) => {
  const option = useMemo(() => {
    if (!data || !data.nodos || data.nodos.length === 0) return null

    const nodes = data.nodos.map((name) => ({ name, itemStyle: { color: nodeColor(name) } }))
    const links = data.links.source.map((sourceIdx, i) => ({
      source: data.nodos[sourceIdx],
      target: data.nodos[data.links.target[i]],
      value: data.links.value[i],
    }))

    return {
      textStyle: echartsBaseTextStyle(),
      series: [
        {
          type: 'sankey' as const,
          orient: 'horizontal' as const,
          nodeGap: 15,
          nodeWidth: 20,
          data: nodes,
          links,
          lineStyle: { color: 'gradient' as const, opacity: 0.4 },
          label: { fontSize: 12 },
        },
      ],
    }
  }, [data])

  if (!option) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Flujo de Atención Clínica</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes para generar el diagrama Sankey.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Flujo de Atención: Tipo de Parto → Nivel de Atención → Momento de Muerte</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Este diagrama muestra cómo se distribuyeron las gestantes desde el tipo de parto, pasando por el nivel de atención donde fueron atendidas, hasta el momento en que ocurrió la muerte.
      </p>
      <ReactECharts option={option} style={{ height: '450px', width: '100%' }} notMerge={true} />
    </div>
  )
}
```

- [ ] **Paso 4: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/SankeyMortalidad.test.tsx`
Expected: PASS (2 tests)

- [ ] **Paso 5: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 6: Commit**

```bash
git add src/components/dashboard/SankeyMortalidad.tsx src/components/dashboard/SankeyMortalidad.test.tsx
git commit -m "feat: migrar SankeyMortalidad de Plotly a ECharts"
```

---

## Tarea 6: Migrar `SeveridadFallasMorbilidad` a ECharts (bar, pie, boxplot)

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/SeveridadFallasMorbilidad.tsx` (reescritura de `CriteriosInclusionSection`, `MomentoOcurrenciaSection`, `TiempoRemisionSection`; se elimina el código muerto `radarData`/`radarLayout` de `FallasOrganicasSection`, que hoy se calcula pero nunca se renderiza)
- Test: `FRONTED/maternanalytics/src/components/dashboard/SeveridadFallasMorbilidad.test.tsx`

`FallasOrganicasSection` (ranking con barras CSS) y `SeveridadIndicatorsSection` (tarjetas CSS) no usan Plotly — no se tocan más allá de quitar las dos variables muertas.

- [ ] **Paso 1: Escribir el test (fallará: el componente actual usa `react-plotly.js`)**

Crea `src/components/dashboard/SeveridadFallasMorbilidad.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SeveridadFallasMorbilidad } from './SeveridadFallasMorbilidad'

const data = {
  fallas: [{ nombre: 'Falla Cardiaca', casos: 4 }, { nombre: 'Falla Renal', casos: 2 }, { nombre: 'Falla Hepática', casos: 1 }],
  severidad: [{ nombre: 'Ingreso UCI', casos: 5 }],
  total_casos: 10,
}

const morbKpis = { totalCasos: 10, edadPromedio: 28.5, estanciaHospitalaria: 4.2, estanciaUci: 1.1, criteriosPromedio: 2.3 }
const criteriosInclusion = [{ nombre: 'Hemorragia', casos: 6, porcentaje: 60 }]
const momentoOcurrencia = [{ label: 'Parto', count: 5 }, { label: 'Puerperio', count: 5 }]
const tiempoRemision = { valores: [1, 2, 3, 4, 5], min: 1, q1: 2, median: 3, mean: 3, q3: 4, max: 5, total: 5 }

describe('SeveridadFallasMorbilidad', () => {
  it('renderiza las secciones con gráficos sin lanzar excepciones cuando hay datos', () => {
    render(
      <SeveridadFallasMorbilidad
        data={data}
        morbKpis={morbKpis}
        criteriosInclusion={criteriosInclusion}
        momentoOcurrencia={momentoOcurrencia}
        tiempoRemision={tiempoRemision}
      />,
    )
    expect(screen.getByText('Criterios de Inclusión MME')).toBeInTheDocument()
    expect(screen.getByText('Momento de Ocurrencia')).toBeInTheDocument()
    expect(screen.getByText('Tiempo de Remisión')).toBeInTheDocument()
  })

  it('muestra el mensaje de datos insuficientes cuando no hay nada', () => {
    render(
      <SeveridadFallasMorbilidad
        data={undefined}
        morbKpis={null}
        criteriosInclusion={null}
        momentoOcurrencia={null}
        tiempoRemision={null}
      />,
    )
    expect(screen.getByText(/No hay datos suficientes de morbilidad/)).toBeInTheDocument()
  })
})
```

- [ ] **Paso 2: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/SeveridadFallasMorbilidad.test.tsx`
Expected: FAIL — excepción al montar `react-plotly.js` sobre canvas no implementado.

- [ ] **Paso 3: Reescribir `SeveridadFallasMorbilidad.tsx`**

```tsx
import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'

/* ───── Types ───── */
export interface SeveridadFallasData {
  fallas: { nombre: string; casos: number }[]
  severidad: { nombre: string; casos: number }[]
  total_casos: number
}

export interface MorbKpis {
  totalCasos: number
  edadPromedio: number | null
  estanciaHospitalaria: number | null
  estanciaUci: number | null
  criteriosPromedio: number | null
}

export interface CriterioItem {
  nombre: string
  casos: number
  porcentaje: number
}

export interface MomentoItem {
  label: string
  count: number
}

export interface TiempoRemision {
  valores: number[]
  min: number
  q1: number
  median: number
  mean: number
  q3: number
  max: number
  total: number
}

export interface SeveridadFallasMorbilidadProps {
  data: SeveridadFallasData | undefined
  morbKpis: MorbKpis | null
  criteriosInclusion: CriterioItem[] | null
  momentoOcurrencia: MomentoItem[] | null
  tiempoRemision: TiempoRemision | null
}

/* ───── Helpers ───── */
const FALLA_ICONS: Record<string, string> = {
  cardiaca: '❤️', cardíaca: '❤️',
  vascular: '🩸', renal: '🫘',
  hepática: '🟤', hepatica: '🟤',
  metabólica: '⚗️', metabolica: '⚗️',
  cerebral: '🧠', respiratoria: '🫁',
  coagulación: '🩹', coagulacion: '🩹',
}

const SEVERITY_ICONS: Record<string, { icon: string; gradient: string }> = {
  'Ingreso UCI': { icon: '🏥', gradient: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)' },
  'Cirugía Adicional': { icon: '🔪', gradient: 'linear-gradient(135deg, #ea580c 0%, #9a3412 100%)' },
  'Transfusión': { icon: '💉', gradient: 'linear-gradient(135deg, #d97706 0%, #92400e 100%)' },
}

const MOMENTO_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe']

const CRITERIO_COLORS: Record<string, string> = {
  'Hemorragia': '#dc2626',
  'Eclampsia': '#ea580c',
  'Preeclampsia severa': '#d97706',
  'Sepsis': '#059669',
  'Ruptura uterina': '#7c3aed',
}

function getFallaIcon(nombre: string): string {
  const lower = nombre.toLowerCase()
  for (const [key, icon] of Object.entries(FALLA_ICONS)) {
    if (lower.includes(key)) return icon
  }
  return '⚠️'
}

/* ───── Sub-components ───── */

const MorbKpiRow: React.FC<{ kpis: MorbKpis }> = ({ kpis }) => {
  const cards = [
    { title: 'Total Casos MME', value: kpis.totalCasos, suffix: '', icon: '🏥', accent: '#0066cc' },
    { title: 'Edad Promedio', value: kpis.edadPromedio, suffix: ' años', icon: '👩', accent: '#7c3aed' },
    { title: 'Estancia Hospitalaria', value: kpis.estanciaHospitalaria, suffix: ' días', icon: '🛏️', accent: '#059669' },
    { title: 'Estancia UCI', value: kpis.estanciaUci, suffix: ' días', icon: '💊', accent: '#dc2626' },
  ]

  return (
    <div className="morb-kpi-row">
      {cards.map((c, i) => (
        <div className="morb-kpi-card" key={i} style={{ '--accent': c.accent } as React.CSSProperties}>
          <div className="morb-kpi-header">
            <span className="morb-kpi-title">{c.title}</span>
            <span className="morb-kpi-icon">{c.icon}</span>
          </div>
          <div className="morb-kpi-value">
            {c.value != null ? `${c.value}${c.suffix}` : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}

const FallasOrganicasSection: React.FC<{ fallas: SeveridadFallasData['fallas']; totalCasos: number }> = ({ fallas, totalCasos }) => {
  const sorted = useMemo(() => [...fallas].sort((a, b) => b.casos - a.casos), [fallas])
  const maxCasos = sorted.length > 0 ? sorted[0].casos : 1

  return (
    <div className="morb-fallas-section">
      <div className="morb-fallas-ranking">
        <h3 className="chart-card-title">
          <span>Ranking de Fallas</span>
          <span className="morb-badge-count">{sorted.length} tipos</span>
        </h3>
        <div className="morb-fallas-list">
          {sorted.map((f, i) => {
            const pct = totalCasos > 0 ? ((f.casos / totalCasos) * 100).toFixed(1) : '0'
            const barWidth = maxCasos > 0 ? (f.casos / maxCasos) * 100 : 0
            return (
              <div className="morb-falla-item" key={i} style={{ animationDelay: `${i * 80}ms` }}>
                <div className="morb-falla-info">
                  <span className="morb-falla-rank">#{i + 1}</span>
                  <span className="morb-falla-icon">{getFallaIcon(f.nombre)}</span>
                  <span className="morb-falla-name">{f.nombre.replace(/^Falla\s*/i, '')}</span>
                </div>
                <div className="morb-falla-bar-container">
                  <div
                    className="morb-falla-bar"
                    style={{ width: `${barWidth}%`, animationDelay: `${i * 80 + 200}ms` }}
                  />
                </div>
                <div className="morb-falla-stats">
                  <span className="morb-falla-count">{f.casos}</span>
                  <span className="morb-falla-pct">{pct}%</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

const SeveridadIndicatorsSection: React.FC<{ severidad: SeveridadFallasData['severidad']; totalCasos: number }> = ({ severidad, totalCasos }) => {
  return (
    <div className="morb-severity-cards">
      <h3 className="chart-card-title">
        <span>Indicadores de Severidad</span>
        <span className="morb-badge-severity">Intervenciones</span>
      </h3>
      <div className="morb-severity-grid">
        {severidad.map((s, i) => {
          const meta = SEVERITY_ICONS[s.nombre] || { icon: '⚕️', gradient: 'linear-gradient(135deg, #475569, #1e293b)' }
          const pct = totalCasos > 0 ? ((s.casos / totalCasos) * 100) : 0
          return (
            <div className="morb-severity-card" key={i} style={{ animationDelay: `${i * 120}ms` }}>
              <div className="morb-severity-icon-circle" style={{ background: meta.gradient }}>
                <span>{meta.icon}</span>
              </div>
              <div className="morb-severity-info">
                <span className="morb-severity-name">{s.nombre}</span>
                <div className="morb-severity-progress-track">
                  <div
                    className="morb-severity-progress-fill"
                    style={{
                      width: `${Math.min(pct, 100)}%`,
                      background: meta.gradient,
                      animationDelay: `${i * 120 + 300}ms`,
                    }}
                  />
                </div>
                <div className="morb-severity-numbers">
                  <span className="morb-severity-count">{s.casos} casos</span>
                  <span className="morb-severity-pct">{pct.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const CriteriosInclusionSection: React.FC<{ criterios: CriterioItem[] }> = ({ criterios }) => {
  const option = useMemo(() => {
    const maxCasos = criterios.length > 0 ? Math.max(...criterios.map((c) => c.casos)) : 1
    return {
      textStyle: echartsBaseTextStyle(),
      grid: { top: 10, left: 140, right: 90, bottom: 20, containLabel: true },
      xAxis: { type: 'value' as const, max: maxCasos * 1.3, splitLine: { lineStyle: { color: '#f1f5f9' } } },
      yAxis: {
        type: 'category' as const,
        data: criterios.map((c) => c.nombre),
        axisLabel: { fontSize: 12, fontWeight: 600 },
      },
      series: [
        {
          type: 'bar' as const,
          data: criterios.map((c) => ({ value: c.casos, itemStyle: { color: CRITERIO_COLORS[c.nombre] || '#6366f1' } })),
          barCategoryGap: '35%',
          label: {
            show: true,
            position: 'right' as const,
            fontSize: 11,
            fontWeight: 700,
            color: '#334155',
            formatter: (params: { dataIndex: number }) => {
              const c = criterios[params.dataIndex]
              return `${c.casos} (${c.porcentaje.toFixed(1)}%)`
            },
          },
        },
      ],
    }
  }, [criterios])

  return (
    <div className="morb-criterios-section">
      <h3 className="chart-card-title">
        <span>Criterios de Inclusión MME</span>
        <span className="morb-badge-criterios">Diagnósticos</span>
      </h3>
      <ReactECharts option={option} style={{ height: '260px', width: '100%' }} notMerge={true} />
    </div>
  )
}

const MomentoOcurrenciaSection: React.FC<{ data: MomentoItem[] }> = ({ data }) => {
  const total = data.reduce((sum, d) => sum + d.count, 0)

  const option = useMemo(
    () => ({
      textStyle: echartsBaseTextStyle(),
      color: MOMENTO_COLORS.slice(0, data.length),
      tooltip: { trigger: 'item' as const, formatter: '{b}<br/>{c} casos ({d}%)' },
      legend: { bottom: 0, textStyle: { fontSize: 10, color: '#475569' } },
      graphic: [
        {
          type: 'text' as const,
          left: 'center' as const,
          top: 'center' as const,
          style: { text: `${total}\ncasos`, textAlign: 'center' as const, fontSize: 22, fontWeight: 700, fill: '#0f172a' },
        },
      ],
      series: [
        {
          type: 'pie' as const,
          radius: ['55%', '80%'],
          center: ['50%', '45%'],
          data: data.map((d) => ({ name: d.label, value: d.count })),
          label: { show: true, position: 'inside' as const, formatter: '{d}%', fontSize: 12, fontWeight: 700, color: '#fff' },
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
        },
      ],
    }),
    [data, total],
  )

  return (
    <div className="morb-momento-section">
      <h3 className="chart-card-title">
        <span>Momento de Ocurrencia</span>
        <span className="morb-badge-momento">Clínico</span>
      </h3>
      <ReactECharts option={option} style={{ height: '280px', width: '100%' }} notMerge={true} />
    </div>
  )
}

const TiempoRemisionSection: React.FC<{ data: TiempoRemision }> = ({ data }) => {
  const option = useMemo(
    () => ({
      textStyle: echartsBaseTextStyle(),
      grid: { top: 20, left: 60, right: 20, bottom: 30 },
      xAxis: { type: 'category' as const, data: ['Tiempo (h)'] },
      yAxis: {
        type: 'value' as const,
        name: 'Horas',
        nameTextStyle: { fontSize: 11, color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
      },
      series: [
        {
          type: 'boxplot' as const,
          data: [[data.min, data.q1, data.median, data.q3, data.max]],
          itemStyle: { color: 'rgba(99, 102, 241, 0.15)', borderColor: '#4f46e5' },
        },
      ],
    }),
    [data],
  )

  return (
    <div className="morb-remision-section">
      <h3 className="chart-card-title">
        <span>Tiempo de Remisión</span>
        <span className="morb-badge-remision">Horas</span>
      </h3>
      <ReactECharts option={option} style={{ height: '220px', width: '100%' }} notMerge={true} />
      <div className="morb-remision-stats">
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Mediana</span>
          <span className="morb-remision-stat-value">{data.median.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Promedio</span>
          <span className="morb-remision-stat-value">{data.mean.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">Q1–Q3</span>
          <span className="morb-remision-stat-value">{data.q1.toFixed(1)}–{data.q3.toFixed(1)}h</span>
        </div>
        <div className="morb-remision-stat">
          <span className="morb-remision-stat-label">n</span>
          <span className="morb-remision-stat-value">{data.total}</span>
        </div>
      </div>
    </div>
  )
}

/* ───── Main Component ───── */

export const SeveridadFallasMorbilidad: React.FC<SeveridadFallasMorbilidadProps> = ({
  data,
  morbKpis,
  criteriosInclusion,
  momentoOcurrencia,
  tiempoRemision,
}) => {
  const hasAnyData = (data && (data.fallas.length > 0 || data.severidad.length > 0)) ||
    morbKpis || criteriosInclusion || momentoOcurrencia || tiempoRemision

  if (!hasAnyData) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '60px 40px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>🏥</div>
        <h3 className="chart-card-title" style={{ justifyContent: 'center' }}>Análisis de Morbilidad Materna Extrema</h3>
        <p style={{ color: '#64748b', fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
          No hay datos suficientes de morbilidad para generar este análisis. Cargue un archivo de evento 549.
        </p>
      </div>
    )
  }

  return (
    <div className="morb-tab-container">
      {morbKpis && <MorbKpiRow kpis={morbKpis} />}

      {data && data.fallas.length > 0 && (
        <FallasOrganicasSection fallas={data.fallas} totalCasos={data.total_casos} />
      )}

      <div className="morb-severity-criterios-row">
        {data && data.severidad.length > 0 && (
          <SeveridadIndicatorsSection severidad={data.severidad} totalCasos={data.total_casos} />
        )}
        {criteriosInclusion && criteriosInclusion.length > 0 && (
          <CriteriosInclusionSection criterios={criteriosInclusion} />
        )}
      </div>

      <div className="morb-momento-remision-row">
        {momentoOcurrencia && momentoOcurrencia.length > 0 && (
          <MomentoOcurrenciaSection data={momentoOcurrencia} />
        )}
        {tiempoRemision && (
          <TiempoRemisionSection data={tiempoRemision} />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Paso 4: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/SeveridadFallasMorbilidad.test.tsx`
Expected: PASS (2 tests)

- [ ] **Paso 5: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 6: Commit**

```bash
git add src/components/dashboard/SeveridadFallasMorbilidad.tsx src/components/dashboard/SeveridadFallasMorbilidad.test.tsx
git commit -m "feat: migrar SeveridadFallasMorbilidad de Plotly a ECharts y eliminar radar chart muerto"
```

---

## Tarea 7: Migrar `ClusteringSection` a ECharts + echarts-gl (scatter 2D/3D)

**Files:**
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts` (reemplaza `clusteringTrace` por `clusteringChartData`, exporta el tipo `ClusteringChartData`)
- Modify: `FRONTED/maternanalytics/src/components/dashboard/ClusteringSection.tsx` (reescritura completa)
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx` (actualizar el nombre de la prop que recibe `ClusteringSection`)
- Test: `FRONTED/maternanalytics/src/components/dashboard/ClusteringSection.test.tsx`

- [ ] **Paso 1: Reescribir `clusteringTrace` → `clusteringChartData` en el hook**

En `src/hooks/dashboard/useDashboardCharts.ts`:

1. Agrega el tipo exportado, cerca del resto de tipos importados (después de los `import`):

```ts
export type ClusteringPoint2D = { x: number; y: number; color: string; label: string }
export type ClusteringPoint3D = { x: number; y: number; z: number; color: string; label: string }
export type ClusteringChartData =
  | { dim: '2d'; points: ClusteringPoint2D[] }
  | { dim: '3d'; points: ClusteringPoint3D[] }
```

2. Reemplaza el bloque `clusteringTrace` (busca `const clusteringTrace = useMemo`) por:

```ts
  const clusteringChartData = useMemo((): ClusteringChartData | null => {
    if (!activeClusterData) return null

    if (pcaDim === '3d' && activeClusterData.pca_3d) {
      const { x, y, z } = activeClusterData.pca_3d
      return {
        dim: '3d',
        points: x.map((xi, i) => ({
          x: xi,
          y: y[i],
          z: z[i],
          color: clusterMarkerColors[i] ?? '#95a5a6',
          label: `Caso ${i + 1} · Cluster ${activeClusterData.clusters![i]}`,
        })),
      }
    }

    if (activeClusterData.pca_2d) {
      const { x, y } = activeClusterData.pca_2d
      return {
        dim: '2d',
        points: x.map((xi, i) => ({
          x: xi,
          y: y[i],
          color: clusterMarkerColors[i] ?? '#95a5a6',
          label: `Caso ${i + 1} · Cluster ${activeClusterData.clusters![i]}`,
        })),
      }
    }

    return null
  }, [activeClusterData, pcaDim, clusterMarkerColors])
```

3. En el `return` final del hook, reemplaza `clusteringTrace` por `clusteringChartData`:

```ts
  return { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData }
```

- [ ] **Paso 2: Actualizar la prop en `AnalysisHomeSection.tsx`**

Cambia:

```ts
  const { lineChartData, barChartData, activeClusterData, clusteringTrace, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData } = useDashboardCharts({
```

por:

```ts
  const { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData } = useDashboardCharts({
```

Y en el JSX de `<ClusteringSection ...>`, cambia:

```tsx
            clusteringTrace={clusteringTrace}
```

por:

```tsx
            clusteringChartData={clusteringChartData}
```

- [ ] **Paso 3: Escribir el test (fallará: el componente actual espera `clusteringTrace`, no `clusteringChartData`, y usa `react-plotly.js`)**

Crea `src/components/dashboard/ClusteringSection.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ClusteringSection } from './ClusteringSection'
import type { ClusteringChartData } from '../../hooks/dashboard/useDashboardCharts'

const chartData2d: ClusteringChartData = {
  dim: '2d',
  points: [
    { x: 1, y: 2, color: '#0066cc', label: 'Caso 1 · Cluster 0' },
    { x: -1, y: 0.5, color: '#c0392b', label: 'Caso 2 · Cluster 1' },
  ],
}

const chartData3d: ClusteringChartData = {
  dim: '3d',
  points: [{ x: 1, y: 2, z: 0.5, color: '#0066cc', label: 'Caso 1 · Cluster 0' }],
}

const baseProps = {
  segmento: 'mortalidad' as const,
  clusteringSegment: 'mortalidad' as const,
  onClusteringSegmentChange: () => {},
  onPcaDimChange: () => {},
  activeClusterData: { clusters: [0, 1], pca_2d: { x: [1, -1], y: [2, 0.5] } },
  latestMortalidad: { id: 1 },
  latestMorbilidad: null,
  filterYear: '',
  filterMonth: '',
}

describe('ClusteringSection', () => {
  it('renderiza el scatter 2D sin lanzar excepciones cuando hay datos', () => {
    render(<ClusteringSection {...baseProps} pcaDim="2d" clusteringChartData={chartData2d} />)
    expect(screen.getByText('Modelos de Clustering (PCA)')).toBeInTheDocument()
  })

  it('renderiza el scatter 3D sin lanzar excepciones cuando hay datos', () => {
    render(<ClusteringSection {...baseProps} pcaDim="3d" clusteringChartData={chartData3d} />)
    expect(screen.getByText('Modelos de Clustering (PCA)')).toBeInTheDocument()
  })

  it('muestra el mensaje de modelo no disponible cuando no hay datos', () => {
    render(<ClusteringSection {...baseProps} activeClusterData={null} pcaDim="2d" clusteringChartData={null} />)
    expect(screen.getByText(/Modelo de clustering no disponible/)).toBeInTheDocument()
  })
})
```

- [ ] **Paso 4: Ejecutar el test y confirmar que falla**

Run: `pnpm exec vitest run src/components/dashboard/ClusteringSection.test.tsx`
Expected: FAIL — error de tipos (`clusteringTrace` no reconoce la prop `clusteringChartData`) o excepción de `react-plotly.js` en jsdom.

- [ ] **Paso 5: Reescribir `ClusteringSection.tsx`**

```tsx
import 'echarts-gl'
import ReactECharts from 'echarts-for-react'
import { echartsBaseTextStyle } from '../../constants/chartTheme'
import NarrativaIA from '../NarrativaIA'
import type { ClusteringResult } from '../../hooks/dashboard/useAnalysisHomeData'
import type { ClusteringChartData } from '../../hooks/dashboard/useDashboardCharts'
import type { Segmento } from '../../hooks/dashboard/useDashboardMetrics'

export interface ClusteringSectionProps {
  segmento: Segmento
  clusteringSegment: 'mortalidad' | 'morbilidad'
  onClusteringSegmentChange: (segment: 'mortalidad' | 'morbilidad') => void
  pcaDim: '2d' | '3d'
  onPcaDimChange: (dim: '2d' | '3d') => void
  activeClusterData: ClusteringResult | null | undefined
  clusteringChartData: ClusteringChartData | null
  latestMortalidad: { id: number } | null
  latestMorbilidad: { id: number } | null
  filterYear: string
  filterMonth: string
}

function build2DOption(data: Extract<ClusteringChartData, { dim: '2d' }>) {
  return {
    textStyle: echartsBaseTextStyle(),
    tooltip: { formatter: (params: { data: { name: string } }) => params.data.name },
    grid: { top: 20, left: 50, right: 20, bottom: 40 },
    xAxis: { type: 'value' as const, name: 'Componente 1', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } } },
    yAxis: { type: 'value' as const, name: 'Componente 2', splitLine: { lineStyle: { color: 'rgba(0,0,0,0.05)' } } },
    series: [
      {
        type: 'scatter' as const,
        symbolSize: 12,
        data: data.points.map((p) => ({
          value: [p.x, p.y],
          name: p.label,
          itemStyle: { color: p.color, borderColor: '#fff', borderWidth: 1 },
        })),
      },
    ],
  }
}

function build3DOption(data: Extract<ClusteringChartData, { dim: '3d' }>) {
  return {
    textStyle: echartsBaseTextStyle(),
    tooltip: {},
    grid3D: { boxWidth: 100, boxHeight: 100, boxDepth: 100 },
    xAxis3D: { type: 'value' as const, name: 'PC1' },
    yAxis3D: { type: 'value' as const, name: 'PC2' },
    zAxis3D: { type: 'value' as const, name: 'PC3' },
    series: [
      {
        type: 'scatter3D' as const,
        symbolSize: 8,
        data: data.points.map((p) => ({
          value: [p.x, p.y, p.z],
          name: p.label,
          itemStyle: { color: p.color },
        })),
      },
    ],
  }
}

export function ClusteringSection({
  segmento,
  clusteringSegment,
  onClusteringSegmentChange,
  pcaDim,
  onPcaDimChange,
  activeClusterData,
  clusteringChartData,
  latestMortalidad,
  latestMorbilidad,
  filterYear,
  filterMonth,
}: ClusteringSectionProps) {
  const filtros = { year: filterYear || undefined, month: filterMonth || undefined }

  return (
    <div className="advanced-grid-row">
      <div className="clustering-card-span-8">
        <div className="chart-card-title">
          <span>Modelos de Clustering (PCA)</span>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {segmento === 'ambos' && (
              <div className="mini-cluster-toggles">
                <button
                  className={`btn-mini-toggle ${clusteringSegment === 'mortalidad' ? 'active' : ''}`}
                  onClick={() => onClusteringSegmentChange('mortalidad')}
                  disabled={!latestMortalidad}
                >
                  Mortalidad
                </button>
                <button
                  className={`btn-mini-toggle ${clusteringSegment === 'morbilidad' ? 'active' : ''}`}
                  onClick={() => onClusteringSegmentChange('morbilidad')}
                  disabled={!latestMorbilidad}
                >
                  Morbilidad
                </button>
              </div>
            )}
            <div className="mini-cluster-toggles">
              <button className={`btn-mini-toggle ${pcaDim === '2d' ? 'active' : ''}`} onClick={() => onPcaDimChange('2d')}>
                2D
              </button>
              <button className={`btn-mini-toggle ${pcaDim === '3d' ? 'active' : ''}`} onClick={() => onPcaDimChange('3d')}>
                3D
              </button>
            </div>
          </div>
        </div>

        <div style={{ height: '340px' }}>
          {activeClusterData && clusteringChartData ? (
            <ReactECharts
              option={clusteringChartData.dim === '3d' ? build3DOption(clusteringChartData) : build2DOption(clusteringChartData)}
              style={{ height: '100%', width: '100%' }}
              notMerge={true}
            />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888', textAlign: 'center', padding: '0 20px' }}>
              Modelo de clustering no disponible.<br/>Se requiere mayor cantidad y variabilidad de datos numéricos.
            </div>
          )}
        </div>
      </div>

      <div className="ai-insight-card-span-4">
        {segmento === 'ambos' ? (
          <>
            {latestMortalidad && (
              <NarrativaIA
                analisisId={latestMortalidad.id}
                tipo="resumen_ejecutivo"
                titulo="Resumen de Hallazgos — Mortalidad"
                filtros={filtros}
              />
            )}
            {latestMorbilidad && (
              <NarrativaIA
                analisisId={latestMorbilidad.id}
                tipo="resumen_ejecutivo"
                titulo="Resumen de Hallazgos — Morbilidad"
                filtros={filtros}
              />
            )}
          </>
        ) : (
          <NarrativaIA
            analisisId={segmento === 'mortalidad' ? latestMortalidad!.id : latestMorbilidad!.id}
            tipo="resumen_ejecutivo"
            titulo="Resumen de Hallazgos"
            filtros={filtros}
          />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Paso 6: Ejecutar el test y confirmar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/ClusteringSection.test.tsx`
Expected: PASS (3 tests) — el caso 3D pasa porque el componente no lanza excepción al montarse, no porque se verifique el dibujo WebGL (ver limitación en la sección "Notas" al inicio del plan).

- [ ] **Paso 7: Build completo**

Run: `pnpm run build`
Expected: compila sin errores.

- [ ] **Paso 8: Verificación manual en navegador (obligatoria para el 3D)**

```bash
pnpm run dev
```

Abre el dashboard, entra a un análisis con clustering disponible, y alterna el toggle 2D/3D en "Modelos de Clustering (PCA)". Confirma visualmente que:
- El scatter 2D muestra los puntos coloreados por cluster.
- El scatter 3D rota con el mouse y muestra los puntos coloreados por cluster (esto es lo que el smoke test automatizado NO puede verificar por la limitación de WebGL en jsdom).

- [ ] **Paso 9: Commit**

```bash
git add src/hooks/dashboard/useDashboardCharts.ts src/components/dashboard/AnalysisHomeSection.tsx src/components/dashboard/ClusteringSection.tsx src/components/dashboard/ClusteringSection.test.tsx
git commit -m "feat: migrar ClusteringSection de Plotly a ECharts + echarts-gl (scatter 2D/3D)"
```

---

## Tarea 8: Limpieza final — remover Plotly

**Files:**
- Modify: `FRONTED/maternanalytics/package.json` (vía `pnpm remove`)
- Delete: `FRONTED/maternanalytics/src/react-plotly.js.d.ts`

- [ ] **Paso 1: Confirmar que no queda ninguna referencia a Plotly**

Run: `grep -ril "plotly" FRONTED/maternanalytics/src`
Expected: sin resultados (ningún archivo).

Si aparece algún resultado, detente y revisa esa referencia antes de continuar — no se debe desinstalar el paquete mientras algún archivo lo siga importando.

- [ ] **Paso 2: Eliminar el archivo de tipos ambientales de Plotly**

```bash
cd FRONTED/maternanalytics
rm src/react-plotly.js.d.ts
```

- [ ] **Paso 3: Desinstalar los paquetes de Plotly**

```bash
pnpm remove plotly.js react-plotly.js
```

- [ ] **Paso 4: Ejecutar toda la suite de tests**

Run: `pnpm test`
Expected: PASS — todos los tests (incluyendo `App.test.tsx` y los 7 nuevos smoke tests de esta migración).

- [ ] **Paso 5: Build completo**

Run: `pnpm run build`
Expected: compila sin errores y sin referencias colgantes a `plotly.js`/`react-plotly.js`.

- [ ] **Paso 6: Commit**

Importante: el árbol de trabajo tiene otros cambios sin relación en `BACKEND/` que no son parte de esta migración. No uses `git add -A`; agrega solo los archivos que tocó esta tarea:

```bash
git add FRONTED/maternanalytics/package.json FRONTED/maternanalytics/pnpm-lock.yaml
git status --short FRONTED/maternanalytics/src/react-plotly.js.d.ts
git commit -m "chore: eliminar plotly.js y react-plotly.js tras completar la migración a Chart.js/ECharts"
```

(El `git status --short` sobre `react-plotly.js.d.ts` debe mostrar `D` — confirma que el borrado del Paso 2 ya quedó registrado; si `git rm` no se usó explícitamente, agrégalo con `git add FRONTED/maternanalytics/src/react-plotly.js.d.ts` antes del commit.)

---

## Verificación final (todas las tareas completas)

- [ ] `pnpm test` — pasa toda la suite.
- [ ] `pnpm run build` — compila sin errores.
- [ ] `pnpm run dev` y recorrer manualmente las 5 pestañas del dashboard (Panorama General, Morbilidad, Mortalidad, Análisis de Demoras, Atención y Oportunidad) verificando que cada gráfico se ve y responde a hover/tooltip como antes.
- [ ] `grep -ril "plotly" FRONTED/maternanalytics/src` no devuelve resultados.
- [ ] `grep -ril "plotly" FRONTED/maternanalytics/package.json` no devuelve resultados.
