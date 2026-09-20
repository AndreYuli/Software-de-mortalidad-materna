# Corrección de nombres en gráficas "Top Causas" — Spec de Diseño

**Fecha:** 2026-09-14
**Depende de:** ninguna
**Contexto:** El usuario reportó que "los nombres de las variables de las gráficas" no quedan completamente visibles junto a su barra. Se investigó el código de todas las gráficas visibles hoy en el dashboard (`AnalysisHomeSection.tsx` y sus hijos) y se confirmó que el único caso real es el de las gráficas "Top 10 Causas de Mortalidad/Morbilidad" en `TrendChartsRow.tsx`: el nombre de la causa CIE-10 se corta a 2 líneas de 45 caracteres con `"..."` cuando es más largo, tanto en el eje como en el tooltip. Las demás gráficas activas (`DistribucionEdadGestacional`, `DistribucionEdadRiesgo`, KPIs) usan etiquetas cortas y no presentan el problema. Este es el primero de 4 mejoras que el usuario pidió abordar por separado (historial de subidas, gráficas sociodemográficas nuevas, y cruce sociodemográfico×clínico quedan para specs futuras).

---

## Objetivo

Que el nombre completo de cada causa CIE-10 sea siempre legible junto a su barra en las gráficas "Top 10 Causas de Mortalidad" y "Top 10 Causas de Morbilidad", sin recortes ni `"..."`, tanto en el eje como en el tooltip.

## Fuera de alcance

- No se tocan otras gráficas (`DistribucionEdadGestacional`, `DistribucionEdadRiesgo`, KPIs, `ExportReportModal`) — no tienen este problema hoy.
- No se cambia el origen de los nombres (`getCie10Description` / `cie10Nombres.json` en `dashboardConstants.ts`) — el texto en sí ya es correcto, el problema es solo de presentación.
- No se agregan gráficas nuevas (radar de fallas, heatmap demoras×causas, etc. — eso es fuera de esta spec).

---

## Estado actual (verificado en código)

- `TrendChartsRow.tsx` define `wrapLabel(text, maxLen = 45)`: parte el texto en líneas de máximo 45 caracteres: si el resultado tiene más de 2 líneas, se queda solo con las 2 primeras y le agrega `"..."` a la segunda. Esto se aplica en `labels: topCausasMortalidad.labels.map((l) => wrapLabel(l))` y su equivalente de morbilidad — bloques casi idénticos, uno para mortalidad y otro para morbilidad, dentro del mismo archivo.
- El contenedor de cada gráfica tiene `style={{ height: '320px' }}` fijo, sin relación con la cantidad de líneas que ocupan las etiquetas.
- No hay callback de tooltip configurado (`options.plugins.tooltip` no se define), así que Chart.js usa el array ya truncado por `wrapLabel` como título del tooltip — el texto completo original nunca se ve, ni pasando el mouse por encima.
- Las gráficas son de Chart.js vía `react-chartjs-2`, `indexAxis: 'y'` (barras horizontales), hasta 10 barras (`slice(0, 10)` ya aplicado en `useDashboardCharts.ts` antes de llegar al componente).
- Existe `TrendChartsRow.test.tsx` con pruebas de renderizado básico (con datos y con lista vacía), sin aserciones sobre el contenido de las etiquetas.

---

## Diseño

### 1. `wrapLabel` sin truncar

Se mantiene el partido en líneas de ~45 caracteres por palabra completa (igual que hoy), pero se elimina el límite de 2 líneas y el `"..."` — devuelve todas las líneas necesarias para el texto completo. Pasa de ser una constante local a una función **exportada** (`export function wrapLabel(...)`) para poder probarla de forma aislada sin depender del canvas de Chart.js (ver sección de pruebas).

### 2. Alto dinámico del contenedor

Se reemplaza el `height: '320px'` fijo por un cálculo basado en el contenido, en una nueva función **exportada** `calculateChartHeight(labels: string[]): number`:

- Por cada etiqueta, cuenta cuántas líneas produce `wrapLabel`.
- Alto = `Math.max(320, ejeXyPadding + numBarras * alturaPorBarra)`, donde `alturaPorBarra` crece según el máximo de líneas entre todas las etiquetas (aprox. 28px por línea de texto + espacio mínimo por barra) y `ejeXyPadding` es un margen fijo (~60px) para el título del eje X.
- Con pocas barras o etiquetas cortas, el resultado nunca baja de 320px (mismo aspecto que hoy).

### 3. Tooltip con texto completo

Se agrega `options.plugins.tooltip.callbacks.title` que devuelve el nombre original sin dividir en líneas (usando el array de `labels` original, no el ya envuelto), como respaldo aunque el eje ya muestre todo.

### 4. Extraer subcomponente compartido `CausasBarChart`

Los dos bloques de gráfica (mortalidad/morbilidad) son casi idénticos salvo color, título y mensaje de "sin registros". Se extrae un subcomponente interno `CausasBarChart` (mismo archivo `TrendChartsRow.tsx`, no exportado) que recibe `title`, `data: TopCausasChartData`, `emptyMessage` y `insight`, y encapsula el wrap sin truncar + alto dinámico + tooltip completo en un solo lugar. `TrendChartsRow` pasa a renderizar dos `<CausasBarChart />` en vez de duplicar el JSX y la config de Chart.js.

---

## Cambios de archivo

1. **`FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`**
   - `wrapLabel`: quitar el límite de 2 líneas y el `"..."`.
   - Nueva función auxiliar para calcular el alto dinámico a partir de las etiquetas.
   - Nuevo subcomponente interno `CausasBarChart` que reemplaza los dos bloques duplicados; agrega el callback de tooltip con el texto original.
   - `TrendChartsRow` queda como wrapper que arma el layout (`charts-grid-row`) y renderiza `<CausasBarChart>` dos veces.
2. **`FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`**
   - Pruebas unitarias directas sobre `wrapLabel` (exportada): con un texto largo (>90 caracteres) devuelve un array de más de 2 líneas y ninguna línea termina en `"..."`; con un texto corto devuelve el texto tal cual.
   - Pruebas unitarias directas sobre `calculateChartHeight` (exportada): con etiquetas cortas devuelve 320 (el mínimo); con etiquetas largas (que generan varias líneas) devuelve un valor mayor a 320, y ese valor crece si se agregan más barras o etiquetas más largas.
   - Las dos pruebas existentes de renderizado (con datos / estado vacío) deben seguir pasando sin cambios — no dependen de inspeccionar el contenido del canvas.

No se toca `useDashboardCharts.ts` (el `slice(0, 10)` y la construcción de labels/values no cambian), ni `dashboardConstants.ts`, ni `AnalysisHomeSection.tsx`.

---

## Verificación

- `pnpm exec tsc -b`, `pnpm run lint`, `pnpm run test` en verde.
- Verificación visual manual: `pnpm run dev`, cargar un análisis con causas CIE-10 de nombre largo, confirmar que el nombre completo se lee junto a la barra en ambas gráficas (mortalidad y morbilidad) y que el tooltip también muestra el texto completo.
