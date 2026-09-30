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
