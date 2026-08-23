# Migración de dashboards de Plotly a Chart.js + Apache ECharts

**Fecha:** 2026-08-23
**Estado:** Aprobado, pendiente de plan de implementación

## Contexto

El dashboard de MaternAnalytics (`FRONTED/maternanalytics`) renderiza todas sus gráficas con `plotly.js` / `react-plotly.js`. El bundle de Plotly es pesado y su renderizado (SVG) no está optimizado para volúmenes de datos ni para rendimiento en general. El objetivo de esta migración es mejorar el rendimiento real del dashboard moviendo el renderizado a librerías basadas en Canvas.

Motivación confirmada con el usuario: **rendimiento real** (no solo modernización preventiva).

## Alcance actual (Plotly)

7 archivos usan Plotly hoy:

- `src/components/dashboard/TrendChartsRow.tsx` — line, bar (x4), pie
- `src/components/dashboard/AtencionOportunidad.tsx` — bar (agrupado/apilado)
- `src/components/dashboard/HeatmapDemoras.tsx` — heatmap
- `src/components/dashboard/SankeyMortalidad.tsx` — sankey
- `src/components/dashboard/SeveridadFallasMorbilidad.tsx` — scatterpolar (radar), bar, pie, box
- `src/components/dashboard/ClusteringSection.tsx` — scatter 2D / scatter3d (toggle 2D/3D de PCA)
- `src/hooks/dashboard/useDashboardCharts.ts` — arma las trazas que consumen los componentes anteriores
- `src/react-plotly.js.d.ts` — tipos ambientales para react-plotly.js

## Decisión: reparto de librerías

Chart.js no soporta nativamente Sankey, Heatmap, Boxplot ni scatter 3D. Por eso se usa un enfoque mixto en vez de una sola librería para todo:

| Componente | Gráficos actuales (Plotly) | Librería destino |
|---|---|---|
| `TrendChartsRow.tsx` | line, bar (x4), pie | **Chart.js** (`react-chartjs-2`) |
| `AtencionOportunidad.tsx` | bar (agrupado/apilado) | **Chart.js** |
| `HeatmapDemoras.tsx` | heatmap | **ECharts** (`echarts-for-react`) |
| `SankeyMortalidad.tsx` | sankey | **ECharts** |
| `SeveridadFallasMorbilidad.tsx` | scatterpolar (radar), bar, pie, box | **ECharts** (los 4 tipos en un solo motor, evita mezclar dos librerías en un mismo archivo) |
| `ClusteringSection.tsx` | scatter 2D / scatter3d | **ECharts** + `echarts-gl` (solo para el 3D) |

**Clustering 3D:** se decidió mantener el toggle 2D/3D existente agregando `echarts-gl` (paquete adicional, WebGL, el más pesado de los tres extras) en vez de eliminar la vista 3D, para preservar paridad de funcionalidad con lo que existe hoy.

### Dependencias

Agregar: `chart.js`, `react-chartjs-2`, `echarts`, `echarts-for-react`, `echarts-gl`.

Quitar (al finalizar todos los componentes): `plotly.js`, `react-plotly.js`, `src/react-plotly.js.d.ts`.

## Theming compartido

Hoy cada componente repite inline valores como `font: 'Plus Jakarta Sans, sans-serif'`, `paper_bgcolor: transparent` y colores hex (`#c0392b` mortalidad, `#2ca02c` morbilidad). Se crea `src/constants/chartTheme.ts` con:

- Fuente y colores base (mortalidad/morbilidad) compartidos.
- Helpers para armar las opciones comunes tanto de Chart.js (`ChartJS.defaults`) como de ECharts (`option.textStyle`, `option.color`, etc.).
- Reutiliza `CLUSTER_COLORS` y `getClusterColor()` ya existentes en `src/constants/dashboardConstants.ts` (no se duplican).

## `useDashboardCharts.ts`

Las trazas actuales están en formato específico de Plotly (`{type: 'scatter', mode: 'lines+markers', ...}`). Se reescriben para devolver datos ya en el formato que consume cada librería nueva:

- Para los charts en Chart.js: forma `{ labels, datasets: [{ data, ...}] }`.
- Para los charts en ECharts: objeto `option` completo o los fragmentos de series/ejes que cada componente necesita.

El hook conserva su única responsabilidad actual: transformar los datos de análisis en estructuras de gráfica, sin hacer fetch ni cálculo de KPIs.

## Orden de migración (incremental)

Rollout incremental: cada paso migra un componente, se verifica visualmente en el navegador (golden path + estado vacío/sin datos), y solo entonces se pasa al siguiente. Durante la transición conviven Plotly, Chart.js y ECharts en el repo — Plotly se retira componente por componente, no de un tirón.

Orden, del más simple/seguro al más riesgoso:

1. `TrendChartsRow.tsx` → Chart.js (line, bar, pie)
2. `AtencionOportunidad.tsx` → Chart.js (bar)
3. `HeatmapDemoras.tsx` → ECharts (heatmap)
4. `SankeyMortalidad.tsx` → ECharts (sankey)
5. `SeveridadFallasMorbilidad.tsx` → ECharts (radar, bar, pie, box)
6. `ClusteringSection.tsx` → ECharts + echarts-gl (scatter 2D/3D)
7. Limpieza final: quitar `plotly.js`, `react-plotly.js`, `src/react-plotly.js.d.ts`; verificar que no quede ninguna referencia (`grep -r plotly`).

## Testing

No existen tests hoy para estos componentes. Por cada componente migrado se agrega un smoke test (vitest + `@testing-library/react`) que verifica:

- Renderiza sin crashear con datos de ejemplo.
- Renderiza sin crashear en estado vacío / sin datos.

No se busca snapshot de píxeles ni comparación visual automatizada — hoy tampoco existe para Plotly.

## Manejo de errores

Se mantiene el mismo patrón que hoy: los componentes ya manejan el caso "sin datos" mostrando un mensaje (p. ej. `ClusteringSection` con "Modelo de clustering no disponible"). Ese comportamiento se preserva 1:1 en la migración, solo cambia el motor de renderizado cuando sí hay datos.

## Fuera de alcance

- No se tocan endpoints backend ni la forma de los datos que entrega la API (`heatmap_demoras`, `sankey_flujo`, `severidad_fallas`, `pca_2d`/`pca_3d`, etc.).
- No se agregan gráficos nuevos ni se cambia el diseño visual/UX de los paneles, solo el motor de renderizado subyacente.
- No se hace benchmarking formal de rendimiento antes/después (fuera del objetivo de esta migración puntual).
