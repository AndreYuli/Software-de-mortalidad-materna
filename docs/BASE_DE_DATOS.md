# Base de datos (PostgreSQL)

Diagrama completo: [`modelo_de_datos.png`](modelo_de_datos.png) y [`modelo_de_datos.svg`](modelo_de_datos.svg)
(vectorial: se puede ampliar sin perder nitidez). Se dibuja desde la base real con
`backend/scripts/dibujar_modelo_de_datos.py`, así que no puede diferir del esquema.

## Una sola fuente de verdad

| Qué | Dónde vive |
|---|---|
| Tablas, llaves, restricciones, índices | `backend/db/models_sqlalchemy.py` |
| Tablas maestras de afiliación y CIE-10, funciones y triggers | `backend/db/auditoria.py` |
| Datos de los catálogos | `backend/db/semillas_catalogos.sql` |
| Vistas del dashboard | `backend/db/database_views.py` |
| **Script de reconstrucción** (generado, no se edita) | `backend/sivigila_maternidad_postgres.sql` |

`python scripts/generar_esquema_sql.py` (desde `backend/`) regenera el script; con `--check` falla si
quedó desactualizado. La prueba `tests/test_esquema_bd.py` hace esa misma comprobación.

## Reconstruir la base

1. Crear una base **vacía** (por ejemplo desde DBeaver).
2. Conectarse a ella y ejecutar `sivigila_maternidad_postgres.sql` completo.

El script no contiene `DROP DATABASE` ni `CREATE DATABASE` (el anterior sí traía `DROP DATABASE
sivigila_maternidad`). Al arrancar, el back-end repite de forma idempotente `create_all`, las tablas
maestras y los triggers, por lo que una base creada con el script o por el arranque queda igual.
Una base con la estructura anterior (columnas `num_gestaciones`, `institucion_ref_1`, etc.) **no se
migra**: se reconstruye.

## Decisiones de diseño

| Decisión | Por qué |
|---|---|
| **Tablas maestras** `cat_*`, `cat_evento`, `departamento`, `secretaria`, `cie10` | Los valores válidos viven en la base y las llaves foráneas impiden valores fuera de lista (antes `secretaria_codigo` y los CIE-10 eran texto libre). |
| **Antecedentes obstétricos en una sola tabla** (`antecedente_obstetrico`) | Gestaciones, partos, cesáreas, abortos, nacidos muertos, hijos vivos, regulación de fecundidad y controles prenatales eran columnas repetidas en morbilidad y mortalidad. Asociación excluyente: dos llaves anulables y un CHECK que exige exactamente una; índice único por caso. Lo propio de cada evento queda en `antecedentes_obstetricos` (morbilidad), `antecedente_materno` y `control_prenatal` (mortalidad). |
| **Triggers de tiempos** | `actualizado_en` lo escribe la base, no la aplicación. `creado_en` tiene valor por defecto del servidor. |
| **Bitácora** `auditoria_cambio` | Quién, cuándo, tabla, registro, operación y **nombres** de columnas cambiadas; no copia valores (los datos de pacientes no se duplican). |
| **Trazabilidad de la carga** | `api_sivigilaimportacion` guarda la fila cargada y su fecha; un trigger exige que `caso_id` exista en la tabla de su `tipo`. |
| **1:1 explícito** | Las tablas de detalle de morbilidad tienen `id_caso` único; las de mortalidad usan `id_caso` como llave primaria. |
| **Un caso no se repite** | Único por (secretaría, paciente, fecha del evento). |
| **CIE-10 normalizado** | Se guarda sin punto y en mayúsculas (`O141`); las causas de morbilidad tienen llave foránea a `cie10`. La tabla incluye la categoría de 3 caracteres (`O14`) porque la carga la acepta. |
| **Índices en todas las llaves foráneas** | PostgreSQL no los crea solo; la prueba `test_todas_las_tablas_tienen_llave_primaria_y_las_fk_estan_indexadas` lo verifica. |
| **Nombres de restricciones predecibles** | `pk_`, `fk_`, `uq_`, `ix_` (convención de nombres en `db/database.py`). |

## Límites declarados

- La causa básica de **mortalidad** no tiene llave foránea a `cie10` (la carga solo valida formato y
  prefijos); solo la de morbilidad.
- `paciente` es único por número de documento y no pertenece a una secretaría: un mismo paciente
  puede aparecer en casos de secretarías distintas.
- El aislamiento por secretaría lo aplica el código (filtros), no la base (no hay *row level security*).
- Las columnas de fecha son `timestamp` sin zona horaria.
- Los booleanos de factores de riesgo y complicaciones (mortalidad) siguen como columnas: es un
  conjunto fijo de la ficha 550.
- Los identificadores usan `SERIAL`, no `IDENTITY`.
