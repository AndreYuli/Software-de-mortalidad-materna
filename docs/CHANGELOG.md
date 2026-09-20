# Changelog

Formato: fecha · agente · qué cambió y por qué. Lo más reciente arriba. Los commits anteriores a esta fecha están en `git log`.

## 2026-09-20 · Claude Code (seguridad y reorganización)
- TAREA 1 (seguridad de la API): `analisis` y `sivigila` exigen JWT; `/media` deja de servirse; el frontend envía `Authorization: Bearer` y, ante 401, borra la sesión y redirige a `/login`; `ProtectedRoute` exige `token`.
- Reorganización (DEC-003, DEC-004): carpetas en minúscula, `data/`, `notes/`, `scripts/`, `docs/historico/`, `components/auth/`, `.dockerignore` por contexto de build, un solo `vitest.config.ts`, comillas simples en Python.
- README reescrito según la estructura real.
- TAREA 2: la letalidad se calcula como muertes ÷ (mortalidad + morbilidad) × 100, con guardas ante denominador 0 y solo con ambos eventos en el análisis; etiquetas unificadas a "Tasa de Letalidad". **Pendiente:** `PRODUCT.md` exige que el equipo confirme esta definición (epidemiológicamente es un índice de mortalidad sobre casos de MME + muertes).

## 2026-09-19 · Claude Code (arquitectura/UX)
- Creados `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/RULES.md` y este archivo (no existían).
- `docs/TASKS.md`: corregida la TAREA 1 (la instrucción `db: Session = Depends(get_current_user)` era incorrecta; se usa `dependencies=[Depends(get_current_user)]` a nivel de router). Añadidas TAREAS 5–7 (rutas anidadas, historial con búsqueda/acciones, rejilla de gráficos).
- Sin cambios de código.

## 2026-09-18 · Auditorías (ver `notes/AUDITORIA-01-GENERAL.md`, `notes/AUDITORIA-02-ESTADOS-Y-FUNCIONALIDADES.md`)
- Corregidos H-05, H-06, H-08, H-09, H-16 (parcial) en frontend; `vitest` excluye `e2e/`.

## 2026-09-17 · `notes/AUDITORIA-CSS.md` / `notes/PENDIENTES-CSS.md`
- Refactor de CSS: login con scope, tokens de marca, spinner unificado.
