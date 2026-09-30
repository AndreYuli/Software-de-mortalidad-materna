# Bitácora de Registro de Errores - SIVIGILA

Documento continuo para registrar y diagnosticar todos los errores reportados durante el uso y pruebas de la plataforma.

---

## [Error #1] Causa básica CIE-10 vacía en 9,984 filas de Excel de Mortalidad

- **Fecha:** 2026-09-29
- **Archivo origen:** `backend/media/uploads/2026/08/dummy_mortalidad.xlsx`
- **Mensaje exacto:**
  > *La columna '10.1 Causa básica CIE-10' está vacía en 9984 fila(s) del Excel: 19991, 19992, 19993, 19994, 19995, 19996, 19997, 19998, 19999, 20000, 20001, 20002, 20003, 20004, 20005, 20006, 20007, 20008, 20009, 20010 … y 9964 más. Es obligatoria: complete el código CIE-10 o elimine esas filas y vuelva a cargar el archivo.*

### Causa Raíz
1. **Regla de negocio en backend ([sivigila_service.py](file:///C:/Users/lopez/Documents/UNIVERSIDAD/Software-de-mortalidad-materna/backend/services/sivigila_service.py)):**
   - La función `_verificar_causa_completa` revisa que ningún registro a insertar tenga la causa básica CIE-10 en blanco, ya que es el dato clínico crítico de la ficha 550 (mortalidad materna).
2. **Contenido del archivo `dummy_mortalidad.xlsx`:**
   - Filas 2 a 19990 (19,989 registros): Tienen todos los datos completos.
   - Filas 19991 a 29974 (9,984 registros): Solo tienen datos de identificación y defunción básicos (6 columnas), pero **21 columnas clínicas están completamente vacías (`NaN`)**, entre ellas:
     - `10.1 Causa básica CIE-10`
     - `6.1 Convivencia`, `6.3 Escolaridad`, `6.4 Regulación Fecundidad`
     - `9.1 Momento de la muerte`, `9.2 Semana gestación`, `9.4 Tipo de parto`
     - Demoras 1 a 4.

### Solución Aplicada
- Se creó el script [`backend/scripts/limpiar_mortalidad_incompleta.py`](file:///C:/Users/lopez/Documents/UNIVERSIDAD/Software-de-mortalidad-materna/backend/scripts/limpiar_mortalidad_incompleta.py).
- Se generó un respaldo de seguridad previo: `dummy_mortalidad.xlsx.bak`.
- Se ejecutó el script y se eliminaron las 9,984 filas truncadas.
- **Resultado:** El archivo [`dummy_mortalidad.xlsx`](file:///C:/Users/lopez/Documents/UNIVERSIDAD/Software-de-mortalidad-materna/backend/media/uploads/2026/08/dummy_mortalidad.xlsx) quedó con **19,989 filas 100% completas** y válidas para importación.
- **Estado:** ✅ Resuelto.

---

## [Error #2] Timeout al procesar o responder ("El servidor tardó demasiado en responder. Intenta de nuevo.")

- **Fecha:** 2026-09-29
- **Origen:** Frontend (`frontend/maternanalytics/src/api.ts` -> `fetchWithTimeout`)
- **Mensaje exacto:**
  > *El servidor tardó demasiado en responder. Intenta de nuevo.*

### Causa Raíz
1. **Volumen de datos masivo (~20,000 registros = ~120,000 inserciones SQL):**
   - El archivo `dummy_mortalidad.xlsx` contiene 19,989 registros.
   - Por cada registro, el backend crea e inserta individualmente vía ORM:
     - 1 Paciente
     - 1 Caso de Mortalidad
     - 1 Antecedente Materno
     - 1 Causa de Defunción
     - 1 Registro de Demora
     - 1 Registro de Importación (hashes)
   - Esto genera **más de 100,000 a 120,000 sentencias SQL individuales** dentro de una única petición HTTP síncrona.
   - Además, al finalizar se genera en disco un archivo Excel consolidado de 20,000 filas con openpyxl.
2. **Corte por límites de tiempo (Timeouts en cadena):**
   - **Servidor Apache (servidor de producción/universidad):** El proxy Apache tiene un `ProxyTimeout` por defecto de **60 segundos**. Si la respuesta tarda más de 1 minuto, Apache corta la conexión con Gateway Timeout.
   - **Cliente Web (Frontend):** `UPLOAD_TIMEOUT_MS = 180_000` (3 minutos). Si se supera ese tiempo, React lanza:
     > *El servidor tardó demasiado en responder. Intenta de nuevo.*

### Opciones de Solución / Mitigación
1. **Para pruebas inmediatas:** Reducir `dummy_mortalidad.xlsx` a un tamaño manejable (ej. 1,000 o 2,000 registros, o usar `data/pruebas/realista_mortalidad_550.xlsx` con 60 registros) para que cargue en 5-10 segundos.
2. **Configuración en servidor:** Añadir `timeout=300` a la directiva `ProxyPass` en `/etc/apache2/sites-enabled/000-default.conf`.
3. **Optimización de Backend:** Migrar la persistencia de ORM fila por fila a inserciones por lotes (`bulk_insert_mappings` o `db.bulk_save_objects`).

---

## [Error #3] DatatypeMismatch en columnas booleanas de PostgreSQL (sin_antecedentes integer vs boolean)

- **Fecha:** 2026-09-29
- **Archivo involucrado:** `backend/media/uploads/2026/08/sivigila_mortalidad_10_casos.xlsx`
- **Mensaje exacto:**
  > *Error al guardar los datos en la base de datos: (psycopg2.errors.DatatypeMismatch) la columna «sin_antecedentes» es de tipo boolean pero la expresión es de tipo integer LINE 1: ...actores, gingivitis_periodontitis) VALUES (90104, 0, 0, 0, 0... ^ HINT: Necesitará reescribir la expresión o aplicarle una conversión de tipo. [SQL: INSERT INTO antecedente_riesgo (id_caso, sin_antecedente…*

### Causa Raíz
1. **Discrepancia entre esquema PostgreSQL y modelos SQLAlchemy:**
   - En el esquema de base de datos (`backend/sivigila_maternidad_postgres.sql`), las tablas `antecedente_riesgo`, `complicacion_embarazo`, `causa_muerte`, `criterios_enfermedad`, `criterios_falla_organica`, `criterios_manejo` y `referencia` tienen sus columnas indicadoras definidas como `BOOLEAN NOT NULL DEFAULT FALSE`.
   - Sin embargo, en `backend/db/models_sqlalchemy.py` todas estas columnas estaban tipadas como `Column(Integer)`.
   - Además, `_parse_bool` en `backend/utils/type_parsers.py` retornaba enteros `0` o `1`.
2. **Comportamiento en PostgreSQL vs SQLite:**
   - SQLite acepta enteros como sustitutos de booleanos sin quejarse.
   - PostgreSQL es estrictamente tipado y rechaza la inserción de un `integer` (0 o 1) en una columna `boolean` sin casteo explícito, lanzando `psycopg2.errors.DatatypeMismatch`.

### Solución Aplicada
1. Se actualizó `backend/db/models_sqlalchemy.py`:
   - Se importó `Boolean`.
   - Se corrigieron los tipos a `Column(Boolean, ...)` en todas las tablas afectadas (`AntecedenteRiesgo`, `ComplicacionEmbarazo`, `CausaMuerte`, `Referencia`, `AntecedentesObstetricos`, `CriteriosEnfermedad`, `CriteriosFallaOrganica`, `CriteriosManejo`).
2. Se actualizó `backend/utils/type_parsers.py`:
   - `_parse_bool` ahora retorna tipos booleanos nativos (`True` o `False`).
3. Se actualizó `backend/services/_sivigila_mortalidad.py` para trabajar directamente con `bool`.
4. Se agregó test de regresión en `backend/tests/test_sivigila_escritura.py` (`test_columnas_booleanas_en_modelos_sqlalchemy`).
- **Estado:** ✅ Resuelto.

---

## [Error #4] CheckViolation en criterios_manejo (restricción chk_total_crit)

- **Fecha:** 2026-09-29
- **Archivo involucrado:** `backend/media/uploads/2026/08/TEST_TASK15_Morbilidad.xlsx`
- **Mensaje exacto:**
  > *Error al guardar los datos en la base de datos: (psycopg2.errors.CheckViolation) el nuevo registro para la relación «criterios_manejo» viola la restricción «check» «chk_total_crit» DETAIL: La fila que falla contiene (12, 40012, t, t, f, 0, f, f, f, f, f, null).*

### Causa Raíz
1. **Regla oficial SIVIGILA 549 y restricción PostgreSQL:**
   - La tabla `criterios_manejo` tiene la restricción `CONSTRAINT chk_total_crit CHECK (total_criterios BETWEEN 1 AND 14)`.
   - Según el protocolo de vigilancia del INS para Morbilidad Materna Extrema (Ficha 549), un caso debe presentar al menos 1 criterio de gravedad para ser clasificado como tal.
2. **Datos inconsistentes en el Excel:**
   - En el archivo subido, filas como la fila 8 tenían criterios de gravedad marcados como positivos (por ejemplo, Sepsis, Ruptura uterina, Ingreso UCI y Cirugía adicional), pero la columna *"Total criterios"* venía con valor `0`.
   - Al insertar directamente ese `0`, PostgreSQL rechazó la fila por violar la restricción `chk_total_crit`.
   - Asimismo, campos de estancia hospitalaria (`dias_estancia_uci`) con valor `0` violaban restricciones tipo `CHECK (dias_estancia_uci >= 1)` en vez de registrarse como `NULL` (sin estancia en UCI).

### Solución Aplicada
1. En `backend/services/_sivigila_morbilidad.py`:
   - Se implementó cálculo defensivo de `total_criterios`: si en el Excel viene vacío, `0` o fuera de rango, el backend calcula la sumatoria real de los criterios clínicos marcados en la fila (mínimo 1, máximo 14).
   - Se sanearon los campos de `manejo_hospitalario`: si `dias_estancia_uci` o `dias_estancia_hosp` son `< 1`, o `unidades_transfundidas < 3`, se asignan como `None` (`NULL` en SQL) en lugar de valores inválidos que violen las restricciones de base de datos.
- **Estado:** ✅ Resuelto.

---

## [Error #5] Chatbot IA no mostraba nombres descriptivos de causas CIE-10 (mostraba códigos con dos puntos vacíos)

- **Fecha:** 2026-09-29
- **Consulta del usuario al Asistente IA:**
  > *"Según la sección 'causas_cie10' del contexto de datos, las causas principales de morbilidad en este análisis son: 1. O72.1 (35,29%): 2. O99.4 (29,41%): 3. O14.1 (26,47%): 4. O15.1 (2,94%): 5. O08.0 (2,94%): 6. O14.0 (2,94%) ... me mostro los numeros mas no los nombres"*

### Causa Raíz
1. En `backend/services/procesador_base.py` (`_analizar_causas_cie10`), el backend construía la lista `top_causas` conteniendo únicamente las llaves `codigo`, `casos` y `porcentaje`, sin asociar la descripción clínica del código CIE-10.
2. El system prompt de `ia-service/prompts/chat_datos.py` prohíbe taxativamente inventar datos que no estén en el JSON recibido (`Regla 1: NO inventes cifras ni datos que no estén en el contexto`).
3. En consecuencia, el modelo intentaba redactar la lista de causas dejando los dos puntos para el nombre, pero al no tener los nombres en su contexto, omitía la descripción textual.

### Solución Aplicada
1. Se centralizó la tabla oficial de 12.634 diagnósticos CIE-10 en `data/referencia/cie10_nombres.json`.
2. Se creó el módulo `backend/utils/cie10.py` con la función `obtener_nombre_cie10()`.
3. Se actualizó `backend/services/procesador_base.py` para enriquecer cada elemento de `top_causas` con el campo `'nombre'`.
4. Se agregó instrucción explícita en `ia-service/prompts/chat_datos.py` (Regla 5) para indicar diagnósticos con nombre descriptivo acompañado del código.
- **Estado:** ✅ Resuelto.

---

## [Error #6] Chatbot IA indicaba no tener información sobre pacientes en UCI o cirugía

- **Fecha:** 2026-09-29
- **Consulta del usuario al Asistente IA:**
  > *"¿Cuántas pacientes requirieron ingreso a UCI o cirugía?"*
  > *Respuesta:* *"No tengo información específica sobre el número de pacientes que requirieron ingreso a UCI o cirugía en el contexto de datos proporcionado..."*

### Causa Raíz
1. En `backend/api/routers/analisis.py`, la lista `claves_contexto` definía un subconjunto restringido de indicadores para inyectar en el prompt de la IA.
2. Se omitió la clave `severidad_fallas` (calculada por `MorbilidadProcessor.analizar_severidad_fallas()`), la cual contiene el conteo de pacientes con `Ingreso UCI`, `Cirugía adicional`, `Transfusión` y fallas orgánicas.
3. También faltaban claves agregadas como `momento_ocurrencia`, `distribucion_edad_gestacional`, `momento_muerte`, `tiempo_remision` e `institucion_referencia`.

### Solución Aplicada
1. En `backend/api/routers/analisis.py`, se expandió `claves_contexto` incluyendo `severidad_fallas`, `momento_ocurrencia`, `momento_muerte`, `tiempo_remision`, `institucion_referencia` y `distribucion_edad_gestacional`.
2. En `backend/services/narrativa_service.py`, se integró `severidad_fallas` en el resumen ejecutivo cuando está disponible.
3. Se agregaron pruebas automáticas de regresión en `backend/tests/test_analisis_router_chat.py`.
- **Estado:** ✅ Resuelto.

