# Auditoría CSS — MaternAnalytics (VidaMaterna)

Fecha: 2026-09-17
Alcance: `FRONTED/maternanalytics/src/**/*.css` (14 archivos), `App.tsx`, `main.tsx`, `DashboardOKD.tsx`, `Login.tsx`, `Register.tsx`, `ViewRouter.tsx`, `vite.config.js`, `package.json`.
Build: `npm run build` pasa (`tsc -b && vite build` OK). Los problemas son arquitectónicos / visuales, no de compilación.

---

## Crítica 1 — `overflow: hidden` global rompe el scroll (CRÍTICO)

**Dónde:** `src/components/LoginLayout.css:20-26`

```css
html, body {
  height: 100%;
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--cream);
  color: var(--text-dark);
  overflow: hidden;
}
```

**Por qué está mal:**
- El proyecto no usa CSS Modules ni Tailwind. Todo el CSS es global y Vite lo empaqueta en 1-2 bundles (`dist/assets/*.css`). El `overflow: hidden` declarado para el login **persiste al navegar a `/dashboard`** y bloquea el scroll de todo el contenido.
- Hay doble definición de base: `src/index.css:1-5` (`* { margin:0; padding:0; box-sizing })` y `LoginLayout.css:6-10` (mismo reset + `*::before, *::after`). También doble `html, body` (`index.css:21-24` vs `LoginLayout.css:20-26`) con distinto `background` (`#f5f5f5` vs `var(--cream)`). Gana el último en orden de bundle: comportamiento impredecible.
- El responsive del login (`LoginLayout.css:87-122`) intenta compensar con `.bottom-bar { position: static }`, señal de que el `hidden` ya molesta en móvil.

**Fix sugerido:**
```css
/* Quitar overflow:hidden de html, body. Scoparlo: */
.page { overflow: hidden; }
@media (max-width: 900px) {
  .page { overflow-y: auto; }
}
```
Y dejar UN solo reset + UN solo `html, body` en `index.css`.

---

## Crítica 2 — Dos sistemas de diseño conviviendo (ALTO)

**Dónde:** `src/index.css:7-19` vs resto del dashboard.

- `index.css` define `--blue-900 ... --blue-100` + `--pink-500`.
- `LoginLayout.css:13-18` añade `--cream, --text-dark/mid/light` solo para login.
- El dashboard ignora esas variables y hardcodea `#0f766e` (teal) en ~100 ocurrencias: `DashboardShell.css:57,61-62`, `StrategicDashboard.css:35,77,90...`, `Sidebar.css:111-113`, `FiltersSidebar.css:12`, `UploadSection.css:82,89...`, etc.

**Por qué está mal:**
- Login azul vs dashboard teal: identidad visual partida.
- Cambiar un color primario obliga a editar 7 archivos con buscar/reemplazar.
- `reportExporter.ts:171-195,386-451` repite los hex en strings de HTML para el reporte, tercer lugar que mantener sincronizado.

**Fix sugerido:** centralizar tokens en `index.css`:
```css
:root {
  --brand-900: #0f172a;
  --brand-700: #0f766e;
  --brand-500: #14b8a6;
  /* ... */
}
```
y reemplazar los hex literales progresivamente.

---

## Crítica 3 — Clases genéricas globales, alto riesgo de colisión (ALTO)

**Dónde:** `Login*.css`, `UploadHistorySection.css:7`, `Spinner.css:9`.

Nombres sin namespace: `.page`, `.left`, `.right`, `.field`, `.field-icon`, `.tag`, `.blob`, `.node`, `.spinner`, `.section-title`, `.form-container`, `.bottom-bar`, `.brand-title`.

**Por qué está mal:**
- Cualquier componente nuevo con `.page` o `.field` hereda estilos del login sin querer.
- Confusión real existente: `.brand-title` (login, `LoginDecorations.css:150`, DM Serif 42px blanco) vs `.brand-title-okd` (sidebar, `Sidebar.css:58`, `font: inherit`). Mismo concepto, dos APIs.
- `.section-title` (`UploadHistorySection.css:7`) es tan genérico que invita a reutilización accidental.
- `@keyframes spin` duplicado idéntico en `Spinner.css:19-21` y `UploadHistorySection.css:35-37`. `spinnerRotate` en `UploadSection.css:487` hace lo mismo con otro nombre. Tres spinners para una app.

**Fix sugerido:** prefijo por dominio (`login-page`, `login-field`...) o migrar a CSS Modules (`Login.module.css`). Consolidar un solo `Spinner` + un solo `@keyframes spin`.

---

## Crítica 4 — Sintaxis nesting SCSS en archivos `.css` planos (MEDIO-ALTO)

**Dónde:** `LoginForm.css:16-29` (`.form-header { h2 {...} p {...} }`), `LoginForm.css:36-73` (`.field { label, input { &:focus, &::placeholder, &:focus-visible } }`), `LoginLayout.css:62` (`.right { &::before }`), `LoginForm.css:172-197` (`.btn-login { &:hover, &:active, &::after }`), `LoginDecorations.css:158-161` (`.brand-title { span {...} }`).

**Por qué está mal:**
- `package.json` no tiene `sass` y `vite.config.js` no configura `postcss-nesting`. Hoy compila porque Vite 8 + navegadores modernos soportan CSS Nesting nativo, pero:
  1. En navegadores viejos (Edge legacy, WebView antiguos institucionales) esas reglas se **ignoran en silencio** → formulario sin estilos de focus/hover.
  2. Es inconsistente: el dashboard usa CSS plano clásico, el login usa nesting. Dos dialectos en el mismo repo.
- El anidado profundo (4 niveles en `.remember input:checked::after`) eleva especificidad sin necesidad.

**Fix sugerido:** o añadir preprocesador de forma explícita, o aplanar:
```css
.form-header h2 { ... }
.field input:focus { ... }
```

---

## Crítica 5 — 86 estilos inline duplicando el CSS (MEDIO)

**Dónde (grep `style=` en `src/`):** `ExportReportModal.tsx` (~15 bloques inline), `CruceVariablesSection.tsx:65-123`, `SociodemographicChartsSection.tsx:64-147`, `TrendChartsRow.tsx:47,88`, `DistribucionEdad*.tsx`, `DashboardLoadingState.tsx:5`, `DashboardErrorState.tsx:7`, `Login.tsx:138-152` (`infoMsg` azul inline vs `.error-msg` rojo en CSS), `App.tsx:30` (fallback "Cargando VidaMaterna...").

**Por qué está mal:**
- Los inline repiten hex ya definidos (`#64748b`, `#0f172a`, `#0f766e`) → tercera fuente de verdad junto a CSS y `reportExporter.ts`.
- No responden a `@media` ni a `prefers-reduced-motion`.
- `ExportReportModal.tsx` entero inline es en la práctica un archivo CSS sin archivo: imposible auditar consistencia.

**Fix sugerido:** extraer `ExportReportModal.css`, `ChartState.css` (vacíos/centrados/error de gráficas), y mover `infoMsg` a clase `.info-msg` en `LoginForm.css`.

---

## Crítica 6 — Responsive fragmentado y hacks de layout (MEDIO)

**Dónde:** breakpoints en `900px` (login), `768px` (shell/sidebar/history), `1024px` (strategic/filters), `1200px`, `600px`, `560px`.

Puntos concretos:
1. `DashboardShell.css:70-74` — `.content-area-okd { padding: 72px 12px 24px }` en móvil solo para dejar hueco al botón flotante `.mobile-topbar-menu-btn` (`Sidebar.css:223-240`, `position: fixed`). Si cambia el tamaño del botón, se desincroniza.
2. Triple altura: `index.css:33-36` (`#root { height:100% }`) + `DashboardShell.css:7-12` (`.dashboard-okd-container { height:100vh }`) + `body { height:100% }`. En móvil `100vh` incluye la barra de URL → doble scroll / salto al hacer scroll. Usar `min-height: 100dvh`.
3. `.sidebar-okd` drawer (`Sidebar.css:251-260`, `translateX(-100%)`, z-index `999/1001/1002`) vs `.filters-sidebar-okd` (`FiltersSidebar.css:19-21`, `position: sticky; top:24px; z-index:10`). Dos modelos de stacking distintos; el overlay (`999`) queda debajo del botón (`1001`) por diseño pero es frágil.
4. Grids KPI correctos en intención (4→2→1 en `StrategicDashboard.css:942-953,1473-1475`) pero `.morb-falla-item { grid-template-columns: 160px 1fr 80px }` (`StrategicDashboard.css:681`) solo baja a `120px` en móvil: nombres largos dependen de `ellipsis` para no romper.

**Fix sugerido:** definir 3 breakpoints canónicos (`--bp-sm:600px, --bp-md:900px, --bp-lg:1200px`), documentarlos, y reemplazar `100vh` por `100dvh` con fallback.

---

## Crítica 7 — Código muerto, imports y detalles de impresión (BAJO)

1. `LoginLayout.css:99-101` oculta `.brand-desc, .brand-tags`, pero `Login.tsx:90-95` ya no los renderiza (solo quedan en `LoginDecorations.css:173-199`). CSS huérfano.
2. `Register.tsx:64` usa `<div className="background-decorations">` que **no existe** en ningún CSS (Register reutiliza `Login.css` pero con estructura distinta a Login: sin `.node`/`.pulse-line`). Envoltorio inútil.
3. `Login.css:6-8` importa 3 hojas vía `@import`. Funciona con Vite, pero el orden de cascada depende del resolvedor; más predecible importar las 3 desde `Login.tsx`/`Register.tsx` (o un solo `Login.bundle.css`).
4. `StrategicDashboard.css:1159-1163` redefine `.dash-control-title h1` para anular el gradiente de `StrategicDashboard.css:30-38` (guerra de especificidad dentro del mismo archivo, sección "Opción 3"). Señal de que el archivo (1507 líneas) debe partirse.
5. `StrategicDashboard.css:1490-1506` — `@media print { body * { visibility: hidden } ... }` combinado con la Crítica 1: si el contenedor estratégico no está montado se imprime en blanco; además no restaura `overflow`.
6. `StrategicDashboard.css:1104-1111` duplica la misma regla `.atencion-main-row { grid-template-columns: 1fr }` en `1200px` y `1024px`.

---

## Resumen de prioridad

| # | Problema | Severidad | Esfuerzo |
|---|----------|-----------|----------|
| 1 | `overflow:hidden` global | Crítico | 5 min |
| 2 | Dos paletas sin tokens | Alto | 1-2 h |
| 3 | Clases genéricas / colisiones | Alto | 2-4 h |
| 4 | Nesting sin preprocesador | Medio-Alto | 1 h |
| 5 | 86 inline styles | Medio | 2-3 h |
| 6 | Responsive fragmentado + 100vh | Medio | 1-2 h |
| 7 | Código muerto / print / imports | Bajo | 30 min |

## Siguiente paso propuesto

1. Quitar `overflow:hidden` de `html,body` (Crítica 1).
2. Centralizar variables en `index.css` (Crítica 2).
3. Renombrar clases de login con prefijo + consolidar spinner (Crítica 3).
