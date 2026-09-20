# Auditoría 02 — Estados y comportamiento de cada funcionalidad

Fecha: 2026-09-18 · Continúa `AUDITORIA-01-GENERAL.md` (los IDs H-xx vienen de ahí; aquí usamos F-xx).

## Método y límites

Para cada pantalla se revisó en el código: estado inicial, carga, éxito, vacío, error, validaciones, mensajes, botones, navegación, clics repetidos, peticiones lentas, peticiones que fallan y ausencia de datos.
**Sigue sin haber verificación en navegador**: todo lo que sigue sale de leer el código y de las pruebas automáticas, no de haber usado la app levantada. Los comportamientos de "clic repetido" y "petición lenta" se razonaron sobre el código (y el timeout se probó con un test unitario), no se reprodujeron en vivo.

---

## Matriz por pantalla

Leyenda: ✅ correcto · 🔧 corregido en esta iteración · ⚠️ pendiente · — no aplica

### Login (`/login`)
| Aspecto | Antes | Ahora |
|---|---|---|
| Inicial / validación | ✅ Zod + `required` nativo (duplicado, ver H-17) | igual |
| Carga | ✅ botón deshabilitado "Verificando…" | igual |
| Error de credenciales | ✅ muestra `detail` | ✅ |
| Respuesta no-JSON (proxy caído, 502) | ❌ `res.json()` lanzaba → mensaje "No se pudo conectar" (engañoso) | 🔧 "El servidor no respondió correctamente…" |
| Error 422 (`detail` es lista) | ❌ `setError(array)` → React lanza "Objects are not valid as a React child" → **pantalla en blanco** | 🔧 se extrae el primer `msg` |
| Petición lenta | ❌ sin límite: botón en "Verificando…" indefinidamente | 🔧 timeout 30 s con mensaje propio |
| Clics repetidos | ✅ botón deshabilitado durante la carga | igual |
| «Recordarme», «¿Olvidaste?» | ⚠️ el primero no hace nada; el segundo solo informa (honesto) | igual |

### Registro (`/register`)
Mismos problemas y correcciones que Login (422 con lista → pantalla en blanco; timeout; no-JSON). Éxito: ✅ mensaje y redirección a los 1,5 s. ⚠️ El `setTimeout` de la redirección no se cancela si el usuario pulsa «Iniciar sesión» antes (navega dos veces; inofensivo).

### Rutas / navegación (`App.tsx`, `DashboardOKD`)
- ✅ Ruta desconocida → `/`; rutas públicas redirigen a `/dashboard` si hay sesión; el botón "atrás" funciona porque la vista se deriva de la URL; menú móvil se cierra al navegar.
- 🔧 **Sin `ErrorBoundary`**: cualquier excepción de render dejaba la pantalla en blanco. Añadido `components/ErrorBoundary.tsx` (mensaje + "Volver al inicio").
- ⚠️ No hay 401/expiración de sesión (H-02): con el token vencido la app sigue "logueada" y todo falla.

### Dashboard Analítico (`AnalysisHomeSection`)
| Aspecto | Antes | Ahora |
|---|---|---|
| **Estado inicial (cargando la lista)** | ❌ mientras `GET /analisis/` no respondía se mostraba **"Aún no hay datos para analizar"** (parpadeo en cada primera visita) | 🔧 muestra "Generando panel…" |
| **Backend caído al abrir** | ❌ el error se tragaba (`console.error`) y se veía la pantalla de bienvenida, como si la BD estuviera vacía | 🔧 estado de error con mensaje y botón **Reintentar** (vuelve a pedir la lista, sin recargar la página) |
| Vacío (sin cargas) | ✅ `WelcomeState` con CTA hacia carga | igual |
| Carga al filtrar | ⚠️ reemplaza todo el panel + filtros por un spinner (H-10) | igual |
| Error del `/completo/` (404/500) | ❌ `fetchAnalisis` devolvía `null` sin avisar → panel en ceros, sin mensaje | 🔧 lanza y se muestra `DashboardErrorState` |
| Petición lenta | ❌ sin límite | 🔧 90 s, con mensaje específico |
| Cambio rápido de filtros | ✅ `AbortController` cancela la anterior | ✅ (ahora combinado con el timeout) |
| Sin datos para el filtro elegido | ✅ las gráficas de causas/sociodemográficas muestran mensaje vacío | igual |
| Pestañas Morbilidad/Mortalidad con un solo tipo cargado | ✅ el cruce muestra "No hay suficientes datos…" | igual |
| Botón "Reintentar" del error | ❌ recargaba toda la página (perdía filtros) | 🔧 acepta `onRetry` (recarga solo si no se pasa) |

### Filtros (`FiltersSidebar` + `useDashboardFilters`)
- 🔧 **Filtro "fantasma"**: al volver a «Todos los años», mes/semana/día quedaban aplicados. El `<select>` de mes queda deshabilitado (y mostrando el mes viejo) pero el backend seguía filtrando por mes en todos los años, sin forma de verlo ni quitarlo salvo el botón "Limpiar". Ahora vaciar el año limpia mes/semana/día, y vaciar el mes limpia el día.
- ⚠️ Semana y mes se pueden combinar (H-13).

### KPIs (`KpiRow`, `TrendBadge`, `useDashboardMetrics`)
- 🔧 **Los comparativos ("+x % vs ant.") nunca funcionaban con filtros.** El backend calculaba `distribucion_mensual` *después* de filtrar por año/mes, así que el periodo anterior llegaba siempre vacío (`prev = 0`) y se mostraba "Estable". Ahora se calcula **antes** de filtrar (`_analisis_calculo.py`). El gráfico de evolución mensual (usado en el export) ya seleccionaba el año por su cuenta, así que no se ve afectado. 49/49 tests de backend pasan; **no hay un test nuevo que cubra este caso** (pendiente).
- 🔧 `0 → N casos` se etiquetaba "Estable"; ahora "Sin base previa".
- 🔧 El texto decía siempre "variación contra el mes anterior" aunque solo se filtre por año (compara con el año previo); corregido.
- ⚠️ **Decisión de dominio (tuya/epidemiología):** la "Tasa de letalidad" se calcula como `mortalidad(550) / morbilidad(549) × 100`, es decir, una *razón* mortalidad/morbilidad extrema, no una letalidad (muertes / casos). El modal de exportar la llama "Razón". Conviene decidir el nombre correcto y el umbral de "≥ 50 % atípico"; además con el segmento "solo mortalidad" el denominador es 0 y muestra "0 %".

### Carga de archivos (`UploadSection` / `UploadCard` / `useFileUpload`)
| Aspecto | Antes | Ahora |
|---|---|---|
| Inicial / drag-over / éxito / error de columnas | ✅ bien resueltos (zona, tarjeta, vista previa, lista de columnas faltantes) | igual |
| **Archivo con otra extensión arrastrado** | ❌ el `accept` no filtra el *drop*; pasaba la validación cliente y fallaba en el servidor | 🔧 se rechaza en el cliente ("No se pudo leer el archivo…") |
| **Archivo con encabezados pero 0 filas** | ❌ botón habilitado; se enviaba un análisis vacío | 🔧 botón deshabilitado + mensaje "no contiene registros" |
| Cambiar de archivo mientras se valida el anterior | ❌ el resultado de la validación vieja podía pisar al nuevo | 🔧 se descartan resultados obsoletos |
| Clic repetido en "Iniciar análisis" | ✅ deshabilitado durante `analyzing` | 🔧 además guarda dentro del handler |
| Petición lenta | ❌ sin límite | 🔧 180 s con mensaje de timeout |
| Error del servidor | ❌ siempre "Error al procesar el archivo" (H-05) | ✅ mensaje real (corregido en iter. 1, ahora también tolera lista 422) |
| Tras el éxito | ⚠️ no navega (H-07); el botón queda deshabilitado hasta quitar el archivo | igual |
| Archivo > 15 MB | ⚠️ `alert()` (H-19) | igual |
| Archivo grande en el navegador | ⚠️ `previewExcel` parsea el libro completo en el hilo principal sin indicador (posible congelamiento hasta ~15 MB) | igual |

### Historial de cargas
- Carga ✅ spinner · vacío ✅ mensaje · éxito ✅ tabla + paginación.
- 🔧 **Error**: solo mostraba el texto, sin salida. Ahora tiene `role="alert"` y botón **Reintentar** (el hook ya exponía `reload`, sin usar). 🔧 Timeout 30 s.
- ⚠️ Cambiar de página muestra spinner en lugar de la tabla (parpadeo); ⚠️ los recuentos no se formatean con separador de miles.

### Cruce de variables
- ✅ estados de carga, error, vacío y datos; cancelación de peticiones obsoletas.
- 🔧 El mensaje de error del backend con `detail` en lista se mostraba como "[object Object]"; ahora se extrae `msg`. 🔧 timeout 30 s.
- ⚠️ Un frame de "No hay suficientes datos…" antes de que arranque la carga (el estado `loading` empieza en `false`).

### Exportar reporte (`ExportReportModal`, `reportExporter`)
- 🔧 **Fallo silencioso**: si la exportación lanzaba, solo había `console.error`; el modal seguía abierto sin explicación. Ahora muestra un mensaje.
- 🔧 **Seguridad (XSS)**: el "PDF" se genera con `document.write` interpolando texto que viene del Excel (códigos/causas CIE-10, nombres de demoras, resumen IA) **sin escapar**. La ventana es `about:blank` del mismo origen: una celda maliciosa con `<img onerror=…>` podía ejecutar código con acceso al `localStorage` (token). Ahora todo lo interpolado se escapa.
- ⚠️ Excel/CSV: valores que empiezan por `=`, `+`, `-`, `@` no se neutralizan (inyección de fórmulas al abrir en Excel).
- ⚠️ Popup bloqueado usa `alert()`; se permite exportar con el panel vacío (CSV solo con encabezados).

### Narrativa IA (`NarrativaIA.tsx`)
- ⚠️ **El componente no se usa en ninguna pantalla** (solo se define y se exporta). El microservicio IA-SERVICE, el endpoint de narrativas y el cache existen pero el usuario no tiene ningún acceso desde la interfaz. Si se conecta: `generar()` no captura excepciones, así que ante un error distinto de 503 quedaría en "Generando narrativa…" para siempre. Si el servicio no está disponible el componente desaparece sin avisar. Decisión tuya: ¿se integra o se retira?

---

## Cambios realizados en esta iteración

| Archivo | Cambio |
|---|---|
| `src/api.ts` | Nuevos `fetchWithTimeout`, `extractErrorMessage`, `describeNetworkError`; timeouts en historial, cruce y narrativa |
| `src/components/Login.tsx`, `Register.tsx` | Timeout, respuesta no-JSON, `detail` en lista (evita pantalla en blanco) |
| `src/hooks/files/useFileUpload.ts` | Extensión `.xlsx`, descarta validaciones obsoletas, timeout 180 s, guarda contra doble envío |
| `src/components/dashboard/UploadSection.tsx` | Bloquea y explica archivos sin registros |
| `src/hooks/analysis/useAnalysisList.ts`, `useDashboardData.ts`, `ViewRouter.tsx`, `AnalysisHomeSection.tsx`, `DashboardErrorState.tsx` | Estados de carga/error de la lista de análisis; reintento sin recargar |
| `src/hooks/dashboard/useAnalysisHomeData.ts` | Errores HTTP ya no se ignoran; timeout 90 s |
| `src/components/dashboard/UploadHistorySection.tsx` | Botón Reintentar en error |
| `src/hooks/filters/useDashboardFilters.ts` | Limpieza en cascada de filtros dependientes |
| `src/components/dashboard/TrendBadge.tsx`, `KpiRow.tsx` | "Sin base previa"; texto del periodo de comparación |
| `src/components/dashboard/ExportReportModal.tsx`, `src/utils/reportExporter.ts` | Mensaje de error de exportación; escape de HTML |
| `src/components/ErrorBoundary.tsx`, `App.tsx` | Nuevo error boundary |
| `BACKEND/services/_analisis_calculo.py` | `distribucion_mensual` calculada antes de filtrar |
| `src/api.test.ts` | 6 tests nuevos (extracción de errores, timeout, red) |

**Verificación:** `tsc -b` limpio · `vitest` 18 archivos / 71 tests OK (antes 65) · `pytest` backend 49/49 · `eslint` sin cambios (los mismos 8 errores previos, ninguno nuevo). Sin commits.

## Pendiente / decisiones para ti

1. **H-01/H-02** (autenticación de la API + token + 401) sigue siendo lo más importante.
2. Nombre y fórmula de la "tasa de letalidad" (ver KPIs).
3. ¿Integrar o retirar `NarrativaIA`?
4. Flujo post-subida (H-07) y parpadeo al filtrar/paginar (H-10).
5. Test de backend que cubra el comparativo con filtros (no lo escribí; el cambio de `distribucion_mensual` está verificado solo por lectura de código y porque los 49 tests existentes siguen pasando).
6. Verificación real en navegador (Playwright ya está instalado en el frontend) una vez haya Postgres + backend levantados.
