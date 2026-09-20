# Changelog

Formato: fecha · agente · qué cambió y por qué. Lo más reciente arriba. Los commits anteriores a esta fecha están en `git log`.

## 2026-09-20 · Claude Code (seguridad y reorganización)
- TAREA 1 (seguridad de la API): `analisis` y `sivigila` exigen JWT; `/media` deja de servirse; el frontend envía `Authorization: Bearer` y, ante 401, borra la sesión y redirige a `/login`; `ProtectedRoute` exige `token`.
- Reorganización (DEC-003, DEC-004): carpetas en minúscula, `data/`, `notes/`, `scripts/`, `docs/historico/`, `components/auth/`, `.dockerignore` por contexto de build, un solo `vitest.config.ts`, comillas simples en Python.
- README reescrito según la estructura real.
- TAREAS 3 y 5: `DashboardOKD` es layout con `<Outlet/>` y una sola `ProtectedRoute`; tras subir un archivo se navega a `/dashboard`; se elimina el estado de vista muerto (`useActiveView`); segmento y pestañas suben al layout para no perderse al cambiar de ruta. Tests de rutas en `App.test.tsx`.
- TAREA 4: `NarrativasResumen` muestra el resumen ejecutivo IA (uno por evento del segmento) bajo los KPIs; es opcional (botón «Generar resumen IA»), sigue el estilo sobrio `chart-ai-insight` y desaparece si `ia-service` no está disponible. `NarrativaIA` ahora captura errores de red (antes quedaba en «Generando…»).
- TASK-002 / TASK-023: las gráficas sociodemográficas pasan a rejilla de 2 columnas (CSS grid con *container query* a 640 px de ancho de la sección; 1 columna en móvil y, si queda una sola gráfica en la última fila, ocupa todo el ancho). Se decide por el ancho de la sección y no por el del viewport porque con la barra lateral y los filtros el contenido mide ~690 px a 1280 px. Verificado a 1440/1280/768/375 px.
- TASK-003 (DEC-002): el gráfico de cruce nombra las variables seleccionadas en el título, el eje X («Número de casos por …»), el eje Y y la leyenda, y se actualizan al cambiarlas (`utils/cruceLabels.ts`). Las gráficas sociodemográficas fijas conservan su etiqueta «Casos» (no son dinámicas).
- e2e: `e2e/helpers/auth.ts` usa una sesión real (los tokens falsos dan 401 desde la TAREA 1); nuevos e2e de token inválido y de navegación tras carga (POST mockeado).
- TAREA 2: la letalidad se calcula como muertes ÷ (mortalidad + morbilidad) × 100, con guardas ante denominador 0 y solo con ambos eventos en el análisis; etiquetas unificadas a "Tasa de Letalidad". **Pendiente:** `PRODUCT.md` exige que el equipo confirme esta definición (epidemiológicamente es un índice de mortalidad sobre casos de MME + muertes).

## 2026-09-19 · Claude Code (arquitectura/UX)
- Creados `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/RULES.md` y este archivo (no existían).
- `docs/TASKS.md`: corregida la TAREA 1 (la instrucción `db: Session = Depends(get_current_user)` era incorrecta; se usa `dependencies=[Depends(get_current_user)]` a nivel de router). Añadidas TAREAS 5–7 (rutas anidadas, historial con búsqueda/acciones, rejilla de gráficos).
- Sin cambios de código.

## 2026-09-18 · Auditorías (ver `notes/AUDITORIA-01-GENERAL.md`, `notes/AUDITORIA-02-ESTADOS-Y-FUNCIONALIDADES.md`)
- Corregidos H-05, H-06, H-08, H-09, H-16 (parcial) en frontend; `vitest` excluye `e2e/`.

## 2026-09-17 · `notes/AUDITORIA-CSS.md` / `notes/PENDIENTES-CSS.md`
- Refactor de CSS: login con scope, tokens de marca, spinner unificado.
