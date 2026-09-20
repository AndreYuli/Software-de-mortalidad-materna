# Reestructuración de Navegación del Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestructurar la navegación de `AnalysisHomeSection` de las 5 pestañas actuales (Panorama, Morbilidad, Mortalidad, Demoras, Atención) a 3 pestañas principales (Generalidades, Morbilidad, Mortalidad), donde Morbilidad y Mortalidad tienen cada una 2 subpestañas (Factores Sociodemográficos, Factores Clínicos), según lo acordado en la reunión del 2026-08-24 (Fase 1 de `ayudas/2026-08-30-plataforma-vidamaterna-requisitos-design.md`).

**Architecture:** Se extrae el estado de navegación de dos niveles a un hook nuevo (`useDashboardTabs`) probado de forma aislada, se crea un componente `SubTabs` reutilizable para el segundo nivel y un componente `SociodemograficoPendiente` como placeholder mientras la Fase 0 (captura de variables sociodemográficas) no esté lista. Las gráficas ya existentes (`SeveridadFallasMorbilidad`, `AtencionOportunidad`, `SankeyMortalidad`, `HeatmapDemoras`, `TrendChartsRow`, `ClusteringSection`) no cambian de implementación — solo se reubican bajo la nueva estructura de pestañas en `AnalysisHomeSection.tsx`.

**Tech Stack:** React 18 + TypeScript, Vitest + React Testing Library, CSS plano (`StrategicDashboard.css`).

---

## Alcance y fuera de alcance

**Dentro de esta fase:**
- Nuevo modelo de navegación de 2 niveles (pestaña principal + subpestaña).
- Reubicación de las gráficas existentes bajo la nueva estructura, sin tocar su lógica interna.
- Placeholder para "Factores Sociodemográficos" (aún sin datos — depende de la Fase 0 del spec).

**Fuera de esta fase** (quedan para fases posteriores del spec):
- Cualquier variable o gráfica sociodemográfica real (Fase 0 y Fase 3 del spec).
- Fix de la fórmula de tasa de letalidad (Fase 4).
- Filtro por semana (Fase 5).

## File Structure

- Create: `FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.ts` — estado de la pestaña principal y la subpestaña activa.
- Create: `FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.test.ts`
- Create: `FRONTED/maternanalytics/src/components/dashboard/SubTabs.tsx` — botones de segundo nivel (Sociodemográfico/Clínico).
- Create: `FRONTED/maternanalytics/src/components/dashboard/SubTabs.test.tsx`
- Create: `FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.tsx` — placeholder de la subpestaña sociodemográfica.
- Create: `FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.test.tsx`
- Modify: `FRONTED/maternanalytics/src/components/dashboard/StrategicDashboard.css` — estilos de `.dashboard-subtabs` / `.subtab-button`.
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx` — nuevo modelo de pestañas y reubicación de contenido.

---

### Task 1: Hook `useDashboardTabs`

**Files:**
- Create: `FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.ts`
- Test: `FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.test.ts`

- [ ] **Step 1: Escribir el test que falla**

```ts
import { describe, it, expect } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { useDashboardTabs } from './useDashboardTabs'

describe('useDashboardTabs', () => {
  it('inicia en la pestaña generalidades y en la subpestaña clínica', () => {
    const { result } = renderHook(() => useDashboardTabs())
    expect(result.current.activeTab).toBe('generalidades')
    expect(result.current.activeSubTab).toBe('clinico')
  })

  it('cambia de pestaña principal con setActiveTab', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveTab('morbilidad'))
    expect(result.current.activeTab).toBe('morbilidad')
  })

  it('permite cambiar de subpestaña con setActiveSubTab', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveSubTab('sociodemografico'))
    expect(result.current.activeSubTab).toBe('sociodemografico')
  })

  it('reinicia la subpestaña a clínico al cambiar de pestaña principal', () => {
    const { result } = renderHook(() => useDashboardTabs())
    act(() => result.current.setActiveSubTab('sociodemografico'))
    expect(result.current.activeSubTab).toBe('sociodemografico')

    act(() => result.current.setActiveTab('mortalidad'))
    expect(result.current.activeSubTab).toBe('clinico')
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/hooks/navigation/useDashboardTabs.test.ts`
Expected: FAIL — `Cannot find module './useDashboardTabs'`

- [ ] **Step 3: Implementación mínima**

```ts
import { useCallback, useState } from 'react'

export type MainTab = 'generalidades' | 'morbilidad' | 'mortalidad'
export type SubTab = 'sociodemografico' | 'clinico'

export function useDashboardTabs(initialTab: MainTab = 'generalidades') {
  const [activeTab, setActiveTabState] = useState<MainTab>(initialTab)
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('clinico')

  const setActiveTab = useCallback((tab: MainTab) => {
    setActiveTabState(tab)
    setActiveSubTab('clinico')
  }, [])

  return { activeTab, setActiveTab, activeSubTab, setActiveSubTab }
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/hooks/navigation/useDashboardTabs.test.ts`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.ts FRONTED/maternanalytics/src/hooks/navigation/useDashboardTabs.test.ts
git commit -m "feat: agregar hook useDashboardTabs para navegacion de dos niveles"
```

---

### Task 2: Componente `SubTabs`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/dashboard/SubTabs.tsx`
- Test: `FRONTED/maternanalytics/src/components/dashboard/SubTabs.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SubTabs } from './SubTabs'

describe('SubTabs', () => {
  it('renderiza los botones de Factores Sociodemográficos y Factores Clínicos', () => {
    render(<SubTabs active="clinico" onChange={() => {}} />)
    expect(screen.getByText('Factores Sociodemográficos')).toBeInTheDocument()
    expect(screen.getByText('Factores Clínicos')).toBeInTheDocument()
  })

  it('marca como activo el botón correspondiente a `active`', () => {
    render(<SubTabs active="sociodemografico" onChange={() => {}} />)
    expect(screen.getByText('Factores Sociodemográficos')).toHaveClass('active')
    expect(screen.getByText('Factores Clínicos')).not.toHaveClass('active')
  })

  it('llama a onChange con la clave de la subpestaña al hacer click', () => {
    const onChange = vi.fn()
    render(<SubTabs active="clinico" onChange={onChange} />)
    fireEvent.click(screen.getByText('Factores Sociodemográficos'))
    expect(onChange).toHaveBeenCalledWith('sociodemografico')
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/SubTabs.test.tsx`
Expected: FAIL — `Cannot find module './SubTabs'`

- [ ] **Step 3: Implementación mínima**

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
    <div className="dashboard-subtabs">
      {SUBTAB_ORDER.map((key) => (
        <button
          key={key}
          type="button"
          className={`subtab-button ${active === key ? 'active' : ''}`}
          onClick={() => onChange(key)}
        >
          {SUBTAB_LABELS[key]}
        </button>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/SubTabs.test.tsx`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/SubTabs.tsx FRONTED/maternanalytics/src/components/dashboard/SubTabs.test.tsx
git commit -m "feat: agregar componente SubTabs para el segundo nivel de navegacion"
```

---

### Task 3: Componente `SociodemograficoPendiente`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.tsx`
- Test: `FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SociodemograficoPendiente } from './SociodemograficoPendiente'

describe('SociodemograficoPendiente', () => {
  it('muestra el nombre del evento en el título', () => {
    render(<SociodemograficoPendiente evento="Morbilidad" />)
    expect(screen.getByText('Factores Sociodemográficos de Morbilidad')).toBeInTheDocument()
  })

  it('explica por qué la sección está pendiente', () => {
    render(<SociodemograficoPendiente evento="Mortalidad" />)
    expect(screen.getByText(/zona, etnia, estrato/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/SociodemograficoPendiente.test.tsx`
Expected: FAIL — `Cannot find module './SociodemograficoPendiente'`

- [ ] **Step 3: Implementación mínima**

```tsx
export interface SociodemograficoPendienteProps {
  evento: 'Morbilidad' | 'Mortalidad'
}

export function SociodemograficoPendiente({ evento }: SociodemograficoPendienteProps) {
  return (
    <div className="tab-placeholder">
      <h3>Factores Sociodemográficos de {evento}</h3>
      <p>
        Esta sección está en construcción: las variables de zona, etnia, estrato
        socioeconómico, afiliación al sistema de salud y población vulnerable aún
        no están disponibles en los datos cargados.
      </p>
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/SociodemograficoPendiente.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.tsx FRONTED/maternanalytics/src/components/dashboard/SociodemograficoPendiente.test.tsx
git commit -m "feat: agregar placeholder SociodemograficoPendiente"
```

---

### Task 4: Estilos de las subpestañas

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/StrategicDashboard.css:124-129`

- [ ] **Step 1: Insertar los estilos nuevos**

Insertar el siguiente bloque inmediatamente después de `.tab-button.active { ... }` (línea 128) y antes de `.tab-placeholder` (línea 130):

```css
.dashboard-subtabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.subtab-button {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.subtab-button:hover {
  background: #f1f5f9;
}

.subtab-button.active {
  background: #eff6ff;
  border-color: #0066cc;
  color: #0066cc;
}
```

- [ ] **Step 2: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/StrategicDashboard.css
git commit -m "style: agregar estilos de subpestanas dashboard-subtabs"
```

---

### Task 5: Rewire `AnalysisHomeSection.tsx`

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Agregar los imports nuevos**

En `AnalysisHomeSection.tsx`, después de la línea `import { ExportReportModal } from './ExportReportModal'` (línea 17), agregar:

```tsx
import { useDashboardTabs } from '../../hooks/navigation/useDashboardTabs'
import { SubTabs } from './SubTabs'
import { SociodemograficoPendiente } from './SociodemograficoPendiente'
```

- [ ] **Step 2: Reemplazar el estado de `activeTab`**

Buscar (línea 53-54):

```tsx
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'panorama' | 'morbilidad' | 'mortalidad' | 'demoras' | 'atencion'>('panorama')
```

Reemplazar por:

```tsx
  const [isExportModalOpen, setIsExportModalOpen] = useState(false)
  const { activeTab, setActiveTab, activeSubTab, setActiveSubTab } = useDashboardTabs()
```

- [ ] **Step 3: Reemplazar los botones de pestaña principal**

Buscar el bloque `<div className="dashboard-tabs">...</div>` (líneas 149-180, con los 5 botones: Panorama General, Morbilidad, Mortalidad, Análisis de Demoras, Atención y Oportunidad). Reemplazarlo por:

```tsx
            <div className="dashboard-tabs">
              <button
                className={`tab-button ${activeTab === 'generalidades' ? 'active' : ''}`}
                onClick={() => setActiveTab('generalidades')}
              >
                Generalidades
              </button>
              <button
                className={`tab-button ${activeTab === 'morbilidad' ? 'active' : ''}`}
                onClick={() => setActiveTab('morbilidad')}
              >
                Morbilidad (Ev. 549)
              </button>
              <button
                className={`tab-button ${activeTab === 'mortalidad' ? 'active' : ''}`}
                onClick={() => setActiveTab('mortalidad')}
              >
                Mortalidad (Ev. 550)
              </button>
            </div>
```

- [ ] **Step 4: Reemplazar el contenido condicional de las pestañas**

Buscar el bloque que empieza en `{activeTab === 'panorama' && (` y termina después de `{activeTab === 'atencion' && ( ... )}` (líneas 194-249). Reemplazarlo por:

```tsx
          {activeTab === 'generalidades' && (
            <>
              <TrendChartsRow
                lineChartData={lineChartData}
                barChartData={barChartData}
                demorasChartData={demorasChartData}
                edadChartData={edadChartData}
                momentoChartData={momentoChartData}
                segmento={segmento}
              />

              <ClusteringSection
                segmento={segmento}
                clusteringSegment={clusteringSegment}
                onClusteringSegmentChange={setClusteringSegment}
                pcaDim={pcaDim}
                onPcaDimChange={setPcaDim}
                activeClusterData={activeClusterData}
                clusteringChartData={clusteringChartData}
                latestMortalidad={latestMortalidad}
                latestMorbilidad={latestMorbilidad}
                filterYear={filterYear}
                filterMonth={filterMonth}
              />
            </>
          )}

          {activeTab === 'morbilidad' && (
            <>
              <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Morbilidad" />
              )}

              {activeSubTab === 'clinico' && (
                <>
                  <SeveridadFallasMorbilidad
                    data={severidadFallasData}
                    morbKpis={morbKpis}
                    criteriosInclusion={criteriosInclusionData}
                    momentoOcurrencia={momentoOcurrenciaData}
                    tiempoRemision={tiempoRemisionData}
                  />
                  <AtencionOportunidad
                    kpis={atencionKpis}
                    institucionReferencia={institucionReferenciaData}
                    obstetricoEdad={obstetricoEdadData}
                  />
                </>
              )}
            </>
          )}

          {activeTab === 'mortalidad' && (
            <>
              <SubTabs active={activeSubTab} onChange={setActiveSubTab} />

              {activeSubTab === 'sociodemografico' && (
                <SociodemograficoPendiente evento="Mortalidad" />
              )}

              {activeSubTab === 'clinico' && (
                <>
                  <div className="charts-grid-row">
                    <SankeyMortalidad data={sankeyFlujoData} />
                  </div>
                  <div className="charts-grid-row">
                    <HeatmapDemoras data={heatmapDemorasData} />
                  </div>
                </>
              )}
            </>
          )}
```

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat: reestructurar navegacion del dashboard a 3 pestanas con subpestanas"
```

---

### Task 6: Verificación completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Ejecutar toda la suite de tests**

Run: `cd FRONTED/maternanalytics && npm test`
Expected: todos los tests pasan, incluyendo los ya existentes de `AtencionOportunidad.test.tsx`, `HeatmapDemoras.test.tsx`, `SeveridadFallasMorbilidad.test.tsx`, `SankeyMortalidad.test.tsx` (si existe), `ClusteringSection.test.tsx` y `TrendChartsRow.test.tsx` — estos no deberían romperse porque su implementación interna no cambió, solo dónde se montan dentro de `AnalysisHomeSection`.

- [ ] **Step 2: Verificar tipos y build**

Run: `cd FRONTED/maternanalytics && npm run build`
Expected: compila sin errores de TypeScript (confirma que `activeTab`/`activeSubTab` se usan con los tipos correctos en todo `AnalysisHomeSection.tsx`).

- [ ] **Step 3: Lint**

Run: `cd FRONTED/maternanalytics && npm run lint`
Expected: sin errores nuevos.

- [ ] **Step 4: Verificación manual en el navegador**

Run: `cd FRONTED/maternanalytics && npm run dev`

Con el backend (`BACKEND`) y el servicio de IA corriendo y al menos un archivo de mortalidad y uno de morbilidad ya cargados (o cargarlos desde la UI):

1. Entrar a "Dashboard Analítico" y confirmar que la pestaña activa por defecto es **Generalidades**, mostrando `TrendChartsRow` y `ClusteringSection` igual que antes.
2. Click en **Morbilidad (Ev. 549)** → debe verse la barra de subpestañas con "Factores Sociodemográficos" y "Factores Clínicos", con "Factores Clínicos" activo por defecto mostrando `SeveridadFallasMorbilidad` y `AtencionOportunidad`.
3. Click en "Factores Sociodemográficos" dentro de Morbilidad → debe verse el placeholder "Factores Sociodemográficos de Morbilidad".
4. Click en **Mortalidad (Ev. 550)** → confirmar que la subpestaña vuelve a "Factores Clínicos" por defecto (no queda en "Sociodemográficos" del tab anterior) y muestra `SankeyMortalidad` y `HeatmapDemoras`.
5. Click en "Factores Sociodemográficos" dentro de Mortalidad → debe verse el placeholder "Factores Sociodemográficos de Mortalidad".
6. Confirmar que no hay errores en la consola del navegador durante la navegación.

- [ ] **Step 5: Commit final si hubo ajustes**

Si la verificación manual no requirió cambios, no hay nada que commitear en este paso. Si se detectaron ajustes menores (por ejemplo de estilos), aplicarlos y:

```bash
git add -A
git commit -m "fix: ajustes tras verificacion manual de la reestructuracion de navegacion"
```

---

## Notas para fases posteriores

- Cuando la Fase 0 del spec (captura de variables sociodemográficas) esté lista, `SociodemograficoPendiente` se reemplaza por las gráficas reales dentro de las mismas ramas `activeSubTab === 'sociodemografico'` — no requiere tocar el modelo de navegación de este plan.
- `ClusteringSection` se deja en "Generalidades" porque el spec no le asigna una subpestaña específica; si en la Fase 3 se decide moverlo a "Factores Clínicos" de mortalidad/morbilidad, es un cambio de una línea en `AnalysisHomeSection.tsx`.
