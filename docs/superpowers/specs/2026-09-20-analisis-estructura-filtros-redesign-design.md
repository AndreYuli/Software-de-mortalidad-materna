# Rediseño de la estructura del Análisis y de la barra de filtros (Tailwind + lucide-react)

Fecha: 2026-09-20
Alcance: cuarta parte del rediseño del frontend; segunda sub-parte de "Análisis y gráficas". Cubre el reparto de la pantalla, el encabezado, las pestañas, la barra de filtros y los estados de carga, error y bienvenida.
Sub-partes pendientes de Análisis: modal de exportación y gráficas.
Partes anteriores: auth, layout del dashboard y KPIs/IA (todas implementadas).

## Contexto

- Tailwind v4 y `lucide-react` configurados. Tokens: `brand-deep` (#290764), `brand-violet` (#4b0453), `brand-magenta` (#89005e).
- Hoy `AnalysisHomeSection` reparte la pantalla en una columna principal y una columna de filtros a la derecha (`FiltersSidebar`, un `<aside>` vertical).
- Componentes implicados, en `src/components/dashboard/`: `AnalysisHomeSection.tsx`, `SubTabs.tsx`, `FiltersSidebar.tsx`, `WelcomeState.tsx`, `DashboardLoadingState.tsx`, `DashboardErrorState.tsx`.
- `DashControlBar.tsx` no lo usa ningún archivo (código muerto). `FilterPanel.tsx` tampoco; se deja para la parte del modal de exportación.
- Tests existentes que se ven afectados: `FiltersSidebar.test.tsx` (4 tests) y `SubTabs.test.tsx` (3 tests; uno comprueba la clase `active`).
- Restricción e2e: `e2e/dashboard.spec.ts` usa `page.getByRole('combobox').first()`; el selector de Evento debe seguir siendo el primer `combobox` del DOM.

## Decisiones

- Los filtros pasan a una **barra horizontal** encima del contenido (se elimina la columna derecha).
- Pestañas principales **subrayadas**; subpestañas como **píldoras**.
- En móvil la barra de filtros es **plegable** con un botón "Filtros".
- La barra queda fija arriba al hacer scroll solo desde `lg`; en móvil no, para no chocar con la barra superior del menú.

## Reparto de la pantalla (`AnalysisHomeSection`)

Solo cambia el JSX; la lógica (hooks, memos, estados de carga/error/bienvenida, exportación) y las props no cambian.

- Contenedor único: `flex flex-col gap-6`. Orden: encabezado, pestañas principales, barra de filtros, KPIs, resúmenes de IA, contenido de la pestaña activa.
- Desaparece el envoltorio en dos columnas (`dashboard-analysis-layout`, `dashboard-analysis-main`) y la columna de filtros.
- `ExportReportModal` sigue montado al final con las mismas props.

### Encabezado (inline en `AnalysisHomeSection`)

- Etiqueta "Vigilancia materna SIVIGILA": `text-xs font-semibold uppercase tracking-wider text-brand-magenta`.
- `h1` "Sistema de análisis epidemiológico": `text-2xl font-bold text-brand-deep`.
- Subtítulo "Lectura técnica de mortalidad materna 550 y morbilidad materna extrema 549": gris.
- Si existe `ultimaSemanaReportada`: etiqueta con `CalendarClock` y el texto "Última carga: Semana {semana} de {anio}".

## Componentes

### `MainTabs` (nuevo, `src/components/dashboard/MainTabs.tsx`)

Props: `active: MainTab`, `onChange: (tab: MainTab) => void` (`MainTab` se importa de `hooks/navigation/useDashboardTabs`).

- Contenedor con `role="tablist"` y `aria-label="Secciones del análisis"`, `border-b border-slate-200`, `flex gap-6`, con desplazamiento horizontal si no caben.
- Cada pestaña: `<button type="button" role="tab" aria-selected>` con etiquetas `Generalidades`, `Morbilidad (Ev. 549)`, `Mortalidad (Ev. 550)` (mismas que hoy), en ese orden.
- Estilo: inactiva `text-slate-500 hover:text-slate-800`; activa `text-brand-magenta` con `border-b-2 border-brand-magenta`; `-mb-px` para que la línea solape el borde del contenedor.

### `SubTabs` (rediseño)

Props y exportaciones sin cambios (`active: SubTab`, `onChange`). Etiquetas: `Factores Sociodemográficos`, `Factores Clínicos`.

- Contenedor `role="tablist"` con `aria-label="Factores"`, `flex flex-wrap gap-2`.
- Cada botón `type="button" role="tab" aria-selected`, con forma de píldora: activa `bg-brand-magenta text-white`; inactiva `bg-slate-100 text-slate-600 hover:bg-slate-200`.
- Se sustituye la clase `active` por `aria-selected`.

### `FiltersBar` (renombre de `FiltersSidebar`, `src/components/dashboard/FiltersBar.tsx`)

Se renombra archivo y componente (`git mv`); el tipo pasa a `FiltersBarProps`. **Las props no cambian.**

- Contenedor `<section aria-label="Filtros del análisis">`: fondo blanco, borde `border-slate-200`, esquinas redondeadas, sombra suave, relleno. Desde `lg`: `sticky top-0 z-10`.
- **Fila de acciones** (siempre visible): botón "Filtros" (`SlidersHorizontal`, solo visible bajo `lg`, con `aria-expanded` y `aria-controls`; muestra un puntito `bg-brand-magenta` si `hasActiveFilters`) y botón "Exportar Reporte" (`Download`, botón principal magenta) a la derecha.
- **Panel de selectores** (`id` referenciado por `aria-controls`): bajo `lg` se muestra solo cuando está desplegado (estado local `open`, cerrado al inicio); desde `lg` siempre visible en una fila (`lg:grid lg:grid-cols-5`, o flex), y en móvil en una columna.
- Selectores, en este orden y con estas etiquetas visibles (encima, pequeñas): `Evento` (solo si hay `segmento` y `onSegmentoChange`), `Año de Reporte`, `Mes de Reporte`, `Semana de Reporte`, `Día de Reporte`. Ids `filter-segmento`, `filter-year`, `filter-month`, `filter-week`, `filter-day`.
- Opciones y reglas de deshabilitado sin cambios: año deshabilitado sin años disponibles; mes y semana deshabilitados sin año; día deshabilitado sin mes. Opciones de Evento: `549 + 550 integrados`, `Solo mortalidad 550` (si hay `latestMortalidad`), `Solo morbilidad 549` (si hay `latestMorbilidad`). 53 semanas y 31 días como hoy.
- `Limpiar`: aparece si `hasActiveFilters` y llama a los cuatro `onXChange('')`, igual que hoy. Visible en la fila de acciones.
- Las frases de ayuda ("Define el universo analítico…", "* Selecciona un año primero…", "* Selecciona un mes primero…") dejan de mostrarse: pasan a texto `sr-only` enlazado con `aria-describedby` y a `title` del selector deshabilitado.
- El selector de Evento es el primer `combobox` del DOM.

### `WelcomeState`

Props sin cambios (`onGoToUpload`). Misma lógica (`showChoices`).

- Tarjeta centrada, blanca, con borde y sombra: círculo `bg-brand-magenta/10` con `FileText`, título "Análisis Epidemiológico", texto explicativo actual y el botón principal "Importar Datos Epidemiológicos".
- Al pulsar: dos botones-tarjeta en cuadrícula: "Mortalidad" con `Droplet` y subetiqueta "Evento 550", "Morbilidad Extrema" con `Hospital` y "Evento 549"; cada uno llama a `onGoToUpload('mortalidad' | 'morbilidad')`.

### `DashboardLoadingState`

Ícono `Loader2` girando y el texto "Generando panel estratégico...", centrados, con `role="status"`.

### `DashboardErrorState`

Props sin cambios (`message`, `onRetry?`). Tarjeta centrada con `AlertCircle` rojo, el mensaje con `role="alert"` (se quita el emoji ❌) y el botón "Reintentar" (principal magenta); sin `onRetry` recarga la página (`window.location.reload()`), igual que hoy.

### `NarrativaIA`

Se quita el `mt-4` de la tarjeta (el espacio lo pone el `gap-6` del contenedor). Sin otros cambios.

## Sin cambios

Toda la lógica de `AnalysisHomeSection` y sus hooks, `useDashboardTabs` (incluido reiniciar la subpestaña a "Factores Clínicos" al cambiar de pestaña principal), las props de `AnalysisHomeSection` y de los componentes de contenido, y `ExportReportModal`.

## Se elimina

- `DashControlBar.tsx` (sin usos).
- Las clases CSS inexistentes de estos componentes.
- Los usos de `BloodDropIcon`, `HospitalIcon` y `DocumentIcon` en `WelcomeState`. Si tras el cambio no queda ningún uso en `src` fuera de `components/icons/`, se borran esos archivos y sus exportaciones de `icons/index.ts` (como en las partes anteriores).

## Accesibilidad

- Pestañas con `tablist` / `tab` / `aria-selected`; íconos decorativos con `aria-hidden="true"`.
- Botón "Filtros" con `aria-expanded` y `aria-controls`; el puntito de filtros activos no es solo visual (el botón conserva su nombre y se añade texto `sr-only` "hay filtros activos").
- Estados con `role="status"` / `role="alert"`.
- Cada selector con su `<label htmlFor>`.

## Pruebas

- `FiltersSidebar.test.tsx` pasa a `FiltersBar.test.tsx` con los 4 casos actuales (importan `FiltersBar`) más: el botón "Filtros" alterna el panel y `aria-expanded`; el puntito/aviso de filtros activos aparece solo con algún filtro; "Exportar Reporte" llama a `onExport`; el selector de Evento es el primer `combobox`.
- `SubTabs.test.tsx`: se cambia la comprobación de la clase `active` por `aria-selected`.
- Nuevos: `MainTabs.test.tsx`, `WelcomeState.test.tsx`, `DashboardStates.test.tsx` (carga y error, incluido `onRetry` y el recargar).
- `AnalysisHomeSection` no tiene tests; se verifica con `tsc`, el build y la suite.
- Verificar `tsc -b`, `vite build` y `vitest run --testTimeout=30000`.
