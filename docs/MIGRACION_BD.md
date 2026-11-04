# Migración de la base de datos a la estructura nueva

Cómo pasar una base con la **estructura anterior** (la de la rama `main`: tablas
`antecedentes_obstetricos` y `antecedente_materno`, columnas `causa_asociada_2/3/4`,
`institucion_ref_1/2`, `cirugia_1/2` y `control_prenatal.num_cpn`) a la estructura actual
(`docs/BASE_DE_DATOS.md`) **sin perder información**.

## Principio: copiar a una base nueva, no modificar la existente

La migración **no altera la base de origen**: la abre en modo de solo lectura y copia los
datos a una base **nueva** creada con el script actual. La base anterior queda intacta como
respaldo vivo y como referencia; si algo sale mal, la plataforma sigue usando la anterior.

Reconstruir desde cero **no es** una migración: crear la base con el script y volver a cargar los
Excel pierde los análisis guardados, las narrativas, los usuarios y el historial de cargas, y
cambia los identificadores. Este procedimiento conserva todos los identificadores (`id_caso`,
`id_paciente`, análisis, importaciones), así que las relaciones se mantienen.

El backend **se niega a arrancar** sobre una base con la estructura anterior
(`db/migrations.py::verificar_estructura_compatible`): crear las tablas nuevas vacías al lado
de las viejas dejaría los antecedentes históricos fuera de las vistas del dashboard.

## Qué hace el script `backend/scripts/migrar_estructura_anterior.py`

| Origen (estructura anterior) | Destino (estructura nueva) |
|---|---|
| `antecedentes_obstetricos` | Comunes en `antecedente_obstetrico` (`caso_morbilidad_id`); propios en `antecedente_obstetrico_morbilidad`. Renombres: `num_gestaciones`→`gestaciones`, `muertos`→`nacidos_muertos`, `vivos`→`hijos_vivos`, `semanas_inicio_cpn`→`semana_inicio_cpn`. |
| `antecedente_materno` + `control_prenatal.num_cpn/semana_inicio_cpn` | Comunes en `antecedente_obstetrico` (`caso_mortalidad_id`, `id_regulacion_fec`→`id_regulacion_fecundidad`, `num_cpn`→`num_controles_prenatales`); convivencia y escolaridad en `antecedente_materno_mortalidad`. |
| `causas_morbilidad.causa_asociada_2/3/4` | `causa_asociada_morbilidad` con `orden` 1, 2 y 3 (la posición original se conserva aunque haya huecos). |
| `referencia.institucion_ref_1/2` | `referencia_institucion` (`orden` 1 y 2). |
| `manejo_hospitalario.cirugia_1/2` y `_cual` | `cirugia_adicional_morbilidad` (FK a `cat_tipo_cirugia`). |
| `api_usuario.departamento/secretaria` (texto) | No se copian: los nombres salen de las tablas maestras por `secretaria_codigo`. Si el texto no coincide con el maestro, se informa. |
| Resto de tablas | Columnas comunes, mismos identificadores. |

### Reglas de datos

- **CIE-10**: se normalizan (mayúsculas, sin punto ni espacios: `o72.1` → `O721`) antes de
  relacionarlos con el catálogo `cie10`. Vacíos y guiones (`—`) son «sin dato».
- **CIE-10 obligatorio inexistente** (causa principal de morbilidad, causa básica de
  mortalidad): la migración **se detiene** y lista cada caso. Se corrige en el origen o con un
  archivo de correcciones; el script no inventa equivalencias ni elimina registros.
- **Valor opcional que no puede guardarse**: no se descarta. Queda en la tabla
  `migracion_registro_pendiente` del destino (tabla y columna de origen, caso, posición, valor
  original y normalizado, motivo) y en el informe. Motivos posibles:
  - `cie10_inexistente`: causa asociada o complicación del feto (`compl_feto_rn_cie10`, que
    queda `NULL` en el destino) con un código que no está en el catálogo.
  - `repite_causa_principal`: una causa asociada igual a la principal del caso.
  - `causa_asociada_repetida_en_el_caso`: el mismo código en dos posiciones.
  - `repite_institucion_1`: la institución de referencia 2 igual a la 1.
- **Duplicados que la estructura nueva no admite** (dos antecedentes o dos referencias para un
  caso, dos casos con la misma secretaría, paciente y fecha): la migración **se detiene** y los
  lista. Hay que decidir a mano qué fila conservar, en el origen.
- **Catálogos**: los `cat_*` del origen deben coincidir con los del destino (mismo id y texto);
  si no, se detiene.
- **Secretarías y eventos**: deben existir en las tablas maestras del destino; si no, se detiene.
- `creado_en` vacío (lo permitía la estructura anterior) toma la fecha de la migración y se
  informa cada registro afectado.

## Procedimiento

> Ejecutar primero todo el procedimiento en una **copia** (por ejemplo, restaurando el respaldo
> en una base de pruebas). En el servidor real, coordinar una ventana sin cargas de Excel.

Desde `backend/`, con las credenciales en el entorno (`PGPASSWORD` o `DB_PASSWORD`):

1. **Respaldo** (el script lo vuelve a hacer y verificar con `--confirmar`, pero conviene tener
   uno propio):

   ```bash
   pg_dump -h localhost -U postgres -Fc -f respaldo_sivigila_$(date +%Y%m%d).dump sivigila_maternidad
   pg_restore --list respaldo_sivigila_*.dump > /dev/null && echo "respaldo legible"
   ```

2. **Base destino vacía** con el script actual:

   ```bash
   psql -h localhost -U postgres -d postgres -c "CREATE DATABASE sivigila_maternidad_v2 ENCODING 'UTF8';"
   psql -h localhost -U postgres -d sivigila_maternidad_v2 -v ON_ERROR_STOP=1 -f sivigila_maternidad_postgres.sql
   ```

3. **Simulación** (copia y valida todo dentro de una transacción y la deshace; el destino no
   cambia):

   ```bash
   python scripts/migrar_estructura_anterior.py --origen sivigila_maternidad \
       --destino sivigila_maternidad_v2 --simular
   ```

   Códigos de salida: `0` correcto, `2` hay bloqueantes (no se copió nada), `3` falló una
   validación (se deshizo todo), `1` error de uso o de conexión.

4. **Revisar el informe** en `backend/migracion_reportes/migracion_<fecha>.md` (y `.json`):
   bloqueantes, registros pendientes, observaciones, conteos por tabla y validaciones.

5. **Correcciones CIE-10** (solo si hubo `cie10_obligatorio_inexistente`): crear
   `correcciones_cie10.csv` con la decisión de una persona responsable de la información:

   ```csv
   tabla,columna,id_caso,valor_original,codigo_corregido
   causa_muerte,causa_basica_cie10,21,O99.99Z,O85
   causas_morbilidad,causa_principal_cie10,,O14-1,O141
   ```

   `id_caso` vacío aplica a todos los casos con ese valor. El código corregido también debe
   existir en el catálogo. Repetir la simulación con `--correcciones correcciones_cie10.csv`.
   Las correcciones aplicadas quedan en el informe.

6. **Migración confirmada** (hace y verifica un respaldo nuevo con `pg_dump`/`pg_restore --list`
   antes de copiar, y confirma solo si todas las validaciones pasan):

   ```bash
   python scripts/migrar_estructura_anterior.py --origen sivigila_maternidad \
       --destino sivigila_maternidad_v2 --confirmar [--correcciones correcciones_cie10.csv] \
       [--pg-bin /usr/lib/postgresql/16/bin]
   ```

7. **Permisos** del usuario de la aplicación sobre la base nueva (ver DEPLOY.md §2).

8. **Comprobar** antes de cambiar la conexión: abrir el dashboard apuntando a la base nueva en un
   entorno de prueba, revisar los conteos del informe y la tabla `migracion_registro_pendiente`.

9. **Cambiar la conexión**: `db_name=sivigila_maternidad_v2` en `backend/.env` y reiniciar el
   servicio. La base `sivigila_maternidad` **no se borra**: queda como respaldo y referencia.

**Volver atrás**: restablecer `db_name=sivigila_maternidad` y reiniciar. Como la base anterior
no se modificó, no hay nada que restaurar.

## Validaciones del informe

- Conteo por tabla, origen contra destino (las tablas hijas: valores migrados + pendientes =
  valores no vacíos del origen).
- Casos de morbilidad y de mortalidad por secretaría.
- Ninguna importación apunta a un caso inexistente.
- Antecedentes de cada caso comparados **campo por campo** entre origen y destino.
- Cada causa obligatoria igual a su valor normalizado (o a su corrección).
- Todas las llaves foráneas las hace cumplir PostgreSQL: una fila que no entra se identifica
  (tabla, identificadores y error) y la migración se deshace.

Las pruebas `backend/tests/test_migracion_estructura_anterior.py` ejecutan todo esto sobre bases
desechables: un origen con la estructura de main (`tests/fixtures/esquema_main_legado.sql`) y
datos con los casos difíciles (`tests/fixtures/datos_main_legado.sql`).

## Bases creadas por versiones intermedias de esta rama

Una base creada con el script de la rama antes de esta corrección (sin `cat_tipo_cirugia` ni las
llaves foráneas nuevas) **no es** la estructura anterior y el script de migración no la acepta
como origen. Al arrancar, el backend le agrega las columnas `evento` e `id_caso` de la bitácora,
siembra `cat_tipo_cirugia` y recrea triggers y vistas, pero **no** agrega las restricciones nuevas
(FK de CIE-10 en mortalidad, `UNIQUE(id_caso, cie10)`, institución no repetida, FK de
`cirugia_adicional_morbilidad.id_tipo_cirugia`). Solo se usaron para pruebas: se recomienda
recrearlas con el script.
