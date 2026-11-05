# Pendientes tras la corrección al aval condicionado (al 4-nov-2026)

Lo ya hecho está en `CAMBIOS_CORRECCION_AVAL.md`. Los pendientes de fase 1 anteriores siguen en `PENDIENTES_FASE1.md`.

## Base de datos: estado de las observaciones de la matriz

| Ítem | Estado en el código | Falta |
|---|---|---|
| 5. Definición del modelo de datos | No aplica al código (redacción del artículo) | — |
| 6. PK, FK y cardinalidades | Implementado: todas las tablas con PK y FK indexadas; 1:1 explícito en el esquema (`id_caso` único o PK) | Actualizar la Figura 4 del artículo con los diagramas de `docs/modelo_de_datos/` |
| 7. Campos compartidos en antecedentes | Implementado: `antecedente_obstetrico` común; migración desde `antecedentes_obstetricos`/`antecedente_materno` probada | Actualizar artículo, Tablas 7–8 y Figura 4; ya no es «trabajo futuro» |
| 8. Causas asociadas (1FN) | Implementado: `causa_asociada_morbilidad` con FK, orden y `UNIQUE(id_caso, cie10)`; se recupera en vista, API, análisis, dashboard y exportes; migración probada | Actualizar artículo (Discusión y Conclusiones): la normalización ya no es una propuesta |
| 13. Confiabilidad del modelo de datos | Parcial: ver «Límites declarados» en `docs/BASE_DE_DATOS.md` | Mantener los límites visibles en el artículo |

## Servidor / despliegue
- [ ] Migrar la base del servidor con `scripts/migrar_estructura_anterior.py` siguiendo `docs/MIGRACION_BD.md` (respaldo, base nueva `sivigila_maternidad_v2`, simulación, revisión del informe, migración confirmada, cambio de `db_name`). **No** reconstruir ni borrar la base actual. Ensayarlo antes con una copia restaurada del respaldo.
- [ ] Revisar el informe de la simulación sobre los datos reales: bloqueantes (CIE-10 obligatorios inexistentes, duplicados) y registros pendientes. Las correcciones CIE-10 las decide una persona responsable de la información, no el script.
- [ ] Llevar la rama al servidor (hoy solo está en local, sin push) tras integrarla con `main`.
- [ ] Cambiar `OLLAMA_MODEL` en el `.env` del ia-service si el modelo vuelve a fallar; probar con una petición real.
- [ ] Rotar `jwt_secret` (valor por defecto en `backend/core/config.py`) y la clave de NVIDIA. `DEPLOY.md` publica la contraseña de ejemplo del usuario `app_mortalidad`: cambiarla en el servidor si se usó tal cual.
- [ ] El contador de intentos de login vive en memoria de cada proceso: con varios procesos cada uno cuenta aparte.
- [x] ~~El script SQL trae `DROP DATABASE`~~: ya no lo trae (lo verifica `test_script_sql_no_borra_ni_crea_bases_de_datos`). `DEPLOY.md` ya no indica `DROP DATABASE`.

## Datos y plantillas
- [ ] La plantilla oficial de morbilidad (`frontend/maternanalytics/public/plantillas/PLANTILLA DATOS MORBILIDAD.xlsx`, rama `main`) trae en la fila de ejemplo 4 la misma causa asociada (`N17.9`) en dos columnas. Con `UNIQUE(id_caso, cie10)` esa fila se rechaza con mensaje de fila y columna: corregir el ejemplo de la plantilla.
- [ ] `scripts/generar_excels_realistas.py` genera `6.1 Convivencia = 'Unión libre'`, que no existe en `cat_convivencia`: los Excel de mortalidad que produce no cargan (anterior a esta corrección).

## Funcionalidad
- [ ] Ítems 1 y 2 de la matriz: no hay modelo de asociación, solo frecuencia.
- [ ] Ítem 9: falta la revisión clínica de las narrativas por profesionales (el lote solo mide cifras y reglas de texto).
- [ ] Registro abierto: decidir verificación de correo institucional y aprobación de un administrador.
- [ ] Sin autenticación multifactor. Mínimo de contraseña de 8: por debajo de los 15 de NIST SP 800-63B-4 para un solo factor (declarado en el artículo (5)). Subirlo a 15 o agregar MFA lo resolvería.
- [ ] La lista de contraseñas comunes es corta, de ejemplo.
- [x] ~~La validación CIE-10 está en la aplicación, no en la base~~: todas las columnas CIE-10 tienen llave foránea a `cie10` (morbilidad y mortalidad).

## Calidad
- [ ] Límites declarados de la base: ver «Límites declarados» en `docs/BASE_DE_DATOS.md` (sin RLS, `timestamp` sin zona, institución como texto libre).
- [ ] Ocho archivos de prueba del backend importan `main.py`, que al importarse ejecuta `create_all` y los ajustes de arranque contra la base de `DB_*`: correr la suite siempre con `DB_NAME` apuntando a una base desechable.
- [ ] Con Node 25+ las pruebas del front fallan por el `localStorage` nativo de Node: correrlas con `NODE_OPTIONS=--no-experimental-webstorage`.
- [ ] El `venv` local tenía `bcrypt 5.0.0` (el proyecto fija `4.0.1`): reinstalar con `pip install -r requirements.txt`.
- [ ] ESLint del front: errores en archivos no tocados (deuda anterior).
- [ ] Los `.xlsx` de `e2e/fixtures` están ignorados por `.gitignore`: copiarlos del repo original para correr Playwright en otro lugar.
- [ ] Los CSV de relevancia se versionaron con `git add -f` (el `.gitignore` ignora `*.csv`).

## Rama
- [ ] Integrar `main` (3 commits: plantillas oficiales 549/550 y cambios del front) y volver a correr las pruebas, incluidas `tests/test_importacion_plantillas_pg.py`, que usan esas plantillas.
- [ ] Decidir cómo integrar: merge o PR hacia `main`. La rama `test/e2e-historias-usuario` tiene cambios sin confirmar: no tocarla.
