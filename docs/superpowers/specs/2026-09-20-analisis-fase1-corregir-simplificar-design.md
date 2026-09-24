# Fase 1: corregir y simplificar el Análisis

Fecha: 2026-09-20
Alcance: correcciones de indicadores, color y densidad visual del análisis, más una carga de datos de prueba realistas para poder ver el dashboard con proporciones creíbles.
Fuentes: `critica_dashboard_vidamaterna.md` (crítica experta aportada por el usuario) e informe del Ministerio de Salud *Trayectorias de la morbilidad y mortalidad materna en Colombia 2015-2024* (noviembre de 2025).
Fuera de alcance (proyectos aparte, ver "No incluido"): razón de mortalidad materna con nacidos vivos, filtros por fecha de ocurrencia / semana epidemiológica / territorio, mapa, agrupación de causas CIE-10, criterios del 549, calidad del dato, privacidad de la exportación.

## Contexto y hallazgos

- El usuario percibe el análisis como "una sopa": todo visible a la vez, con el mismo peso y con mucho texto.
- Los datos cargados son de prueba: `backend/scripts/generar_excels_prueba.py` usa `random.choice` uniforme, lo que explica las barras de causas casi iguales y la proporción MME:MM ≈ 1:1 (10.031 frente a 10.069).
- Referencia oficial (informe del Ministerio): 33.182 casos de MME en 2024 (15.109 en 2015); razón de MME de 22,9 a 72,6 por 1.000 nacidos vivos; razón de mortalidad materna de 45,6 por 100.000 nacidos vivos en 2024; 5.179 muertes maternas tempranas (evento 550) en el análisis 2015-2024. Es decir, decenas de casos de MME por cada muerte materna.
- El informe usa la expresión "índice de letalidad" para la MME (Gráfico 3), mientras que la crítica dice que la fórmula de la app, `MM / (MME + MM)`, es el "índice de mortalidad" del enfoque *near miss*. No se pudo leer la fórmula oficial (está en una imagen).
- Base de datos: PostgreSQL local (`sivigila_maternidad`, 83 MB) con 6 usuarios reales. No hay `pg_dump` en la máquina. **El análisis se calcula desde todos los casos acumulados en la base** (`_construir_df_desde_bd` devuelve "todos los casos de la base de datos" del tipo), no desde el último archivo subido. Por eso cargar datos realistas encima de los ~40.000 casos de prueba uniformes no serviría: habría que vaciar los casos. El equipo ya usa esa práctica (`backend/scripts/recortar_bd.py` hace `TRUNCATE`).
- El árbol de trabajo tiene cambios sin commitear ajenos a esta fase (`backend/api/routers/analisis.py`, `backend/schemas/analisis_schema.py`, `backend/services/ia_client.py`, `ia-service/*`, `frontend/.../api.ts`, `frontend/.../DashboardOKD.tsx`, `docs/TASKS.md`, `docs/PLAN_CHATBOT.md`). Esta fase no los toca ni los incluye en sus commits.

## Decisiones (las marcadas con ⚠ son mías y conviene validarlas)

1. **KPIs.** La franja pasa a cuatro celdas: Mortalidad materna 550, Morbilidad materna extrema 549, **Relación MME/MM** e **Índice de mortalidad**. Se elimina "Casos analizados" (suma de eventos distintos) y la alerta ámbar del 50 %.
2. ⚠ **Nombre del indicador.** "Tasa de letalidad" pasa a "Índice de mortalidad" con la fórmula `MM / (MME + MM) × 100` en un tooltip. El nombre está pendiente de validar con quien conozca los lineamientos del INS, porque el informe oficial usa "índice de letalidad" en el contexto de la MME.
3. **Color de eventos.** Mortalidad en vino `#9F1D35` y morbilidad en ámbar `#D9822B` (sustituyen a rojo y verde). Validados con `validate_palette.js`: separación para daltonismo ΔE 23,5 (antes 6,5); el ámbar queda en 2,85:1 de contraste, compensado con las etiquetas de valor visibles.
4. **Causas principales.** La barra mayor arriba (hoy se invierte la lista y sale abajo); número `n (%)` al final de cada barra; barras más compactas (unos 28 px por barra de una línea).
5. **Resumen de IA.** Un único panel plegable al final de la pantalla, cerrado por defecto, con el aviso "Generado automáticamente por IA local; requiere validación del equipo de vigilancia".
6. ⚠ **Filtros.** Se quita "Día de Reporte" de la barra (solo la interfaz; el estado interno no se toca) y la barra **deja de quedar fija**. No pude reproducir el botón cortado tras la barra fija; quitar el `sticky` elimina esa clase de problemas. Se puede reactivar.
7. **Datos de prueba realistas.** Reinicio controlado de los casos (con copia en CSV, sin tocar usuarios ni catálogos), un generador nuevo (sin modificar el actual) y su carga por la API.

## Componentes y cambios

### `KpiRow`

- Props nuevas: `totalMortalidad`, `totalMorbilidad`, `relacionMmeMm` e `indiceMortalidad` (números o `null` si no se pueden calcular; los calcula `calcularIndicadores` en `utils/indicadoresMaternos.ts`, que además solo los da con ambos eventos en el análisis), `yearCompareMort`, `yearCompareMorb`, `periodo?`. Se retiran `totalCasos`, `curTot` y `prevTot`.
- Celdas: (1) Mortalidad materna 550 con `TrendBadge`; (2) Morbilidad materna extrema 549 con `TrendBadge`; (3) **Relación MME/MM** = `totalMorbilidad / totalMortalidad`, mostrada como `N:1` con un decimal y formato es-CO, o `—` si no hay muertes; (4) **Índice de mortalidad** con `%` y un tooltip con la fórmula (botón con `Info`, `aria-label`, texto también para lectores de pantalla).
- Formato numérico es-CO en todas las cifras (`20.100`, `50,1 %`).
- Sin alerta de umbral.

### Colores

- `CHART_COLORS` en `constants/chartTheme.ts`: `mortalidad: '#9F1D35'`, `morbilidad: '#D9822B'`. `hooks/dashboard/useDashboardCharts.ts` deja de escribir los hexadecimales a mano y usa `CHART_COLORS`.
- Se actualizan los tests que fijan los valores antiguos.

### Gráficas de causas (`TrendChartsRow`, `useDashboardCharts`)

- `useDashboardCharts` deja de invertir la lista (`.reverse()`) para que la barra mayor quede arriba.
- `TopCausasChartData` gana `total` (registros del evento, para el porcentaje).
- Plugin propio de Chart.js (`barValueLabelsPlugin`, sin dependencias nuevas) en `utils/barValueLabels.ts`: dibuja `n (p %)` a la derecha de cada barra; el eje X deja margen para que no se recorten.
- `calculateChartHeight` pasa a ~28 px por barra de una línea (+20 px por línea extra); se actualizan sus constantes y su test.

### `AiSummaryPanel` (nuevo, `src/components/dashboard/AiSummaryPanel.tsx`)

- Botón de encabezado "Resumen ejecutivo (IA)" con `aria-expanded` / `aria-controls` y `ChevronDown` que gira; cerrado al inicio.
- Dentro: el aviso de validación y `NarrativasResumen` (sin cambios).
- `AnalysisHomeSection` lo coloca al final de la pantalla y deja de mostrar `NarrativasResumen` bajo los KPIs.

### `FiltersBar`

- Se retira el selector "Día de Reporte" y sus props (`filterDay`, `onDayChange`); "Limpiar" ya no llama a `onDayChange`.
- Se quita `lg:sticky lg:top-0 lg:z-10`.

### `AnalysisHomeSection`

Solo el JSX y las props que pasa a `KpiRow`, `FiltersBar` y el nuevo panel; los hooks y la lógica no cambian.

## Datos de prueba realistas (tareas previas)

1. **Reinicio controlado de casos** (`backend/scripts/reiniciar_datos_casos.py`), con el permiso explícito del usuario para borrar datos de prueba:
   - Simulación por defecto; solo borra con `--confirmar`.
   - Calcula las tablas afectadas (casos, análisis, importaciones y narrativas de IA, más todas las que dependan de ellas por clave foránea) y **aborta** si alguna es protegida: `api_usuario`, `cat_*`, `django_*`, `auth_*`.
   - Antes de borrar exporta cada tabla a CSV en `data/local/backup_<fecha>/` (carpeta ya ignorada por git), porque no hay `pg_dump`.
   - `TRUNCATE ... RESTART IDENTITY` en una sola transacción; después comprueba que los usuarios siguen intactos.
2. **Generador realista** (`backend/scripts/generar_excels_realistas.py`, con tests): reutiliza las funciones de `generar_excels_prueba.py` y sobrescribe las columnas clave con `random.choices` ponderado (semilla fija). **60 muertes maternas (550) y 3.000 casos de MME (549)** (relación 50:1); fechas entre 2025-01-01 y 2026-08-31; causas con distribución sesgada (trastornos hipertensivos primero); edades, zona, etnia, población vulnerable y afiliación con pesos realistas y solo valores de los catálogos. Salida en `data/pruebas/realista_*.xlsx` (esa ruta sí se versiona).
3. **Carga por la API** (`backend/scripts/cargar_excels_realistas.py`) con el usuario de pruebas de los e2e (`e2e@vidamaterna.co`, constantes públicas del helper).

## No incluido (proyectos aparte)

Razón de mortalidad materna y razón de MME (necesitan nacidos vivos del DANE); filtros por fecha de ocurrencia, semana epidemiológica, departamento y municipio; mapa y tendencia semanal; agrupación de causas CIE-10 y "Otras"; criterios de inclusión del 549; indicadores de calidad del dato; anonimización de la exportación y supresión de territorios con n < 5; qué datos recibe el modelo de IA; el aviso de "datos de prueba" (depende de identificar el origen del archivo). Varios requieren decisiones de quien conozca los lineamientos del INS.

## Pruebas

- `KpiRow.test.tsx`: reescrito para las nuevas celdas (relación con y sin muertes, formato es-CO, tooltip de la fórmula, ausencia de alerta y de "Casos analizados").
- `chartTheme.test.ts`: colores nuevos y el plugin de etiquetas.
- Hooks (`useDashboardCharts.test.ts`): orden de causas (mayor primero) y `total`.
- `causasChartLabels.test.ts`: nuevas alturas.
- `AiSummaryPanel.test.tsx` nuevo (cerrado por defecto, se abre y cierra, aviso visible al abrir, `NarrativasResumen` solo dentro).
- `FiltersBar.test.tsx`: sin el selector de día.
- `TrendChartsRow.test.tsx`: se mantienen sus pruebas de accesibilidad.
- Verificar `tsc -b`, `vite build`, `vitest run --testTimeout=30000` y, con los datos realistas cargados, una revisión visual del usuario.
