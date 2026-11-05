# Decisiones del proyecto

Este documento registra decisiones importantes para evitar que el equipo o los agentes de IA vuelvan a cuestionar o modificar decisiones previamente aprobadas.

Cada decisión debe mantenerse breve, concreta y trazable. Si una decisión cambia, no se debe borrar sin más: agregar una nueva decisión que la reemplace o actualizar su estado explicando el motivo.

## Estados posibles

- **PROPUESTA:** decisión sugerida, pendiente de validación.
- **APROBADA:** decisión aceptada y vigente.
- **REEMPLAZADA:** decisión sustituida por una decisión posterior.
- **DESCARTADA:** decisión que ya no se seguirá.

---

## DEC-001

### Fecha

2026-09-19

### Decisión

Las visualizaciones relacionadas deben aprovechar el espacio horizontal disponible cuando sea adecuado.

### Motivo

Facilitar la comparación entre visualizaciones y reducir desplazamiento vertical.

### Estado

APROBADA

---

## DEC-002

### Fecha

2026-09-19

### Decisión

Las gráficas dinámicas deben actualizar sus etiquetas, ejes, títulos y textos asociados cuando cambie la variable seleccionada.

### Motivo

Evitar etiquetas genéricas que no permitan identificar correctamente la información representada.

### Estado

APROBADA

---

## DEC-003

### Fecha

2026-09-20

### Decisión

Renombrar las carpetas `BACKEND`, `IA-SERVICE` y `FRONTED` a `backend`, `ia-service` y `frontend`, y separar el material no ejecutable en `data/` (referencia, pruebas sintéticas y `local` sin versionar), `notes/` (notas; `notes/local` sin versionar) y `scripts/` (arranque y pruebas e2e). Los planes y specs anteriores pasan a `docs/historico/`.

### Motivo

Nombres consistentes (`FRONTED` era un typo; en Linux `./BACKEND` y `./backend` son carpetas distintas) y separar código, documentación, notas y datos. Solo se versionan datos con procedencia confirmada: las fichas oficiales, la tabla CIE-10 y los Excel sintéticos generados por `backend/scripts`.

### Estado

APROBADA. Reemplaza la nota anterior de `ARCHITECTURE.md` que pedía no renombrar `FRONTED`.

---

## DEC-004

### Fecha

2026-09-20

### Decisión

No mover el código de `backend` ni de `ia-service` a una subcarpeta `app/`, y usar comillas simples en Python (`ruff format`, `quote-style = "single"`).

### Motivo

Pasar a `app/` obliga a reescribir unos 110 imports de primer nivel, `Path('media')` (relativo al directorio de arranque), los scripts, los tests y el `CMD` de Docker, sin aportar funcionalidad. Se puede retomar como tarea aparte. Las comillas simples son la preferencia del equipo.

### Estado

APROBADA

---

## DEC-005

### Fecha

2026-11-04

### Decisión

En producción, `ia-service` usa **Groq** (plan gratuito) como proveedor LLM, con el modelo `openai/gpt-oss-20b` y la API compatible con OpenAI (`LLM_BASE_URL=https://api.groq.com/openai/v1`). La API key vive solo en `ia-service/.env` del servidor, que no se versiona. El código no cambia: ya usaba `LLM_BASE_URL`, `LLM_API_KEY` y `OLLAMA_MODEL` para `/chat` y `/generar-narrativa`. En desarrollo se puede seguir usando Ollama dejando `LLM_BASE_URL` vacío.

### Motivo

- **Ollama local en el servidor:** descartado. La VM no expone `avx`, `avx2` ni `sse4_2`; `qwen2.5:1.5b` generó a 0,6 tokens/s (126 s para 50 tokens, más que el timeout de 120 s del chat) y `minicpm-v` no terminó en 300 s.
- **NVIDIA (proveedor anterior):** dejó de responder; desde el 2026-11-04 da `404 not found for account` en todos los modelos probados.
- **OpenRouter:** descartado por el equipo.
- **Groq con `openai/gpt-oss-20b`:** modelo de producción disponible en el plan gratuito de la cuenta; respondió en menos de 1 s desde el servidor. `llama-3.3-70b-versatile` no estaba disponible para la cuenta.

Límites observados el 2026-11-04: 1.000 peticiones/día y 8.000 tokens/min. No son garantías. Los indicadores agregados y las preguntas salen a un tercero (EE. UU.); nunca filas de pacientes.

### Estado

APROBADA. Reemplaza el uso de NVIDIA descrito antes en `DEPLOY.md`, sección 6.
