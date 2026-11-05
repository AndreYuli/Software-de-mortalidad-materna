# Lote 3 - criterio de validación (escrito antes de ejecutar; corregido el 2026-11-05)

Corrección: la primera versión tomó como base `Validacion 2 - cifras de las narrativas.py`, que es el LOTE 1
del manuscrito (15 textos, Llama 3.2). La base correcta es el LOTE 2 (3-nov-2026), descrito abajo.

## Qué se prueba
Tercer lote, con el modelo del servidor: Groq, `openai/gpt-oss-20b` (`LLM_BASE_URL=https://api.groq.com/openai/v1`).

## Base: lote 2 (lote_narrativas_3-nov.json, editar_articulo_pasada2.py)
- 18 solicitudes (3 repeticiones x resumen_ejecutivo, demoras, tendencias x mortalidad y morbilidad); 2 fallaron por
  tiempo de espera, 16 narrativas analizadas. Modelo google/gemma-4-31b-it por la API de NVIDIA.
- Se generaron desde la propia plataforma (endpoint `/api/analisis/{id}/narrativa/{tipo}/` -> backend -> ia-service ->
  proveedor), con los análisis 2 (mortalidad) y 3 (morbilidad) del usuario E2E; el campo `verificacion` lo calculó el
  verificador del backend (`backend/services/narrativa_verificacion.py`, commit a520cdbf, rama correccion/aval-condicionado).
- El lote no guardó los indicadores de origen ni el script que lo generó (no hay script en el repo ni en 02_Correcciones).

## Qué se mantiene
- 18 solicitudes con la misma estructura, prompts de producción (`ia-service/prompts`), subconjunto de indicadores por
  tipo de `extraer_indicadores_para_narrativa`, llamada igual a `_chat_openai` (un mensaje `user`, sin parámetros extra,
  timeout 120 s) y el mismo verificador (copia exacta en `narrativa_verificacion_a520cdbf.py`).
- Criterio numérico: una cifra coincide si es igual a algún valor de los indicadores, redondeada (o truncada) a los
  decimales del texto; se excluyen códigos CIE-10, «CIE-10», «demora N» y numeración «(1)»/«1.». «6.065» vale como 6065 o 6,065.
  Los años y meses que son claves de `distribucion_mensual` cuentan como datos. Las cifras sin coincidencia se
  revisan una por una («derivada» o «no respaldada»). Se reportan también las alertas de coherencia del verificador.

## Qué cambia respecto del lote 2
| Aspecto | Lote 2 | Lote 3 |
|---|---|---|
| Modelo / proveedor | gemma-4-31b-it / NVIDIA | openai/gpt-oss-20b / Groq |
| Camino | plataforma completa (backend -> ia-service) | llamada directa a Groq con el mismo prompt y payload |
| Indicadores | de la BD (análisis 2 y 3) | recalculados con los mismos procesadores desde los Excel E2E |
| Datos de mortalidad | 400 casos | 400 = mortalidad-realista-200 + mortalidad-valida-pequena (INFERIDO, no exacto: ver abajo) |
| Reintentos | no | espera y reintento ante 429 (límite de Groq) |
| Registro | solo texto y verificación | además fecha, id del modelo devuelto, latencia, tokens, respuesta cruda |

## Datos: lo que se pudo y no se pudo reproducir
- Morbilidad (200 casos, 125 con tiempo de remisión): coincide con el lote 2.
- Mortalidad: los 400 casos salen de dos cargas E2E; con realista-200 + valida-pequena el verificador respalda 54 de las
  57 cifras de las narrativas de mortalidad del lote 2 (con realista-200 sola, 45). Las 3 restantes son la edad promedio
  (34,96 en el lote 2; 30,11 con estos Excel): el Excel realista pasa por la BD y la edad se recalcula, algo que este
  script no reproduce. Por tanto los indicadores de mortalidad del lote 3 son una aproximación, no los mismos del lote 2.
