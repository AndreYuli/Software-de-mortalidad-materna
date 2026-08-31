# Distribución de Edad de Riesgo en Sociodemográfico — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir los cortes de edad de riesgo obstétrico (hoy `<20/20-29/30-39/≥40`, mezclando el corte real de riesgo de 35 dentro del grupo `30-39`) agregando un nuevo agrupamiento `<19 años / 19-34 años / ≥35 años` — los cortes que pidió explícitamente Cielo en la reunión del 2026-08-24 (min. 54:51–55:52) — y mostrarlo como gráfica real en la subpestaña "Factores Sociodemográficos" de Morbilidad y Mortalidad, reemplazando parcialmente el placeholder `SociodemograficoPendiente` (que se mantiene para el resto de variables sociodemográficas aún bloqueadas por la Fase 0 del spec maestro).

**Architecture:** Nuevo método compartido en `ProcesadorBase` (backend) que no toca el agrupamiento existente usado por los cruces obstétricos (`analizar_obstetrico_por_edad`, cuyos consumidores — `ClusteringSection`, `ObstetricoEdadSection` — no deben cambiar de comportamiento). Se expone como una clave nueva en la respuesta de `/analisis/{id}/completo/`, se extrae en el frontend con un `useMemo` por evento, y se renderiza en un componente nuevo y aislado (`DistribucionEdadRiesgo`) con su propio resumen de IA, siguiendo el mismo patrón que el resto de gráficas del dashboard.

**Tech Stack:** FastAPI + pandas (backend), React 18 + TypeScript + Chart.js vía `react-chartjs-2` (frontend), pytest y Vitest.

---

## Alcance y fuera de alcance

**Dentro de este plan:**
- Nuevo agrupamiento de edad `<19 / 19-34 / ≥35` en el backend, independiente del agrupamiento existente de 4 grupos.
- Exponerlo en la respuesta de análisis completo para mortalidad y morbilidad.
- Graficarlo en la subpestaña Sociodemográfico de ambos eventos.

**Fuera de este plan:**
- No se modifica `analizar_obstetrico_por_edad` ni sus 4 grupos existentes (`ClusteringSection`, `ObstetricoEdadSection` siguen igual).
- No se resuelve el resto del bloque sociodemográfico (etnia, estrato, zona, afiliación SS, población vulnerable) — sigue bloqueado por la Fase 0 del spec maestro y sigue mostrando `SociodemograficoPendiente`.
- No se decide todavía si "Asiste a controles prenatales" se reclasifica (pendiente de confirmación con Saray/Cielo, ver `ayudas/2026-08-30-fase2-catalogo-variables.md`).

## File Structure

- Modify: `BACKEND/services/procesador_base.py` — nuevo método `analizar_distribucion_edad_riesgo`.
- Test: `BACKEND/tests/test_mortalidad_processor.py` — nuevo test.
- Test: `BACKEND/tests/test_morbilidad_processor.py` — nuevo test.
- Modify: `BACKEND/services/_analisis_calculo.py` — exponer la nueva clave en ambas ramas de `calcular_completo`.
- Modify: `FRONTED/maternanalytics/src/types.ts` — nuevo campo en `AnalisisMeta`.
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts` — extraer `edadRiesgoMortalidad` / `edadRiesgoMorbilidad`.
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.ts` — nueva función `getEdadRiesgoAiInsight`.
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts` — nuevo test.
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx`
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.test.tsx`
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx` — wire del nuevo componente.

---

### Task 1: Backend — `analizar_distribucion_edad_riesgo` en `ProcesadorBase`

**Files:**
- Modify: `BACKEND/services/procesador_base.py`
- Test: `BACKEND/tests/test_mortalidad_processor.py`
- Test: `BACKEND/tests/test_morbilidad_processor.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `BACKEND/tests/test_mortalidad_processor.py`:

```python
def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 5, 1]
    assert resultado["total"] == 6
```

Agregar al final de `BACKEND/tests/test_morbilidad_processor.py`:

```python
def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 6, 0]
    assert resultado["total"] == 6
```

(`MorbilidadProcessor` y `MortalidadProcessor` ya importan `df_morbilidad_ejemplo`/`df_mortalidad_ejemplo` en sus respectivos archivos de test — no hace falta agregar imports nuevos.)

- [ ] **Step 2: Ejecutar los tests y verificar que fallan**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest tests/test_mortalidad_processor.py tests/test_morbilidad_processor.py -q`
Expected: 2 FAILs con `AttributeError: 'MortalidadProcessor' object has no attribute 'analizar_distribucion_edad_riesgo'` (y lo mismo para `MorbilidadProcessor`), el resto de tests existentes en verde.

- [ ] **Step 3: Implementación mínima**

Agregar en `BACKEND/services/procesador_base.py`, como método nuevo de la clase `ProcesadorBase` (después de `analizar_obstetrico_por_edad`, sin modificar ese método ni su lista `grupos`):

```python
    def analizar_distribucion_edad_riesgo(self) -> dict[str, Any]:
        """Agrupa los casos por los cortes de edad de mayor riesgo obstétrico.

        Los cortes (<19, 19-34, ≥35 años) son los definidos por la experta de
        dominio para priorizar el seguimiento de los extremos de edad
        materna, y son distintos de los 4 grupos usados en
        `analizar_obstetrico_por_edad` (que sirven para cruces con otras
        variables obstétricas, no para esta distribución simple).

        Returns:
            Dict con 'labels' (nombres de los 3 grupos), 'valores' (conteo
            de casos por grupo) y 'total' (casos con edad registrada). Dict
            vacío si no hay columna 'Edad' o no hay datos válidos.
        """
        resultado: dict[str, Any] = {}
        if "Edad" not in self.df.columns:
            return resultado
        edades = pd.to_numeric(self.df["Edad"], errors="coerce").dropna()
        if edades.empty:
            return resultado

        grupos = [
            {"label": "<19 años", "min": 0, "max": 18},
            {"label": "19-34 años", "min": 19, "max": 34},
            {"label": "≥35 años", "min": 35, "max": 120},
        ]
        valores = [
            int(((edades >= g["min"]) & (edades <= g["max"])).sum()) for g in grupos
        ]
        resultado = {
            "labels": [g["label"] for g in grupos],
            "valores": valores,
            "total": int(len(edades)),
        }
        return resultado
```

- [ ] **Step 4: Ejecutar los tests y verificar que pasan**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest tests/test_mortalidad_processor.py tests/test_morbilidad_processor.py -q`
Expected: todos los tests pasan (los 2 nuevos + los existentes, sin regresiones).

- [ ] **Step 5: Commit**

```bash
git add BACKEND/services/procesador_base.py BACKEND/tests/test_mortalidad_processor.py BACKEND/tests/test_morbilidad_processor.py
git commit -m "feat: agregar distribucion de edad por cortes de riesgo obstetrico"
```

---

### Task 2: Backend — exponer la nueva clave en la respuesta de análisis completo

**Files:**
- Modify: `BACKEND/services/_analisis_calculo.py`

- [ ] **Step 1: Agregar la clave a ambas ramas de `calcular_completo`**

En `BACKEND/services/_analisis_calculo.py`, dentro de `calcular_completo`, en la rama `if analisis.tipo == "mortalidad":` agregar la clave `"distribucion_edad_riesgo"` al dict `resultado`:

Buscar:

```python
        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = {
                **meta,
                "tipo": "mortalidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "momento_muerte": p.analizar_momento_muerte(),
                "demoras": p.analizar_demoras(),
                "causas_cie10": p.analizar_causas_cie10(top_n=15),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "heatmap_demoras": p.analizar_heatmap_causa_demoras(top_n=20),
                "sankey_flujo": p.analizar_sankey_flujo(),
            }
        else:
            p = MorbilidadProcessor(df)
            resultado = {
                **meta,
                "tipo": "morbilidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "criterios_inclusion": p.analizar_criterios_inclusion(),
                "momento_ocurrencia": p.analizar_momento_ocurrencia(),
                "institucion_referencia": p.analizar_institucion_referencia(),
                "tiempo_remision": p.analizar_tiempo_remision(),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "severidad_fallas": p.analizar_severidad_fallas(),
            }
```

Reemplazar por:

```python
        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = {
                **meta,
                "tipo": "mortalidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "momento_muerte": p.analizar_momento_muerte(),
                "demoras": p.analizar_demoras(),
                "causas_cie10": p.analizar_causas_cie10(top_n=15),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "heatmap_demoras": p.analizar_heatmap_causa_demoras(top_n=20),
                "sankey_flujo": p.analizar_sankey_flujo(),
            }
        else:
            p = MorbilidadProcessor(df)
            resultado = {
                **meta,
                "tipo": "morbilidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "criterios_inclusion": p.analizar_criterios_inclusion(),
                "momento_ocurrencia": p.analizar_momento_ocurrencia(),
                "institucion_referencia": p.analizar_institucion_referencia(),
                "tiempo_remision": p.analizar_tiempo_remision(),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "severidad_fallas": p.analizar_severidad_fallas(),
            }
```

- [ ] **Step 2: Verificar que la suite completa de backend sigue pasando**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests pasan (no debería haber ningún test que dependa de las claves exactas del dict de `calcular_completo`, pero confirmar que no rompe nada).

- [ ] **Step 3: Commit**

```bash
git add BACKEND/services/_analisis_calculo.py
git commit -m "feat: exponer distribucion_edad_riesgo en el analisis completo"
```

---

### Task 3: Frontend — tipo, extracción del hook y resumen de IA

**Files:**
- Modify: `FRONTED/maternanalytics/src/types.ts`
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts`
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.ts`
- Test: `FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts`

- [ ] **Step 1: Agregar el tipo en `types.ts`**

En `FRONTED/maternanalytics/src/types.ts`, dentro de la interfaz `AnalisisMeta` (que ya tiene `causas_cie10`, `criterios_inclusion`, `demoras`), agregar:

Buscar:

```ts
export interface AnalisisMeta {
  id: number
  nombre_archivo: string
  fecha_carga: string
  limpieza_datos: Record<string, unknown>
  total_registros?: number
  anos_disponibles: number[]
  filtros_activos: { year: string | null; month: string | null }
  distribucion_mensual?: Record<string, Record<string, number>>
  causas_cie10?: { top_causas: CausaCie10[]; total_causas_unicas: number }
  criterios_inclusion?: Record<string, CriterioInclusion>
  demoras?: Record<string, DemoraDetalle>
}
```

Reemplazar por:

```ts
export interface AnalisisMeta {
  id: number
  nombre_archivo: string
  fecha_carga: string
  limpieza_datos: Record<string, unknown>
  total_registros?: number
  anos_disponibles: number[]
  filtros_activos: { year: string | null; month: string | null }
  distribucion_mensual?: Record<string, Record<string, number>>
  causas_cie10?: { top_causas: CausaCie10[]; total_causas_unicas: number }
  criterios_inclusion?: Record<string, CriterioInclusion>
  demoras?: Record<string, DemoraDetalle>
  distribucion_edad_riesgo?: { labels: string[]; valores: number[]; total: number }
}
```

- [ ] **Step 2: Escribir el test de `getEdadRiesgoAiInsight` que falla**

Agregar al `describe('aiChartInsights', ...)` de `FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts` (junto al import list, agregar `getEdadRiesgoAiInsight` a los imports desde `'./aiChartInsights'`):

```ts
  it('genera resumen de distribucion de edad de riesgo', () => {
    const data = { labels: ['<19 años', '19-34 años', '≥35 años'], valores: [1, 3, 2], total: 6 }
    const result = getEdadRiesgoAiInsight(data, 'Mortalidad')
    expect(result).toContain('mortalidad')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('retorna null para distribucion de edad de riesgo sin datos', () => {
    expect(getEdadRiesgoAiInsight(null, 'Morbilidad')).toBeNull()
  })
```

- [ ] **Step 3: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/utils/aiChartInsights.test.ts`
Expected: FAIL — `getEdadRiesgoAiInsight is not a function` o error de import.

- [ ] **Step 4: Implementación mínima — `getEdadRiesgoAiInsight`**

Agregar en `FRONTED/maternanalytics/src/utils/aiChartInsights.ts`, cerca de `getEdadAiInsight` (reutiliza el helper `pct` ya definido en el archivo):

```ts
export function getEdadRiesgoAiInsight(
  data: { labels: string[]; valores: number[]; total: number } | null,
  evento: 'Morbilidad' | 'Mortalidad',
): string | null {
  if (!data || data.total === 0) return null

  const casosRiesgo = (data.valores[0] || 0) + (data.valores[2] || 0)
  const riesgoPct = pct(casosRiesgo, data.total)

  return `El ${riesgoPct}% de los casos de ${evento.toLowerCase()} (${casosRiesgo} de ${data.total} pacientes) ocurrieron en los grupos de mayor riesgo obstétrico: menores de 19 años o de 35 años en adelante.`
}
```

- [ ] **Step 5: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/utils/aiChartInsights.test.ts`
Expected: PASS (todos los tests del archivo, incluidos los 2 nuevos).

- [ ] **Step 6: Extraer los datos por evento en `useDashboardCharts.ts`**

En `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts`, agregar (después del bloque de `edadChartData`, antes de `momentoChartData`):

```ts
  const edadRiesgoMortalidad = useMemo(() => {
    return mortalidadData?.distribucion_edad_riesgo ?? null
  }, [mortalidadData])

  const edadRiesgoMorbilidad = useMemo(() => {
    return morbilidadData?.distribucion_edad_riesgo ?? null
  }, [morbilidadData])
```

Y agregar `edadRiesgoMortalidad, edadRiesgoMorbilidad` al objeto que retorna el hook (línea final `return { lineChartData, barChartData, ... }`).

- [ ] **Step 7: Verificar tipos y tests**

Run: `cd FRONTED/maternanalytics && npx tsc --noEmit && npx vitest run`
Expected: sin errores de tipos; toda la suite existente sigue pasando más los 2 tests nuevos de `aiChartInsights.test.ts`.

- [ ] **Step 8: Commit**

```bash
git add FRONTED/maternanalytics/src/types.ts FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts FRONTED/maternanalytics/src/utils/aiChartInsights.ts FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts
git commit -m "feat: extraer distribucion de edad de riesgo y su resumen de IA"
```

---

### Task 4: Frontend — componente `DistribucionEdadRiesgo`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx`
- Test: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'

const sampleData = { labels: ['<19 años', '19-34 años', '≥35 años'], valores: [1, 3, 2], total: 6 }

describe('DistribucionEdadRiesgo', () => {
  it('renderiza el titulo con el nombre del evento cuando hay datos', () => {
    render(<DistribucionEdadRiesgo data={sampleData} evento="Mortalidad" />)
    expect(screen.getByText('Distribución por Edad y Riesgo Obstétrico (Mortalidad)')).toBeInTheDocument()
  })

  it('muestra un mensaje de datos insuficientes cuando no hay datos', () => {
    render(<DistribucionEdadRiesgo data={null} evento="Morbilidad" />)
    expect(screen.getByText('No hay datos suficientes de edad para generar esta gráfica.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/DistribucionEdadRiesgo.test.tsx`
Expected: FAIL — `Cannot find module './DistribucionEdadRiesgo'`

- [ ] **Step 3: Implementación mínima**

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getEdadRiesgoAiInsight } from '../../utils/aiChartInsights'

export interface DistribucionEdadRiesgoData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadRiesgoProps {
  data: DistribucionEdadRiesgoData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const RISK_COLORS = ['#dc2626', '#0066cc', '#dc2626']

export function DistribucionEdadRiesgo({ data, evento }: DistribucionEdadRiesgoProps) {
  const insight = useMemo(() => getEdadRiesgoAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Distribución por Edad y Riesgo Obstétrico</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes de edad para generar esta gráfica.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Distribución por Edad y Riesgo Obstétrico ({evento})</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Las mujeres menores de 19 años o de 35 años en adelante tienen mayor riesgo de morbilidad y mortalidad materna.
      </p>
      <div style={{ height: '280px' }}>
        <Bar
          data={{
            labels: data.labels,
            datasets: [
              {
                data: data.valores,
                backgroundColor: RISK_COLORS,
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
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
      <ChartAiInsight insight={insight} />
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/DistribucionEdadRiesgo.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.test.tsx
git commit -m "feat: agregar componente DistribucionEdadRiesgo"
```

---

### Task 5: Wire en `AnalysisHomeSection.tsx`

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Importar el nuevo componente**

Después de la línea `import { SociodemograficoPendiente } from './SociodemograficoPendiente'`, agregar:

```tsx
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'
```

- [ ] **Step 2: Destructurar los nuevos datos del hook**

Buscar:

```tsx
  const { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData } = useDashboardCharts({
```

Reemplazar por:

```tsx
  const { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData, edadRiesgoMortalidad, edadRiesgoMorbilidad } = useDashboardCharts({
```

- [ ] **Step 3: Renderizar la gráfica junto al placeholder en Morbilidad**

Buscar:

```tsx
              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Morbilidad" />
              )}
```

(la que está dentro de `{activeTab === 'morbilidad' && (`) y reemplazar por:

```tsx
              {activeSubTab === 'sociodemografico' && (
                <>
                  <DistribucionEdadRiesgo data={edadRiesgoMorbilidad} evento="Morbilidad" />
                  <SociodemograficoPendiente evento="Morbilidad" />
                </>
              )}
```

- [ ] **Step 4: Renderizar la gráfica junto al placeholder en Mortalidad**

Buscar:

```tsx
              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Mortalidad" />
              )}
```

(la que está dentro de `{activeTab === 'mortalidad' && (`) y reemplazar por:

```tsx
              {activeSubTab === 'sociodemografico' && (
                <>
                  <DistribucionEdadRiesgo data={edadRiesgoMortalidad} evento="Mortalidad" />
                  <SociodemograficoPendiente evento="Mortalidad" />
                </>
              )}
```

- [ ] **Step 5: Verificar tipos y tests**

Run: `cd FRONTED/maternanalytics && npx tsc --noEmit && npm test`
Expected: sin errores de tipos; toda la suite pasa (incluye los tests nuevos de Tasks 3 y 4).

- [ ] **Step 6: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat: mostrar distribucion de edad de riesgo en factores sociodemograficos"
```

---

### Task 6: Verificación completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Suite completa de backend**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests pasan, sin regresiones.

- [ ] **Step 2: Suite completa de frontend + build + lint**

Run: `cd FRONTED/maternanalytics && npm test && npm run build && npm run lint`
Expected: tests en verde, build sin errores, lint sin errores nuevos (los preexistentes en archivos no tocados por este plan no cuentan como regresión).

- [ ] **Step 3: Verificación manual en el navegador**

Con backend y frontend corriendo y datos de mortalidad/morbilidad cargados:

1. Ir a Morbilidad (Ev. 549) → Factores Sociodemográficos → debe verse la gráfica "Distribución por Edad y Riesgo Obstétrico (Morbilidad)" con 3 barras (`<19 años`, `19-34 años`, `≥35 años`), las de riesgo en rojo y la del medio en azul, seguida del placeholder de las demás variables sociodemográficas pendientes.
2. Repetir en Mortalidad (Ev. 550) → Factores Sociodemográficos.
3. Confirmar que el resumen de IA debajo de la gráfica menciona el porcentaje de casos en los grupos de riesgo.
4. Confirmar que las gráficas de "Distribución por Edad Materna" en Generalidades y "Variables Obstétricas por Edad" en Morbilidad → Clínico siguen mostrando los 4 grupos de siempre (`<20/20-29/30-39/≥40`), sin cambios — esas NO deben verse afectadas por este plan.

- [ ] **Step 4: Commit final si hubo ajustes**

Si la verificación manual no requirió cambios, no hay nada que commitear. Si se detectaron ajustes menores:

```bash
git add -A
git commit -m "fix: ajustes tras verificacion manual de distribucion de edad de riesgo"
```
