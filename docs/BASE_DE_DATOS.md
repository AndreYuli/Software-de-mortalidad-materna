# Base de datos (PostgreSQL)

Diagramas (en `docs/modelo_de_datos/`; los `.svg` son vectoriales y se pueden ampliar sin perder nitidez):
`bd_00_completa` (todas las tablas), `bd_01_nucleo`, `bd_02_sistema`, `bd_03_morbilidad`, `bd_04_mortalidad` y
`bd_05_catalogos`. Se dibujan desde una base real con `backend/scripts/dibujar_modelo_de_datos.py` (conectado
a una base creada con el script, no a la de trabajo), así que no pueden diferir del esquema. En los de dominio,
las llaves hacia un catálogo o hacia una tabla de otro diagrama se anotan en la columna («→ tabla») en vez de
dibujarse como línea.

## Una sola fuente de verdad

| Qué | Dónde vive |
|---|---|
| Tablas, llaves, restricciones, índices | `backend/db/models_sqlalchemy.py` (`Base`) |
| Vistas (modelos de solo lectura) | `backend/db/models_sqlalchemy.py` (`VistaBase`, `MetaData` aparte) y su SQL en `backend/db/database_views.py` |
| Tablas maestras (eventos, afiliación, CIE-10, tipos de cirugía), funciones y triggers | `backend/db/auditoria.py` |
| Datos de los catálogos `cat_*` | `backend/db/semillas_catalogos.sql` |
| **Script de reconstrucción** (generado, no se edita) | `backend/sivigila_maternidad_postgres.sql` |
| **Migración desde la estructura anterior** | `backend/scripts/migrar_estructura_anterior.py` ([MIGRACION_BD.md](MIGRACION_BD.md)) |

`python scripts/generar_esquema_sql.py` (desde `backend/`) regenera el script; con `--check` falla si
quedó desactualizado. La prueba `tests/test_esquema_bd.py` hace esa misma comprobación.

## Crear una base nueva (sin datos)

1. Crear una base **vacía** (por ejemplo desde DBeaver).
2. Conectarse a ella y ejecutar `sivigila_maternidad_postgres.sql` completo (fija `client_encoding` UTF-8).

El script no contiene `DROP DATABASE` ni `CREATE DATABASE`. Una base vacía también queda completa si
solo se arranca el backend: `create_all` crea las tablas, el arranque siembra los catálogos vacíos, las
tablas maestras y el CIE-10, recrea triggers y vistas. Las dos formas producen el mismo esquema (comparado
con `pg_dump --schema-only`) y la prueba `test_pg_arranque_sobre_base_vacia_crea_vistas_y_catalogos` lo
comprueba. Las vistas viven en un `MetaData` separado, así que `create_all` nunca las crea como tablas
físicas vacías; si encuentra una tabla `v_*` vacía de una versión anterior la reemplaza por la vista, y si
tiene filas no la toca y lo informa.

## Pasar una base con datos de la estructura anterior

**No se reconstruye: se migra** a una base nueva con `scripts/migrar_estructura_anterior.py`, con respaldo
previo, simulación, validación de conteos y relaciones, y sin modificar la base original
(ver [MIGRACION_BD.md](MIGRACION_BD.md)). El backend se niega a arrancar sobre la estructura anterior.

## Decisiones de diseño

| Decisión | Por qué |
|---|---|
| **Causas asociadas en 1FN** (`causa_asociada_morbilidad`) | Reemplaza las columnas repetidas `causa_asociada_2/3/4`. Una fila por causa con `orden` 1..3 (posición de la ficha 549), `UNIQUE(id_caso, orden)`, `UNIQUE(id_caso, cie10)`, FK a `caso_morbilidad` con `ON DELETE CASCADE` y FK a `cie10`. Se lee con la vista `v_causa_asociada_morbilidad` (una fila por causa, con su descripción) y la relación ORM `CasoMorbilidad.causas_asociadas`. |
| **Causa principal ≠ causa asociada** | No cabe en un `UNIQUE` (están en tablas distintas): la carga lo rechaza con fila y columna, y la migración lo deja en `migracion_registro_pendiente`. |
| **Instituciones de referencia en 1FN** (`referencia_institucion`) | Reemplaza `institucion_ref_1/2`. Según el instructivo de la ficha 549, la 2 (5.3) es la institución que remitió a la paciente **hacia la 1** (5.2): es una cadena de remisión, así que una misma institución no ocupa las dos posiciones (índice único sobre `lower(trim(institucion))`; la carga lo avisa con fila y columna). |
| **Cirugías adicionales en 1FN** (`cirugia_adicional_morbilidad`) | Reemplaza `cirugia_1/2` y `_cual`. `id_tipo_cirugia` es FK al catálogo `cat_tipo_cirugia` (1 Histerectomía, 2 Laparotomía, 3 Legrado, 4 Otra), los mismos cuatro valores que admitía el `CHECK` anterior. Dos cirugías «Otra» son válidas. |
| **Tablas maestras** `cat_*`, `cat_evento`, `departamento`, `secretaria`, `cie10`, `cat_tipo_cirugia` | Los valores válidos viven en la base y las llaves foráneas impiden valores fuera de lista. |
| **CIE-10 con llave foránea** | `causas_morbilidad.causa_principal_cie10`, `causa_asociada_morbilidad.cie10`, `causa_muerte.causa_basica_cie10` y `control_prenatal.compl_feto_rn_cie10` (opcional) referencian `cie10`. Se guardan normalizados (`O141`, sin punto). La tabla incluye la categoría de 3 caracteres (`O14`) porque la carga la acepta. La carga valida existencia con fila y columna antes de escribir. |
| **Antecedentes obstétricos en una sola tabla** (`antecedente_obstetrico`) | Gestaciones, partos, cesáreas, abortos, nacidos muertos, hijos vivos, regulación de fecundidad y controles prenatales eran columnas repetidas en morbilidad y mortalidad. Asociación excluyente: dos llaves anulables y un CHECK que exige exactamente una; índice único por caso. Lo propio de cada evento queda en `antecedente_obstetrico_morbilidad` (morbilidad) y `antecedente_materno_mortalidad` y `control_prenatal` (mortalidad). |
| **Triggers de tiempos** | `actualizado_en` lo escribe la base, no la aplicación. `creado_en` tiene valor por defecto del servidor. |
| **Bitácora** `auditoria_cambio` | Tabla, registro, operación, momento, usuario de base de datos, **evento e `id_caso`** (también en las tablas hijas: se resuelve por la columna del caso o por la tabla padre) y **nombres** de columnas cambiadas; no copia valores. Cubre pacientes, casos, antecedentes, causas (principales, asociadas y de muerte), instituciones, cirugías, control prenatal, análisis y usuarios. |
| **Trazabilidad de la carga** | `api_sivigilaimportacion` guarda la fila cargada y su fecha; un trigger exige que `caso_id` exista en la tabla de su `tipo`. |
| **1:1 explícito** | Las tablas de detalle de morbilidad tienen `id_caso` único; las de mortalidad usan `id_caso` como llave primaria. |
| **Un caso no se repite** | Único por (secretaría, paciente, fecha del evento). |
| **Índices en todas las llaves foráneas** | PostgreSQL no los crea solo; la prueba `test_todas_las_tablas_tienen_llave_primaria_y_las_fk_estan_indexadas` lo verifica. |
| **`api_usuario` sin texto repetido** | Solo guarda `secretaria_codigo`; los nombres salen de las tablas maestras. |
| **Nombres de restricciones predecibles** | `pk_`, `fk_`, `uq_`, `ix_` (convención de nombres en `db/database.py`). |

## Cómo se usan las causas asociadas en cada capa

| Capa | Dónde |
|---|---|
| Carga de Excel 549 | `services/_sivigila_morbilidad.py` (escribe filas hijas; recargar reemplaza, no duplica) y `services/sivigila_service.py` (valida código, repetición y causa principal) |
| Vista | `v_causa_asociada_morbilidad` |
| ORM | `CasoMorbilidad.causas_asociadas` (solo lectura, por `orden`) |
| API | `GET /api/sivigila/morbilidad/`: cada caso trae `causas_asociadas` (`orden`, `cie10`, `descripcion`), en una sola consulta adicional por página |
| Análisis | `_analisis_persistencia._agregar_causas_asociadas` las proyecta en memoria a las columnas de la plantilla; `MorbilidadProcessor.analizar_causas_asociadas` (cada caso cuenta una vez por código; porcentaje sobre el total de casos) |
| Dashboard | «Top 10 Causas asociadas de Morbilidad» (`TrendChartsRow`) |
| Exportes | Hoja «Causas asociadas CIE-10» del Excel, sección del informe PDF y filas «Morbilidad (causa asociada)» del CSV |

## Límites declarados

- `referencia_institucion.institucion` es texto libre: no hay un catálogo de instituciones (REPS)
  en el proyecto, así que dos escrituras distintas de la misma institución no se detectan.
- `paciente` es único por número de documento y no pertenece a una secretaría: un mismo paciente
  puede aparecer en casos de secretarías distintas.
- El aislamiento por secretaría lo aplica el código (filtros), no la base (no hay *row level security*).
- Las columnas de fecha son `timestamp` sin zona horaria.
- La bitácora guarda el usuario de la base de datos (`usuario_bd`), no el usuario de la aplicación: no sirve
  para saber quién cargó o editó. En un borrado en cascada de una tabla padre, las filas hijas quedan en la
  bitácora con `id_caso` nulo (el padre ya no existe cuando se registran).
- `api_usuario` no tiene rol, estado ni correo verificado (registro abierto).
- `total_criterios` (morbilidad) se guarda tal como viene o se calcula: no hay una restricción que lo compare
  con los criterios marcados, y la regla «ingreso a UCI exige días de UCI» cruza dos tablas, así que la valida
  la carga y no la base.
- `fecha_defuncion` es opcional.
- Los booleanos de factores de riesgo y complicaciones (mortalidad) y las cuatro demoras siguen como columnas:
  son atributos distintos de un conjunto fijo de la ficha 550, no un grupo repetido del mismo dato.
- Los identificadores usan `SERIAL`, no `IDENTITY`.
- Una base creada por una versión intermedia de esta rama no recibe en el arranque las restricciones nuevas
  (ver [MIGRACION_BD.md](MIGRACION_BD.md#bases-creadas-por-versiones-intermedias-de-esta-rama)).
