# Rediseño de KPIs y resumen de IA del análisis (Tailwind + lucide-react)

Fecha: 2026-09-20
Alcance: tercera parte del rediseño del frontend; primera sub-parte de "Análisis y gráficas". Componentes: `KpiRow`, `TrendBadge`, `NarrativaIA` (usado por `NarrativasResumen`) y `ChartAiInsight`.
Sub-partes pendientes de Análisis (cada una con su diseño): estructura de la pantalla, panel de filtros y exportación, gráficas.
Partes anteriores: `2026-09-20-auth-redesign-design.md` y `2026-09-20-dashboard-layout-redesign-design.md` (implementadas).

## Contexto

- Tailwind v4 y `lucide-react` configurados. Tokens: `brand-deep` (#290764), `brand-violet` (#4b0453), `brand-magenta` (#89005e). En `src/index.css` el magenta está pensado para "alertas de IA".
- Ubicación: `src/components/dashboard/` (`KpiRow.tsx`, `TrendBadge.tsx`, `ChartAiInsight.tsx`, `NarrativasResumen.tsx`) y `src/components/NarrativaIA.tsx`.
- Existe `NarrativasResumen.test.tsx` (6 tests, deben seguir pasando sin cambios). No hay tests de `KpiRow`, `TrendBadge` ni `ChartAiInsight`.
- `AnalysisHomeSection` usa estos componentes; sus props no cambian, así que ese archivo no se modifica.

## Decisiones

- KPIs: **franja compacta** (una sola tarjeta dividida en 4 celdas).
- Se **quitan** los textos explicativos y el chip "Revisar consistencia / Indicador estable".
- Resumen de IA: **tarjeta magenta suave** con ícono `Sparkles`.
- Tendencias: **subir en verde, bajar en rojo**.

## Componentes

### `KpiRow`

Props sin cambios: `totalCasos`, `totalMortalidad`, `totalMorbilidad`, `tasaLetalidad`, `curTot`, `prevTot`, `yearCompareMort`, `yearCompareMorb`.

- `section` con `aria-label="Resumen epidemiológico"`, blanca, borde `border-slate-200`, esquinas redondeadas y sombra suave.
- Rejilla de 4 celdas: 1 columna en móvil, 2 desde `sm`, 4 desde `lg`; divisores entre celdas.
- Cada celda: círculo suave con ícono (`aria-hidden`), etiqueta pequeña en gris, cifra grande en `text-brand-deep`, y la tendencia debajo.

| Celda | Etiqueta | Ícono | Cifra | Tendencia |
|---|---|---|---|---|
| 1 | Casos analizados | `Activity` | `totalCasos` | `TrendBadge` con `{ cur: curTot, prev: prevTot }` |
| 2 | Mortalidad materna 550 | `Droplet` | `totalMortalidad` | `TrendBadge` con `yearCompareMort` |
| 3 | Morbilidad materna extrema 549 | `Hospital` | `totalMorbilidad` | `TrendBadge` con `yearCompareMorb` |
| 4 | Tasa de letalidad | `Percent` | `{tasaLetalidad}%` | ninguna |

- **Letalidad alta:** si `Number.parseFloat(tasaLetalidad)` es finito y ≥ 50, la celda 4 usa fondo y cifra ámbar, con ícono `TriangleAlert`. Para no depender solo del color: `title="Valor atípicamente alto"` en la celda y un texto `sr-only` con el mismo mensaje.
- Se elimina `dominantEventLabel` y todo el texto de apoyo, el chip de calidad y el encabezado "Registro por evento / SIVIGILA".

### `TrendBadge`

Props sin cambios: `compare: CompareResult | null`. Misma lógica de cálculo.

| Caso | Salida |
|---|---|
| `compare` nulo | texto gris "Histórico" |
| `prev === 0` y `cur > 0` | píldora gris "Sin base previa" |
| `prev === 0` y `cur === 0` | píldora gris "Estable" |
| `pct > 0` | píldora verde con `TrendingUp` y `+N% vs ant.` |
| `pct <= 0` | píldora roja con `TrendingDown` y `N% vs ant.` |

El signo y los decimales se calculan como hoy (`pct.toFixed(0)`, `+` solo si `pct >= 0`). Nota: hoy `pct === 0` cae en la clase `trend-down`; se mantiene esa regla (rojo con `+0% vs ant.`) para no cambiar la lógica en un rediseño visual. Los íconos llevan `aria-hidden`.

### `NarrativaIA` (`src/components/NarrativaIA.tsx`)

Props y lógica sin cambios (`analisisId`, `tipo`, `titulo`, `filtros`; estados `idle | loading | success | unavailable | error`; `unavailable` devuelve `null`).

- Tarjeta: `rounded-xl border border-brand-magenta/30 bg-brand-magenta/5 p-4`, con un margen superior para separarla de lo anterior (no se usa un contenedor envolvente: los tests esperan que no quede ningún nodo cuando el bloque desaparece).
- Cabecera: `Sparkles` (`aria-hidden`) y el `titulo` en `brand-deep`, semibold.
- Botones ("Generar resumen IA", "Regenerar", "Reintentar"): botón principal `bg-brand-magenta`, texto blanco; "Regenerar" y "Reintentar" con `RefreshCw` (`aria-hidden`). Los textos no cambian.
- `loading`: `Loader2` girando y el texto "Generando narrativa..." con `role="status"`.
- `success`: el texto de la narrativa en gris oscuro, y el botón Regenerar alineado a la derecha.
- `error`: "No se pudo generar la narrativa. Intenta de nuevo." en rojo con `role="alert"`.

### `NarrativasResumen`

Sin cambios de código.

### `ChartAiInsight`

Misma familia visual, más ligera: `rounded-lg border border-brand-magenta/20 bg-brand-magenta/5 p-3`, `Sparkles` y la etiqueta "Lectura automatizada" pequeña en `brand-magenta`, y el texto debajo. Sigue devolviendo `null` sin `insight`. Se cambia el tipo `React.FC` por una función normal con `ChartAiInsightProps` (la exportación con nombre `ChartAiInsight` se mantiene).

## Se elimina

- Las clases CSS ya inexistentes de estos cuatro componentes (`epidemiology-summary`, `summary-*`, `surveillance-register`, `register-*`, `case-fatality-*`, `kpi-trend-period`, `trend-badge`, `chart-ai-insight`, `narrativa-ia`, `btn-mini-toggle`).
- El uso de `BloodDropIcon` y `HospitalIcon` en `KpiRow`. Sus archivos **no** se borran: `WelcomeState` aún los usa.

## Accesibilidad

- Íconos decorativos con `aria-hidden="true"`.
- Alerta de letalidad alta con texto para lectores de pantalla y `title`.
- Los estados de la narrativa mantienen `role="status"` / `role="alert"`.

## Pruebas

- `NarrativasResumen.test.tsx`: sin cambios, debe seguir pasando (protege `NarrativaIA`).
- Nuevo `TrendBadge.test.tsx`: los cinco casos de la tabla, incluido el signo y `pct === 0`.
- Nuevo `KpiRow.test.tsx`: muestra las cuatro etiquetas y cifras; la letalidad < 50 no muestra la alerta; ≥ 50 sí (texto `sr-only` "Valor atípicamente alto"); tasa no numérica no muestra alerta.
- Nuevo `ChartAiInsight.test.tsx`: devuelve nada sin `insight` y muestra etiqueta y texto con él.
- Verificar `tsc -b`, `vite build` y `vitest run --testTimeout=30000`.
