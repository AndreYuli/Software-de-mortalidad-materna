# Auditoría 01 — Revisión general del proyecto

Fecha: 2026-09-18 · Alcance: BACKEND (FastAPI), FRONTED/maternanalytics (React + Vite + TS), IA-SERVICE, Docker.

## Método y límites (leer primero)

- **Ejecutado:** `tsc -b`, `eslint`, `vitest`, `pytest` (backend e IA-SERVICE).
- **Leído a mano:** `main.py`, config, seguridad, routers, servicio de subida, persistencia, `App.tsx`, `api.ts`, Login/Register, todos los hooks, Sidebar, AnalysisHome, Upload*, Historial, Filtros, ExportModal, `index.html`, `docker-compose.yml`.
- **NO hecho en esta iteración:** no arranqué la app en un navegador (requiere Postgres + backend), así que **no hay verificación visual real** (responsive, contraste, overflow, gráficas ECharts). Tampoco leí a fondo `StrategicDashboard.css` (1508 líneas), los procesadores de mortalidad/morbilidad, `reportExporter`, ni `IA-SERVICE/prompts`. Todo lo visual de abajo sale del código, no de capturas.

## Resultado de las verificaciones automáticas

| Herramienta | Antes | Después |
|---|---|---|
| `tsc -b` | limpio | limpio |
| `pytest` backend | 49 OK | (sin cambios de backend) |
| `pytest` IA-SERVICE | 18 OK | (sin cambios) |
| `vitest` | 3 archivos FALLAN (los specs `e2e/` de Playwright los recogía Vitest) + 65 tests OK | 17 archivos / 65 tests OK |
| `eslint` | 8 errores + 1 warning | igual (no tocado, ver H-12) |

---

## Hallazgos

Severidad: **CRÍTICO** / **ALTO** / **MEDIO** / **BAJO**. Estado: ✅ corregido · ⏳ pendiente (decisión tuya).

### Seguridad / autenticación

**H-01 · CRÍTICO ⏳ — La API no exige autenticación en ningún endpoint de datos.**
`get_current_user` existe en `BACKEND/api/dependencies.py` pero no lo usa ningún router. Cualquiera con la URL puede `GET /api/sivigila/pacientes/` (nombres e identificación de pacientes), `POST /api/analisis/` (subir archivos), leer análisis, etc. Además `/media` (Excel con datos de pacientes) se sirve como estático público. El login solo "decora" el frontend.
→ Propuesta: `dependencies=[Depends(get_current_user)]` en los 3 routers de datos, enviar `Authorization: Bearer` desde el frontend (un helper `apiFetch` central), y servir `/media` con endpoint autenticado o no montarlo.

**H-02 · ALTO ⏳ — El frontend nunca envía el token ni maneja 401/expiración.**
`api.ts` y los hooks usan `fetch` sin `Authorization`. El JWT dura 60 min pero `ProtectedRoute` solo mira si existe `token` **o** `username` en localStorage (basta con escribir `username` a mano para entrar). No hay redirección a login cuando el token expira. Va de la mano con H-01.

**H-03 · MEDIO ⏳ — Configuración por defecto insegura.** `jwt_secret='cambia-esto-en-produccion'` y `db_password='password'` como defaults: si falta la variable, arranca igual sin avisar. Sugerencia: fallar al arrancar si `JWT_SECRET` es el default fuera de desarrollo.

**H-04 · MEDIO ⏳ — Registro abierto.** `/api/auth/register/` permite que cualquiera cree cuenta; al proteger la API decidir si el registro debe estar restringido (es una plataforma de datos clínicos).

### Errores funcionales

**H-05 · ALTO ✅ — Los errores del backend al subir un archivo nunca se mostraban.**
`useFileUpload.ts` leía `err.error` / `err.columnas_faltantes`, pero FastAPI responde `{ "detail": "..." }`. Resultado: siempre "Error al procesar el archivo." aunque el backend dijera "Faltan columnas requeridas: …".
Corrección: ahora lee `detail` (string) con fallback seguro si el cuerpo no es JSON.

**H-06 · ALTO ✅ — Hora de la carga desfasada en el Historial.**
`Analisis.fecha_carga` es `DateTime` sin zona (guardado en UTC) y `isoformat()` no añade `Z`; el navegador lo interpreta como hora local (Colombia UTC-5 ⇒ 5 h de error). Además el `try/catch` de `formatFecha` nunca actuaba (`new Date()` no lanza, devolvía "Invalid Date").
Corrección: en `UploadHistorySection.tsx` se añade `Z` si falta zona y se devuelve el texto original si la fecha es inválida. (Ideal a futuro: columna `DateTime(timezone=True)` o serializar con `Z` en backend.)

**H-07 · ALTO ⏳ — Tras subir un archivo no se navega al dashboard (código muerto).**
`handleUploadSuccess` (en `useDashboardData`) llama `setActiveView('analisis')`, pero la vista activa ahora se deriva de la URL en `DashboardOKD`, por lo que ese estado ya no hace nada. Consecuencia: el usuario se queda en la pantalla de carga con el botón deshabilitado y el `setTimeout` de 1500 ms no tiene efecto visible. Además `selectedAnalisisId`/`analysisType` se calculan pero ya no llegan a ninguna vista.
→ Decisión tuya: ¿redirigir a `/dashboard` tras el éxito (`navigate` en `DashboardOKD`) y limpiar el estado muerto?

**H-08 · MEDIO ✅ — Formatos aceptados que el backend no puede leer.**
El input aceptaba `.xlsx,.xls,.csv`, pero el backend lee con `openpyxl` (solo `.xlsx`). Un `.xls`/`.csv` pasaba la validación del navegador y fallaba en el servidor con un mensaje confuso. Corregido: `accept=".xlsx"` y texto de ayuda coherente. (El backend tampoco valida extensión ni tamaño: el límite de 15 MB es solo del cliente → H-15.)

**H-09 · MEDIO ✅ — Mensaje de éxito apuntaba a una sección inexistente.**
Decía «Análisis guardados»; en el menú se llama «Dashboard Analítico» / «Historial de Cargas». Corregido.

**H-10 · MEDIO ⏳ — Cada cambio de filtro reemplaza todo el dashboard por la pantalla de carga.**
En `AnalysisHomeSection`, `if (loading) return <DashboardLoadingState/>` desmonta también `FiltersSidebar`: parpadeo, pérdida de foco y de scroll cada vez que se toca un `<select>`. Mejor mantener layout + filtros y mostrar la carga solo sobre el contenido. Mismo patrón en Historial al cambiar de página.

**H-11 · MEDIO ⏳ — `fetchAnalisis` (dashboard) devuelve `null` en silencio si la respuesta no es OK.**
Un 404/500 de `/completo/` produce un dashboard vacío sin mensaje de error (el estado `error` solo se activa por excepciones de red). Debería lanzar y mostrar `DashboardErrorState`.

**H-12 · MEDIO ⏳ — 8 errores de ESLint (reglas de React 19 hooks / `any`).**
`react-hooks/set-state-in-effect` en `useAnalysisList`, `useCruceVariables`, `useUploadHistory`; `no-explicit-any` ×5 en `useDashboardCharts.ts` (líneas 113, 163, 168, 180, 184). No rompen la app pero `lint` está en rojo. Además `useAnalysisList.fetchAnalisis` depende de `selectedAnalisisId`, por lo que se vuelve a llamar (doble fetch) al auto-seleccionar.

**H-13 · BAJO ⏳ — Filtros semana/mes/día combinables de forma incoherente.** Se puede elegir semana y mes a la vez; no hay indicación de cuál prevalece. Semanas ISO 1–53 siempre listadas (la 53 casi nunca existe). Día: siempre 1–31 aunque el mes tenga 28/30.

**H-14 · BAJO ⏳ — Archivos en disco pueden sobrescribirse.** `_guardar_df_como_excel` guarda en `media/uploads/AAAA/MM/<nombre>`: dos cargas con el mismo nombre en el mismo mes se sobrescriben en disco mientras el historial conserva dos filas apuntando al mismo archivo. Además lo guardado es el dataset acumulado y limpio, no el original subido. Sugerencia: prefijar con hash/timestamp.

**H-15 · BAJO ⏳ — El backend acepta cualquier `tipo`, tamaño y extensión;** con un `tipo` inválido el error real (KeyError) se enmascara como "No se pudo leer el archivo Excel". Validar `tipo in {'mortalidad','morbilidad'}` y tamaño en el router.

### UX / accesibilidad / consistencia visual (desde código)

**H-16 · MEDIO ✅ parcial — Modal «Exportar reporte» sin accesibilidad.**
No cerraba con Escape, sin `role="dialog"`/`aria-modal`, botón ✕ sin nombre accesible. Añadidos: Escape, `role="dialog"`, `aria-modal`, `aria-label`, `type="button"` y `aria-label="Cerrar"` en la ✕. **Pendiente:** atrapar/devolver el foco; el modal está 100 % con estilos inline y hex fuera de los tokens (`#64748b`, `#10b981`…), inconsistente con el resto.

**H-17 · MEDIO ⏳ — Login/Register.**
- «Recordarme» es un checkbox decorativo (no hace nada).
- `required` nativo + validación Zod: el navegador bloquea el envío antes de que aparezcan los mensajes de Zod (duplicado).
- Sin `autoComplete` (`email`, `current-password`, `new-password`).
- Sin botón mostrar/ocultar contraseña.
- Token en `localStorage` (expuesto a XSS); aceptable solo tras H-01/H-02.
- Existen dos `LogoIcon` (`components/LogoIcon.tsx` y `components/icons/LogoIcon.tsx`) y 4 CSS de login; verificar duplicación.

**H-18 · MEDIO ⏳ — Pestañas del dashboard sin semántica.** Los `tab-button` no tienen `type="button"`, `role="tab"`, `aria-selected`. Navegación por teclado/lectores degradada.

**H-19 · BAJO ⏳ — `alert()` nativo** en `UploadCard` para archivos > 15 MB (rompe el patrón de mensajes en línea del resto de la pantalla).

**H-20 · BAJO ⏳ — Tipografía.** `index.html` carga *Plus Jakarta Sans* pesos 300–600, pero hay 41 reglas CSS con `font-weight: 700/800` (y el modal usa 800): el navegador sintetiza negritas. Cargar 700/800 o unificar a 600.

**H-21 · BAJO ⏳ — Código/estilos sin uso o mejorables.**
`DashControlBar.tsx` no se importa en ningún sitio; `FilterPanel.css` posiblemente idem; `App.tsx` tiene 5 rutas idénticas a `DashboardOKD` (mejor una ruta con layout anidado: hoy el Dashboard se remonta al navegar entre carga/historial y pierde `segmento`/pestañas); `!important` en `StrategicDashboard.css` (6) y `LoginLayout.css` (2). En el árbol de trabajo hay artefactos generados (`dist`, `playwright-report`, `test-results`, `*.tsbuildinfo`, `test.xlsx`, `archivo_prueba_magico.xlsx` en la raíz): comprobar que estén ignorados.

**H-22 · BAJO ⏳ — Config de tests duplicada.** `vitest.config.ts`, `.js` y `.d.ts` están versionados (Vitest usa el `.ts`); los otros dos son ruido.

**H-23 · BAJO ⏳ — Docker.** `backend` e `ia-service` sin `healthcheck`; `backend` usa `service_started` para `ia-service`. El frontend no está dockerizado (no hay servicio que lo sirva) aunque `env.example` habla de "dominio donde sirves el frontend".

---

## Cambios realizados en esta iteración

| Archivo | Cambio | Hallazgo |
|---|---|---|
| `src/hooks/files/useFileUpload.ts` | Lee `detail` de FastAPI para mostrar el error real | H-05 |
| `src/components/dashboard/UploadHistorySection.tsx` | `formatFecha` interpreta UTC y tolera fechas inválidas | H-06 |
| `src/components/dashboard/UploadCard.tsx` | `accept=".xlsx"` + texto de ayuda | H-08 |
| `src/components/dashboard/UploadSection.tsx` | Texto del mensaje de éxito | H-09 |
| `src/components/dashboard/ExportReportModal.tsx` | Escape, `role="dialog"`, `aria-modal`, nombre accesible de la ✕ | H-16 |
| `src/hooks/analysis/useAnalysisList.ts` | Eliminados 2 `console.log` de depuración | — |
| `vitest.config.ts` | Excluye `e2e/**` (los ejecuta Playwright) → `vitest run` en verde | — |

Verificado tras los cambios: `tsc -b` limpio, `vitest run` 17/17 archivos y 65/65 tests. **No hice commits.** Nota: `UploadCard.tsx` aparece con diff completo en `git diff` por cómo git clasifica ese archivo (CRLF); el cambio real son 2 líneas (`git diff --ignore-space-at-eol`).

## Prioridad sugerida para la siguiente iteración

1. H-01 + H-02 (autenticación real extremo a extremo): es lo único que considero bloqueante antes de exponer el sistema.
2. H-07 (flujo post-subida) y H-10 (parpadeo al filtrar): lo que más notará una usuaria.
3. Auditoría visual real con la app levantada (capturas a 3 anchos) y lectura completa de `StrategicDashboard.css`, `reportExporter` y procesadores.
