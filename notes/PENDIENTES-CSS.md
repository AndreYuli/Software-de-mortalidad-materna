# Pendientes CSS — qué falta por corregir

Fecha: 2026-09-17
Base: working copy sin commitear (15 archivos `M`, `AUDITORIA-CSS.md` y `ChartState.css` como `??`).
Verificación: `npm run build` OK, 65 tests unitarios OK. Fallos e2e pre-existentes (vitest recoge `e2e/*.spec.ts` de Playwright, no causado por estos cambios).

---

## 1. Typo en loading (1 min)

**Archivo:** `FRONTED/maternanalytics/src/components/dashboard/DashboardLoadingState.tsx:7`

```tsx
<p>Generando panel estratgico...</p>
```

**Corregir a:**

```tsx
<p>Generando panel estratégico...</p>
```

---

## 2. Nesting SCSS restante en CSS plano (15 min)

Quedan 4 anidados. O aplanar o declarar preprocesador.

- `FRONTED/maternanalytics/src/components/LoginForm.css:140` — `&:hover` dentro de `.login-remember input[type=checkbox]` / bloque anidado `&:focus-visible`, `&:checked`, `&::after`.
- `FRONTED/maternanalytics/src/components/LoginForm.css:169` — `&:hover`, `&:focus-visible` dentro de `.login-forgot`.
- `FRONTED/maternanalytics/src/components/LoginForm.css:225` — `&:focus-visible`, `&:hover` (`&::after`), `&:active`, `&::after` dentro de `.login-btn-login`.
- `FRONTED/maternanalytics/src/components/LoginDecorations.css:219` — `span {` dentro de `.login-brand-title`.

**Ejemplo de aplanado:**

```css
/* antes */
.login-brand-title {
  ...
  span { color: var(--blue-300); }
}
/* después */
.login-brand-title span { color: var(--blue-300); }
```

---

## 3. `100vh` → `100dvh` (10 min, Crítica 6 pendiente)

Sigue `100vh` en 4 lugares. En móvil causa salto/doble scroll por la barra de URL.

- `FRONTED/maternanalytics/src/components/LoginLayout.css:15` — `.login-page { height: 100vh; }`
- `FRONTED/maternanalytics/src/components/dashboard/DashboardShell.css:9` — `.dashboard-okd-container { height: 100vh; }`
- `FRONTED/maternanalytics/src/components/dashboard/Sidebar.css:255` — `.sidebar-okd { height: 100vh; }` (drawer móvil)
- `FRONTED/maternanalytics/src/components/dashboard/StrategicDashboard.css:436` — `.welcome-dashboard-shell { min-height: calc(100vh - 180px); }`

**Corregir a (con fallback):**

```css
height: 100vh;
height: 100dvh;
```

```css
min-height: calc(100vh - 180px);
min-height: calc(100dvh - 180px);
```

---

## 4. Newlines y formato (5 min)

- `FRONTED/maternanalytics/src/components/dashboard/DashboardLoadingState.tsx` — sin newline al final.
- `FRONTED/maternanalytics/src/components/dashboard/DashboardErrorState.tsx` — sin newline al final.
- `FRONTED/maternanalytics/src/components/dashboard/ChartState.css:1` — línea vacía inicial, quitar.

---

## 5. Archivos `.map` no deben commitearse (5 min)

Untracked y generados por compilador Sass:

- `FRONTED/maternanalytics/src/components/LoginDecorations.css.map`
- `FRONTED/maternanalytics/src/components/LoginForm.css.map`

**Acción:** borrarlos y agregar `*.css.map` al `.gitignore` del frontend (`FRONTED/maternanalytics/.gitignore`).

---

## 6. Detalle visual: se perdió el `❌` (2 min)

**Archivo:** `FRONTED/maternanalytics/src/components/dashboard/DashboardErrorState.tsx:6`

Antes: `<p>❌ {message}</p>`. Ahora: `<p> {message}</p>` (con espacio inicial sobrante).

**Corregir a:**

```tsx
<p>❌ {message}</p>
```

---

## 7. Pendiente mayor: 66 `style={{...}}` restantes (2-3 h, Crítica 5)

Ya migrados: `DashboardLoadingState`, `DashboardErrorState`, `login-info-msg`.
Faltan (grep `style={{` en `src/**/*.tsx`):

- `src/components/dashboard/ExportReportModal.tsx` (~20 bloques: `:48,65,77,79,82,88,108,122,126,130,134,140,143,161,163-168,176,194,196-201,209,227,229-234,242,245,261`)
- `src/components/dashboard/CruceVariablesSection.tsx:65,69,70,90,111,113,116,123`
- `src/components/dashboard/SociodemographicChartsSection.tsx:64,66,76,79,136,138,147`
- `src/components/dashboard/DistribucionEdadRiesgo.tsx:26,28,36,39`
- `src/components/dashboard/DistribucionEdadGestacional.tsx:26,28,36,39`
- `src/components/dashboard/TrendChartsRow.tsx:47,88`
- `src/components/dashboard/KpiRow.tsx:62,72` (solo tamaños de icono, baja prioridad)
- `src/components/dashboard/WelcomeState.tsx:15,31,38` (solo tamaños de icono, baja prioridad)
- `src/components/dashboard/UploadCard.tsx:63,122`
- `src/App.tsx:30` (fallback de Suspense)

Los hex `#0f172a`, `#64748b`, `#0f766e` en esos inline deberían usar `var(--brand-*)` vía clases.

---

## 8. Cierre git sugerido

```bash
git add FRONTED/maternanalytics/src/index.css \
  FRONTED/maternanalytics/src/components/LoginLayout.css \
  FRONTED/maternanalytics/src/components/LoginForm.css \
  FRONTED/maternanalytics/src/components/LoginDecorations.css \
  FRONTED/maternanalytics/src/components/Login.tsx \
  FRONTED/maternanalytics/src/components/Register.tsx \
  FRONTED/maternanalytics/src/components/dashboard/DashboardShell.css \
  FRONTED/maternanalytics/src/components/dashboard/Sidebar.css \
  FRONTED/maternanalytics/src/components/dashboard/FilterPanel.css \
  FRONTED/maternanalytics/src/components/dashboard/FiltersSidebar.css \
  FRONTED/maternanalytics/src/components/dashboard/StrategicDashboard.css \
  FRONTED/maternanalytics/src/components/dashboard/UploadHistorySection.css \
  FRONTED/maternanalytics/src/components/dashboard/UploadSection.css \
  FRONTED/maternanalytics/src/components/dashboard/DashboardLoadingState.tsx \
  FRONTED/maternanalytics/src/components/dashboard/DashboardErrorState.tsx \
  FRONTED/maternanalytics/src/components/dashboard/ChartState.css \
  AUDITORIA-CSS.md
git commit -m "fix(css): scope login, tokens brand, consolida spinner"
```

No incluir: `*.css.map`, `.dockerignore`, `Dockerfile`s, `docker-compose.yml`, `env.example` (mezclan otro cambio, commitear aparte).
