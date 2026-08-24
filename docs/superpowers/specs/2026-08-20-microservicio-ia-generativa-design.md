# Microservicio de IA generativa — Spec de Diseño

**Fecha:** 2026-08-20
**Depende de:** `2026-08-20-migracion-typescript-frontend-design.md` (el frontend nuevo de esta spec se escribe directamente en TypeScript)
**Contexto:** Objetivo 3 de la tesis (`GAPS_ANALISIS.md`) — hoy no existe integración con ningún LLM. Además, `DashboardOKD.jsx:803-844` tiene una tarjeta "🤖 Inteligencia IA" con texto **hardcodeado** (mismo recomendación sin importar los datos) que esta spec reemplaza por narrativa real.

---

## Objetivo

Generar 4 tipos de narrativa en lenguaje natural a partir de los indicadores agregados que el backend ya calcula, usando un LLM local vía Ollama, corriendo como microservicio FastAPI separado del backend principal. El LLM **nunca** recibe datos crudos de pacientes — solo los diccionarios de indicadores ya agregados que produce `calcular_completo` / `ejecutar_clustering`.

## Decisiones ya tomadas (con el usuario, no abiertas a re-discusión en el plan)

- **LLM:** Ollama local, modelo `qwen2.5` (configurable por env var, no hardcodeado).
- **Arquitectura:** proceso FastAPI separado (`IA-SERVICE/`), no un router dentro del monolito — cumple el requisito de "microservicio" de la tesis sin depender de Docker todavía.
- **Alcance:** las 4 narrativas completas de una vez (resumen ejecutivo, demoras/tiempo de remisión, clustering, tendencias).
- **Trigger:** bajo demanda (botón "Generar", no automático al subir el Excel).
- **Persistencia:** se cachea en Postgres; "Regenerar" fuerza nueva llamada al LLM.
- **Manejo de fallas:** si Ollama/IA-SERVICE no responde, la tarjeta correspondiente se **oculta silenciosamente** en la UI (sin mensaje de error visible al usuario final). El backend sí lo loguea server-side para que se pueda depurar.
- **Ubicación en UI:** una narrativa por pestaña — resumen ejecutivo en el dashboard (reemplaza la tarjeta hardcodeada), demoras/tiempo de remisión y tendencias en la pestaña `overview` o `charts` de `AnalisisView` (según corresponda al indicador), clustering en la pestaña `clustering`.

---

## Arquitectura

```
FRONTEND (React+TS, :5173)
      │  GET /api/analisis/{id}/narrativa/{tipo}/?year=&month=&regenerar=
      ▼
BACKEND (FastAPI, :8000) ── Postgres (cache: tabla narrativa_ia)
      │  POST /generar-narrativa  { tipo_narrativa, indicadores }
      ▼
IA-SERVICE (FastAPI, :8001, sin BD)
      │  POST /api/generate  { model, prompt }
      ▼
Ollama (localhost:11434, modelo qwen2.5)
```

IA-SERVICE es stateless y sin acceso a BD — recibe indicadores agregados, arma un prompt con una plantilla, llama a Ollama, devuelve texto. No sabe qué es un "análisis" ni un "paciente".

---

## `IA-SERVICE/` (carpeta nueva, hermana de `BACKEND/` y `FRONTED/`)

```
IA-SERVICE/
├── main.py                 ← FastAPI app, endpoint único
├── core/
│   └── config.py            ← pydantic-settings: OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_TIMEOUT_S
├── schemas.py               ← Pydantic: NarrativaRequest, NarrativaResponse
├── ollama_client.py          ← wrapper HTTP a Ollama (httpx)
├── prompts/
│   ├── __init__.py           ← construir_prompt(tipo_narrativa, indicadores) -> str
│   ├── resumen_ejecutivo.py
│   ├── demoras.py             ← usado también para tiempo_remision de morbilidad
│   ├── clustering.py
│   └── tendencias.py
├── requirements.txt          ← fastapi, uvicorn, httpx, pydantic, pydantic-settings
└── tests/
    ├── test_prompts.py
    ├── test_ollama_client.py
    └── test_main.py
```

### `schemas.py`

```python
class NarrativaRequest(BaseModel):
    tipo_narrativa: Literal['resumen_ejecutivo', 'demoras', 'clustering', 'tendencias']
    tipo_analisis: Literal['mortalidad', 'morbilidad']
    indicadores: dict[str, Any]  # subconjunto ya agregado, nunca filas de pacientes

class NarrativaResponse(BaseModel):
    narrativa: str
    modelo: str
```

### `POST /generar-narrativa`

1. Valida `NarrativaRequest`.
2. `construir_prompt(tipo_narrativa, tipo_analisis, indicadores)` selecciona la plantilla y la rellena.
3. `ollama_client.generar(prompt)` — POST a `{OLLAMA_HOST}/api/generate` con `{model, prompt, stream: false}`, timeout configurable (default 30s).
4. Si Ollama no responde o da timeout → `HTTPException(503, 'IA no disponible')`.
5. Devuelve `NarrativaResponse`.

### Plantillas de prompt

Cada plantilla es una función `construir(indicadores: dict, tipo_analisis: str) -> str` que arma instrucciones explícitas:
- Responder en español, tono profesional para personal de salud pública.
- 150-250 palabras.
- **Nunca inventar cifras que no estén en `indicadores`** — instrucción explícita en el prompt.
- No mencionar nombres propios ni identificadores de pacientes (no los recibe de todas formas).

Mapeo tipo_narrativa → campos de indicadores usados (verificado contra `_analisis_calculo.py` y los processors):
| tipo_narrativa | Campos de entrada | Origen |
|---|---|---|
| `resumen_ejecutivo` | `estadisticas_basicas`, `causas_cie10` o `criterios_inclusion`, totales | `calcular_completo` |
| `demoras` | `demoras` (mortalidad) o `tiempo_remision` (morbilidad) | `MortalidadProcessor.analizar_demoras` / `MorbilidadProcessor.analizar_tiempo_remision` |
| `clustering` | resultado de `ejecutar_clustering` (perfiles, tamaños de cluster) | `ejecutar_clustering` |
| `tendencias` | `distribucion_mensual` | `calcular_completo` (meta) |

---

## `BACKEND/` — cambios

### Tabla nueva `narrativa_ia` (`db/models_sqlalchemy.py`)

```python
class NarrativaIA(Base):
    __tablename__ = 'narrativa_ia'
    id = Column(Integer, primary_key=True, autoincrement=True)
    analisis_id = Column(Integer, ForeignKey('api_analisis.id'), nullable=False)
    tipo_narrativa = Column(String(30), nullable=False)
    filtros_hash = Column(String(64), nullable=False)  # sha256(year|month|tipo_clustering|n_clusters)
    contenido = Column(Text, nullable=False)
    modelo = Column(String(50), nullable=False)
    generado_en = Column(DateTime, nullable=False)
    __table_args__ = (UniqueConstraint('analisis_id', 'tipo_narrativa', 'filtros_hash'),)
```

### `services/ia_client.py`

Wrapper `httpx` hacia IA-SERVICE (`IA_SERVICE_URL`, default `http://localhost:8001`, en `core/config.py`). Expone `generar_narrativa(tipo_narrativa, tipo_analisis, indicadores) -> str`, lanza `IAServiceUnavailableError` (excepción propia) en timeout/conexión rechazada/503 — el router la traduce a HTTP 503.

### `services/narrativa_service.py`

`obtener_narrativa(db, analisis, tipo_narrativa, filtros, regenerar) -> str`:
1. Calcula `filtros_hash`.
2. Si `not regenerar`: busca en `narrativa_ia`; si existe, la devuelve (sin llamar al LLM).
3. Si no existe o `regenerar=True`: recalcula los indicadores relevantes (reusa `calcular_completo` / `ejecutar_clustering` ya existentes), llama a `ia_client.generar_narrativa`, guarda/actualiza la fila (upsert por la unique constraint) y devuelve el texto.

### Router (`api/routers/analisis.py`)

```
GET /api/analisis/{pk}/narrativa/{tipo}/?year=&month=&tipo_clustering=&n_clusters=&regenerar=false
```
- 200 con `{narrativa, modelo, generado_en, desde_cache}` si todo bien.
- 503 con detail claro si `IAServiceUnavailableError` — el frontend interpreta 503 en este endpoint específico como "ocultar tarjeta", no como error genérico.
- Reusa `_get_analisis_or_404` y `_errores_servicio` ya existentes.

---

## `FRONTED/maternanalytics/` — cambios (en TypeScript, sobre la base de la spec previa)

### `src/api.ts` — nueva función

```ts
export async function obtenerNarrativa(
  analisisId: number, tipo: TipoNarrativa, filtros: FiltrosNarrativa, regenerar = false
): Promise<NarrativaResponse | null>  // null si 503 → "no disponible"
```

### `src/components/NarrativaIA.tsx` (componente nuevo, reutilizable)

Props: `{ analisisId, tipo, tipoAnalisis, filtros, titulo }`.
Estados: `idle` (botón "Generar resumen IA") → `loading` → `success` (texto + botón "Regenerar") → `unavailable` (no renderiza nada, `return null`, con un `console.debug` para depuración en dev, nunca visible al usuario — cumple "ocultar silenciosamente").

Usado en:
- `DashboardOKD.tsx`: `AnalysisHomeSection` — reemplaza la llamada a `getAIInsight()` (que se elimina) por `<NarrativaIA tipo="resumen_ejecutivo" .../>`.
- `AnalisisView.tsx`: pestaña `overview` → demoras/tiempo_remision + tendencias; pestaña `clustering` → clustering.

---

## Testing

### `IA-SERVICE/tests/`
- `test_prompts.py`: cada plantilla, con indicadores de ejemplo (incluyendo dict vacío/campos faltantes), produce un string no vacío y no lanza excepción.
- `test_ollama_client.py`: mock de `httpx.AsyncClient.post` — caso éxito, caso timeout (`httpx.TimeoutException`), caso conexión rechazada (`httpx.ConnectError`) → todos mapean a la excepción esperada.
- `test_main.py`: `TestClient`, mockeando `ollama_client.generar`, valida request inválido (422), éxito (200), fallo del cliente (503).

### `BACKEND/tests/` (carpeta nueva — hoy no existe ningún test en BACKEND)
- `test_ia_client.py`: mock de `httpx`, mismos 3 casos que arriba.
- `test_narrativa_service.py`: cache hit (no llama a `ia_client`), cache miss (sí llama y guarda), `regenerar=True` (llama aunque exista cache), `filtros_hash` distingue filtros distintos.
- `test_analisis_router_narrativa.py`: endpoint devuelve 200/503 correctamente; **assert explícito de que el payload enviado a `ia_client.generar_narrativa` no contiene columnas identificables de paciente** (nombre, documento) — es el control de la regla "solo agregados, nunca datos crudos".
- **Red de seguridad sobre código existente** (pedido explícito del usuario): `test_analisis_calculo.py`, `test_mortalidad_processor.py`, `test_morbilidad_processor.py` — tests de regresión con un DataFrame de ejemplo pequeño (fixture con 5-10 filas sintéticas cubriendo las columnas SIVIGILA relevantes) para `calcular_completo`, `analizar_demoras`, `analizar_tiempo_remision`, `ejecutar_clustering`, verificando que no truenan y que las cifras agregadas cuadran con los datos de fixture. Se agregan **antes** de tocar `narrativa_service.py`, para detectar si la integración rompe algo del cálculo existente.
- Configuración: `pytest`, `pytest-mock`, `httpx` (ya viene con FastAPI para `TestClient`) agregados a `requirements.txt`; `conftest.py` con fixture de sesión de BD de test usando **SQLite en memoria** (los modelos no usan tipos específicos de PostgreSQL como `JSONB`/`ARRAY`, así que `Base.metadata.create_all()` funciona igual contra SQLite — evita depender de una instancia de Postgres corriendo solo para tests).

### `FRONTED/maternanalytics/src/components/NarrativaIA.test.tsx`
- Estado `loading` → `success` → texto visible.
- Estado `unavailable` (mock 503) → `container` vacío, no lanza.
- Click en "Regenerar" → segunda llamada a `obtenerNarrativa` con `regenerar=true`.

## Criterio de aceptación

- Con Ollama corriendo localmente y `qwen2.5` descargado: subir un Excel, abrir el dashboard, click en "Generar resumen IA" produce una narrativa coherente con los indicadores reales (no texto fijo).
- Apagando Ollama, la tarjeta se oculta sin romper el resto del dashboard ni mostrar error al usuario.
- Todos los tests listados arriba pasan (`pytest` en `BACKEND/` e `IA-SERVICE/`, `vitest` en frontend).
- El payload que llega a IA-SERVICE nunca contiene columnas identificables (verificado por test, no solo por inspección visual).
