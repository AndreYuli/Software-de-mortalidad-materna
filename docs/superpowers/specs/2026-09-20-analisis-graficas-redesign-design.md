# Rediseño de las gráficas del Análisis (Tailwind + Chart.js)

Fecha: 2026-09-20
Alcance: quinta parte del rediseño del frontend; tercera sub-parte de "Análisis y gráficas". Cubre las cinco gráficas del análisis y su tarjeta contenedora.
Pendiente de Análisis: modal de exportación.
Partes anteriores: auth, layout, KPIs/IA y estructura/filtros (todas implementadas).

## Contexto y problemas detectados

- Las cinco gráficas son de **Chart.js** (`react-chartjs-2`, `Bar`), todas con `maintainAspectRatio: false`, que exige un contenedor con altura fija. **ECharts no se usa** en ninguna gráfica (solo queda referenciado en `constants/chartTheme.ts` y `package.json`); no se toca en esta parte.
- **Sin altura:** al quitar los estilos inline (commit `6ba5c070`), los contenedores de las gráficas perdieron su altura (280 px en las de edad; en las demás, la que calculaba `calculateChartHeight`). Además `calculateChartHeight` dejó de usarse en `TrendChartsRow`, `SociodemographicChartsSection` y `CruceVariablesSection`. Esta parte lo resuelve.
- **Paleta del cruce inválida:** `CRUCE_PALETTE` no pasa `validate_palette.js` (dos colores fuera de la banda de luminosidad, pares que se confunden en deuteranopía) y se repite (`j % 8`) a partir de la 9.ª serie.
- **Color por barra:** las gráficas sociodemográficas pintan cada barra de un color distinto (8 colores) aunque es una sola serie; el color debe identificar una serie, no la posición de la barra.
- Tests que se ven afectados: `SociodemographicChartsSection.test.tsx` busca la clase `.sociodemographic-grid`, que ya no existe en ningún CSS. `CruceVariablesSection.test.tsx` mockea `Bar` y lee sus `options`; `chartTheme.test.ts` fija `CHART_COLORS.mortalidad/morbilidad` (`#c0392b`, `#2ca02c`).
- Fuente de las reglas de color: la skill `dataviz` (una serie = un color; no repetir colores; validar la paleta con su script; marcas finas).

## Decisiones

- **Causas:** se mantienen rojo (mortalidad, `#c0392b`) y verde (morbilidad, `#2ca02c`).
- **Sociodemográficas:** todas las barras en el magenta de marca `#89005e`.
- **Edad y edad gestacional:** se mantienen `STATUS_COLORS` (riesgo rojo `#dc2626`, resto gris `#64748b`, ya validados).
- **Cruce:** paleta categórica validada de la skill `dataviz` (orden fijo): `#2a78d6`, `#eb6834`, `#1baf7a`, `#eda100`, `#e87ba4`, `#008300`, `#4a3aa7`, `#e34948`. **Pendiente conocido:** con más de 8 series los colores se repiten (comportamiento actual); agrupar las sobrantes en "Otras" queda para un cambio aparte.
- **Barras delgadas** (a petición del usuario): máximo 16 px y 60 % de la fila en las horizontales; máximo 40 px en las verticales (pocas barras).
- Sin estilos inline: las alturas salen de una tabla de clases fijas.

## Componentes y utilidades

### `ChartCard` (nuevo, `src/components/dashboard/ChartCard.tsx`)

Props: `title: string`, `eyebrow?: string`, `description?: string`, `insight?: string | null`, `children: ReactNode`.

- `<article>` blanco, `rounded-xl border border-slate-200 p-5 shadow-sm`.
- Cabecera: `eyebrow` (pequeño, `uppercase tracking-wider text-brand-magenta`), `title` en `<h3 className="text-lg font-semibold text-brand-deep">` y `description` en `text-sm text-slate-500`.
- Cuerpo: `children`.
- Pie: si hay `insight`, `<ChartAiInsight insight={insight} />`.
- Los textos vacíos ("Sin datos suficientes…") se pintan dentro de la misma tarjeta como `<p className="text-sm text-slate-500">`.

### `chartHeightClass` (nuevo, `src/utils/chartHeight.ts`)

`chartHeightClass(pixels: number): string`. Tabla de literales de Tailwind (para que el escaneo de clases los encuentre): `h-80` (320), `h-[400px]`, `h-[480px]`, `h-[560px]`, `h-[640px]`, `h-[720px]`, `h-[800px]`, `h-[880px]`, `h-[960px]`, `h-[1040px]`, `h-[1120px]`, `h-[1200px]`, `h-[1280px]`. Devuelve la primera cuya altura sea ≥ `pixels`; por encima del máximo devuelve la última. Constante `CHART_HEIGHT_FIXED = 'h-[280px]'` para las de edad.

### `describeSeries` (nuevo, `src/utils/chartA11y.ts`)

`describeSeries(title: string, labels: string[], values: number[]): string`. Devuelve `"{title}. {label1}: {v1}; {label2}: {v2}…"` para el `aria-label` de las gráficas. Con listas vacías devuelve solo el título.

### `chartTheme.ts` (ampliación)

Se añaden: `BRAND_COLOR = '#89005e'`; `CATEGORICAL_PALETTE` (la de arriba, en ese orden); y los estilos de barra `BAR_STYLE_HORIZONTAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 16, barPercentage: 0.6 }` y `BAR_STYLE_VERTICAL = { borderRadius: 4, borderWidth: 0, maxBarThickness: 40 }`. Los exports existentes no cambian.

### Gráficas

Todas conservan sus datos, hooks, textos y opciones de Chart.js (ejes, tooltips, márgenes del eje Y). Cambian: la tarjeta (`ChartCard`), el contenedor con altura, el estilo de barra, los colores indicados y el `role="img"` + `aria-label` en el `<canvas>` (vía las props de `Bar`).

- **`TrendChartsRow`:** cabecera de sección (`Priorización clínica`, `h2 Causas principales notificadas`, el texto actual) y dos `ChartCard` en `grid gap-6 lg:grid-cols-2`. Cada `CausasBarChart` usa `eyebrow` ("Evento 550"/"Evento 549"), su título, altura `chartHeightClass(calculateChartHeight(data.labels))`, `BAR_STYLE_HORIZONTAL` y el color que ya trae `data.colors`. Estado vacío con su mensaje actual.
- **`DistribucionEdadRiesgo` y `DistribucionEdadGestacional`:** una `ChartCard` cada una (título con el evento y la descripción actuales), altura `h-[280px]`, `BAR_STYLE_VERTICAL`, colores por barra actuales.
- **`SociodemographicChartsSection`:** título de sección `h3` ("Factores Sociodemográficos ({evento})") y un contenedor `grid gap-6 lg:grid-cols-2` con `data-testid="sociodemographic-grid"` que aloja una `ChartCard` por variable con datos (descripción: "Total: N casos con dato registrado"). Todas las barras en `BRAND_COLOR`, altura `chartHeightClass(calculateChartHeight(labels))`, `BAR_STYLE_HORIZONTAL`. Se elimina `SOCIO_PALETTE`.
- **`CruceVariablesSection`:** una `ChartCard`; los dos selectores (`Variable sociodemográfica`, `Variable clínica`, con los mismos `id` y etiquetas) en `grid gap-4 sm:grid-cols-2` con el mismo estilo que los de `FiltersBar`; `Calculando cruce…` con `role="status"`, el error con `role="alert"`, y el mensaje de sin datos. Series con `CATEGORICAL_PALETTE[j % 8]`, altura `chartHeightClass(calculateChartHeight(data.categorias_socio))`, `BAR_STYLE_HORIZONTAL`. Se elimina `CRUCE_PALETTE`.

## Sin cambios

Datos, hooks (`useDashboardCharts`, `useCruceVariables`), utilidades de lectura de IA, `wrapLabel`/`calculateChartHeight`, `Y_AXIS_WIDTH_SAFETY_MARGIN` y los márgenes de eje.

## Se elimina

Las clases CSS inexistentes de estos componentes (`chart-card-col-12`, `chart-card-title`, `epidemiology-chart-card`, `chart-card-heading`, `chart-card-eyebrow`, `causes-*`, `charts-grid-row`, `sociodemographic-*`, `field-label`, `custom-select-wrapper`, `sidebar-select`) y las paletas `SOCIO_PALETTE` y `CRUCE_PALETTE`.

## Accesibilidad

- Cada `<canvas>` con `role="img"` y `aria-label` generado con `describeSeries`.
- Estados de carga/error del cruce con `role="status"` / `role="alert"`.
- Colores: la paleta del cruce se valida con `validate_palette.js` (`--mode light`, sin FAIL; los avisos de contraste se compensan con la leyenda visible). El resto de colores no son solo color: cada barra tiene su etiqueta en el eje.

## Pruebas

- Nuevos: `ChartCard.test.tsx`, `chartHeight.test.ts`, `chartA11y.test.ts`, y en `chartTheme.test.ts` un caso para las constantes nuevas.
- Actualizado: `SociodemographicChartsSection.test.tsx` (usa `data-testid="sociodemographic-grid"`).
- Los demás tests de gráficas (`TrendChartsRow`, `DistribucionEdad*`, `CruceVariablesSection`, `ChartAiInsight`) deben pasar sin cambios.
- Verificar la paleta del cruce con el script, y `tsc -b`, `vite build`, `vitest run --testTimeout=30000`.
