# Plan — Chatbot de preguntas sobre los datos cargados

> **Estado:** APROBADO como plan de implementación (2026-09-20).
> **Alcance:** Opción A — "LLM lector" con contexto de indicadores agregados.
> **Relacionado:** TASK-004 en `docs/TASKS.md`, `IA-SERVICE`/Ollama, narrativas IA actuales.

---

## 1. Decisión de diseño

El chatbot **no** genera código Python por pregunta (opción B, estilo pandas-ai). El backend ya
calcula los agregados necesarios para el dashboard (`calcular_completo`); el chatbot reutiliza ese
contexto **preagregado** y el LLM solo lo lee y redacta la respuesta en lenguaje natural.

- **Seguro:** no se ejecuta código generado por un modelo (sin sandboxing ni inyección).
- **Privado:** nunca se reenvían filas de pacientes, solo indicadores agregados (regla del README y
  de `narrativa_service.extraer_indicadores_para_narrativa`).
- **Reutiliza:** el 100% del pipeline de `analisis_service.calcular_completo` ya construido.
- **Límite conocido:** solo responde preguntas que se pueden contestar con los agregados disponibles.
  Si el dato no está en el contexto, el modelo lo dice en vez de inventarlo.

### Pregunta "¿cuántas muertes hubo en enero de 2024?"

```
[Usuario] ¿Cuántas muertes hubo en enero de 2024?
[Backend] calcula agregados que YA existen -> contexto JSON  (distribucion_mensual)
[Prompt]  DATOS: {"2024": {"1": 3, "2": 5, ...}}  +  PREGUNTA: ¿cuántas muertes en enero 2024?
[LLM]     "En enero de 2024 hubo 3 muertes maternas."
```

El agregado ya está corrido en `_analisis_calculo.py:66` (distribución mensual) — el LLM solo
redacta.

---

## 2. Flujo de datos

```
[Frontend React]
      | POST /api/analisis/{pk}/chat/   body: {pregunta, historial}
      v
[Backend FastAPI]  ->  _get_analisis_or_404(pk)
      | calcula indicadores agregados (calcular_completo con filtros del dashboard)
      | extrae subconjunto agregado (extraer_indicadores_para_narrativa)
      | NUNCA envía filas de pacientes
      v
[IA-SERVICE]  POST /chat  {pregunta, historial, contexto, tipo_analisis}
      | arma mensajes system + historial + pregunta
      v
[Ollama /api/chat]  (qwen2.5)
      v
[IA-SERVICE] -> {respuesta, modelo} -> [Backend] -> [Frontend]
```

El historial de la conversación viaja con cada petición (microservicio sin estado). Si Ollama o
ia-service no están disponibles, el backend responde 503 y el frontend oculta/avisa la
indisponibilidad (mismo patrón que las narrativas).

---

## 3. Cambios por servicio

### 3.1 IA-SERVICE (`ia-service/`) — puerto 8001

**`ia-service/schemas.py`** — modelos nuevos:

```python
class ChatMensaje(BaseModel):
    rol: Literal['usuario', 'asistente']
    contenido: str

class ChatRequest(BaseModel):
    pregunta: str
    historial: list[ChatMensaje]          # conversación previa (últimos N mensajes)
    tipo_analisis: Literal['mortalidad', 'morbilidad']
    contexto: dict[str, Any]              # indicadores agregados

class ChatResponse(BaseModel):
    respuesta: str
    modelo: str
```

**`ia-service/ollama_client.py`** — nueva función `chatear()` que usa `/api/chat` (messages) en
lugar de `/api/generate`, con los mismos `except` de `TimeoutException` / `ConnectError` que
`generar()` (ollama_client.py:31). Devuelve `response.json()['message']['content']`.

**`ia-service/prompts/chat_datos.py`** — plantilla nueva (estilo de `resumen_ejecutivo.py`):

- Rol **system**: "asistente de salud pública que responde preguntas sobre el análisis usando SOLO
  los datos agregados proporcionados; si el dato no está, lo dice; no inventa cifras; no menciona
  identificadores de personas".
- El contexto JSON se serializa dentro del mensaje system.
- El historial y la pregunta van como `messages` con rol `user`/`assistant`.

**`ia-service/prompts/__init__.py`** — registrar `chat_datos.construir` o exponer constructor.

**`ia-service/main.py`** — endpoint nuevo:

```python
@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    # 1. arma los messages (system con contexto + historial + pregunta)
    # 2. llama a generar/chatear() con timeout amplio
    # 3. 503 (OllamaUnavailableError) si Ollama no responde
    # 4. devuelve ChatResponse(respuesta=..., modelo=Config.ollama_model)
```

**Tests:** `ia-service/tests/` — test de `chatear()` (mock de httpx), test del constructor de
prompt, test del endpoint `/chat` (200 con payload válido, 503 con Ollama caído). Estilo de los 18
tests existentes.

### 3.2 Backend (`backend/`) — puerto 8000

**`backend/services/ia_client.py`** — nueva función `chatear_ia()`, espejo de `generar_narrativa()`
(ia_client.py:14): hace POST a `IA_SERVICE_URL/chat`, traduce timeouts/conexión/status != 200 a
`IAServiceUnavailableError`, devuelve `{'respuesta': ..., 'modelo': ...}`.

**`backend/api/routers/analisis.py`** — endpoint nuevo junto a `obtener_narrativa_ia` (línea 330):

```python
@router.post('/analisis/{pk}/chat/')
def chat_analisis(pk: int, req: ChatRequest, db: Session = Depends(get_db)):
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        # 1. analisis_completo = analisis_service.calcular_completo(analisis, year, month, db)
        # 2. contexto = extraer_indicadores_para_narrativa('resumen_ejecutivo'|...)
        #    O un subconjunto fijo de agregados (ver §4)
        # 3. try: ia_client.chatear_ia(pregunta, historial, contexto, analisis.tipo)
        #    except IAServiceUnavailableError -> 503 (patrón de obtener_narrativa_ia)
        # 4. devuelve {'respuesta', 'modelo'}
```

Se reutilizan `_get_analisis_or_404` y `_errores_servicio`; no se agrega lógica de análisis nueva.

**Tests:** `backend/tests/` — test del endpoint `/chat` (mock de `ia_client.chatear_ia`): 200 con
contexto agregado correcto, 503 cuando IA está caída, 404 para análisis inexistente.

### 3.3 Frontend (`frontend/maternanalytics/`) — puerto 5173

**`src/api.ts`** — función nueva junto a `obtenerNarrativa` (línea 102):

```typescript
export interface ChatMensaje { rol: 'usuario' | 'asistente'; contenido: string }

export async function enviarMensajeChat(
  analisisId: number,
  pregunta: string,
  historial: ChatMensaje[],
): Promise<{ respuesta: string; modelo: string } | null> {
  // POST {API_URL}/analisis/{id}/chat/  con timeout ~120s (LLM local lento)
  // status 503 -> null (IA no disponible, mismo patrón que narrativas)
  // ok -> { respuesta, modelo }
}
```

**Componente `src/components/chat/ChatWidget.tsx`**:

- Estado `historial: ChatMensaje[]` en `useState`.
- Input de texto + botón enviar (reutiliza `components/icons/SendIcon.tsx`).
- Burbujas usuario/asistente; spinner mientras espera respuesta.
- `null` -> mensaje "IA no disponible" (no rompe el dashboard).
- Límite de historial enviado (p. ej. últimos 6 mensajes) para controlar el tamaño del prompt.

**Integración:** en el layout del dashboard (`DashboardOKD.tsx`) como panel flotante o pestaña,
sin bloquear la navegación. Location a confirmar al implementar (tarea de UI dentro del plan).

**Tests:** `api.test.ts` (función `enviarMensajeChat`, casos 200/503/error) y test del componente
(mensaje enviado, respuesta renderizada, estado de indisponibilidad).

---

## 4. Contexto agregado que se envía

Subconjunto fijo derivado de `calcular_completo` (`_analisis_calculo.py:80-112`), sin columnas
por-registro:

| Clave | Fuente | Permite responder |
|---|---|---|
| `estadisticas_basicas` | `calcular_estadisticas_basicas()` | totales, conteos, % |
| `distribucion_mensual` | `_calcular_distribucion_mensual` | "¿cuántos en enero?", tendencia |
| `demoras` (mortalidad) | `analizar_demoras()` | protocolo de demoras |
| `causas_cie10` | `analizar_causas_cie10(top_n=10)` | "¿cuáles causas principales?" |
| `criterios_inclusion` (morbilidad) | `analizar_criterios_inclusion()` | criterios MME |
| `distribucion_sociodemografica` | `analizar_distribucion_sociodemografica()` | zona/etnia/afiliación |
| `obstetrico_edad` / `distribucion_edad_riesgo` | por procesador | edad y riesgo |

Se implementará como un helper en el backend (p. ej. `ChatRequest` recibe el dict ya filtrado),
tomando del dict completo **solo** las claves anteriores. Si una clave no existe (p. ej. `demoras`
en morbilidad), se omite.

Los filtros `year`/`month` activos del dashboard aplican a `calcular_completo`; la
`distribucion_mensual` se calcula **antes** del filtrado por diseño actual
(`_analisis_calculo.py:64-67`).

---

## 5. Criterios de aceptación

- [x] `POST /chat` en ia-service responde con texto y modelo (tests con mock de Ollama).
- [x] `POST /api/analisis/{pk}/chat/` responde `200` con contexto agregado y `503` cuando
      IA-SERVICE no está disponible (sin romper el resto de endpoints).
- [x] El frontend muestra la conversación, maneja el estado de carga y el mensaje de
      "IA no disponible" cuando corresponde.
- [x] No se envían filas de pacientes a ningún servicio (solo agregados).
- [x] El chat no bloquea el dashboard; si el servicio de IA cae, el resto sigue funcionando.
- [x] `npx tsc --noEmit`, `pnpm lint`, `pnpm test` y `pnpm build` en verde.
- [x] Pytest de `backend` e `ia-service` en verde.
- [x] Se documenta en `PRODUCT.md` y `ARCHITECTURE.md` el comportamiento del chatbot.

---

## 6. Archivos tocados

**IA-SERVICE**
- `ia-service/schemas.py`
- `ia-service/ollama_client.py`
- `ia-service/prompts/chat_datos.py` (nuevo)
- `ia-service/prompts/__init__.py`
- `ia-service/main.py`
- `ia-service/tests/` (nuevos)

**Backend**
- `backend/services/ia_client.py`
- `backend/api/routers/analisis.py`
- `backend/tests/` (nuevos)

**Frontend**
- `frontend/maternanalytics/src/api.ts`
- `frontend/maternanalytics/src/components/chat/ChatWidget.tsx` (nuevo)
- `frontend/maternanalytics/src/components/DashboardOKD.tsx` (integración)
- `frontend/maternanalytics/src/api.test.ts`, componente test (nuevo)

---

## 7. Tareas de implementación (orden)

1. **IA-SERVICE:** schemas, `chatear()` en ollama_client, plantilla `chat_datos`, endpoint `/chat`.
   Tests de ia-service.
2. **Backend:** `chatear_ia()` en ia_client, helper de contexto agregado, endpoint
   `/api/analisis/{pk}/chat/`. Tests de backend.
3. **Frontend:** `enviarMensajeChat` en api.ts, `ChatWidget`, integración en el dashboard.
   Tests de frontend.
4. **Verificación:** `pnpm build`, `pnpm lint`, `pnpm test`, `npx tsc --noEmit`, pytest de los dos
   servicios, prueba manual con la app levantada y Ollama encendido/apagado.
5. **Docs:** actualizar `PRODUCT.md`, `ARCHITECTURE.md`, `TASKS.md` (TASK-004), `CHANGELOG.md`.

---

## 8. Riesgos y contramedidas

| Riesgo | Contramedida |
|---|---|
| LLM inventa cifras fuera del contexto | Prompt system restrictivo + solo agregados; el modelo debe decir "no tengo ese dato". |
| Prompt muy grande (historial largo) | Limitar historial enviado a últimos ~6 mensajes y contexto fijo, no acumulativo. |
| Latencia alta con qwen2.5 en CPU | Timeout amplio en frontend (~120s) y UX de "escribiendo...". |
| Ollama/ia-service caídos | 503 limpio, mismo patrón de narrativas; el dashboard sigue operando. |
| Pregunta sobre un cruce no precalculado | Respuesta honesta "no tengo ese dato" (extensión futura: opción B). |

---

## 9. Extensión futura (fuera de alcance)

**Opción B — generación de código (pandas-ai):** permitiría preguntas ad-hoc
("cruce rural × preeclampsia"). Requiere sandboxing de ejecución, whitelist de columnas, validación
y auditoría; rompe la simplicidad y la regla de privacidad actual. No se implementa en este plan.