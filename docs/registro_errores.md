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
1. **Volumen de datos masivo (~20,000 registros):**
   - El archivo `dummy_mortalidad.xlsx` contiene 19,989 registros.
   - Durante la subida, el backend realiza múltiples tareas pesadas de forma secuencial:
     - Validación, cálculo de hashes y resolución de catálogos para 19,989 filas.
     - Inserción/actualización en base de datos PostgreSQL de miles de registros relacionados (pacientes, antecedentes, causas, demoras).
     - Escritura en disco de un archivo Excel acumulado de gran tamaño con `openpyxl`.
2. **Límite de tiempo en el frontend (`fetchWithTimeout`):**
   - El cliente web tiene límites de espera (`REQUEST_TIMEOUT_MS = 30s`, `UPLOAD_TIMEOUT_MS = 180s`, `completo = 90s`).
   - Si la operación en el servidor supera ese tiempo (o si el worker de Uvicorn queda saturado por la CPU/disco sin responder a tiempo las solicitudes entrantes), el frontend cancela la petición mediante `AbortController` y lanza este mensaje.

### Opciones de Solución / Mitigación
1. **Ajuste de tiempos de espera (Timeouts):** Ampliar `UPLOAD_TIMEOUT_MS` si se van a cargar archivos de decenas de miles de registros de forma habitual.
2. **Optimización de persistencia en lotes (Batch inserts):** Agrupar inserciones SQL masivas (`bulk_insert_mappings` o `executemany`) y optimizar la generación del Excel acumulado.
3. **Cargar datasets de prueba más ligeros:** Para pruebas locales y visuales, usar conjuntos de datos de 500 a 2,000 registros donde la respuesta es casi inmediata.
