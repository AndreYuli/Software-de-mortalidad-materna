-- Datos sintéticos con la estructura de main (tests/fixtures/esquema_main_legado.sql) para
-- probar scripts/migrar_estructura_anterior.py. Incluyen a propósito los casos difíciles:
-- CIE-10 con punto y en minúscula, «—», códigos inexistentes, causa asociada que repite la
-- principal, institución 2 igual a la 1, complicación del feto inválida y creado_en nulo.
SET search_path TO public;

INSERT INTO api_usuario (id, nombre, email, password_hash, fecha_registro, departamento,
                         secretaria, secretaria_codigo)
VALUES (1, 'Ana Analista', 'ana@bello.gov.co', 'x', '2026-01-01', 'Antioquia',
        'Secretaría de Salud de Bello', 'bello'),
       (2, 'Beto', 'beto@envigado.gov.co', 'x', '2026-01-02', 'Antioquia',
        'Secretaria Envigado (texto viejo)', 'envigado');

INSERT INTO paciente (id_paciente, nombres_apellidos, id_tipo_id, numero_id, fecha_nacimiento,
                      creado_en)
OVERRIDING SYSTEM VALUE VALUES
    (1, 'Paciente Uno', 1, '1001', '1995-03-01', '2026-02-01'),
    (2, 'Paciente Dos', 1, '1002', '1988-07-15', NULL),
    (3, 'Paciente Tres', 1, '1003', '1990-10-10', '2026-02-03'),
    (4, 'Paciente Cuatro', 1, '1004', '1985-01-20', '2026-02-04');

INSERT INTO caso_morbilidad (id_caso, id_paciente, fecha_egreso, creado_en, secretaria_codigo)
OVERRIDING SYSTEM VALUE VALUES
    (10, 1, '2026-02-10', '2026-02-11', 'bello'),
    (11, 2, '2026-03-05', '2026-03-06', 'bello');

INSERT INTO caso_mortalidad (id_caso, id_paciente, id_sitio_defuncion, fecha_defuncion,
                             creado_en, secretaria_codigo)
OVERRIDING SYSTEM VALUE VALUES
    (20, 3, 1, '2026-04-01', '2026-04-02', 'bello'),
    (21, 4, 6, '2026-04-15', '2026-04-16', 'envigado');

INSERT INTO api_analisis (id, tipo, nombre_archivo, archivo_hash, archivo, fecha_carga,
                          total_registros, resumen, secretaria_codigo)
VALUES (5, 'morbilidad', 'morb.xlsx', 'h1', 'media/morb.xlsx', '2026-02-12', 2, '{}', 'bello'),
       (6, 'mortalidad', 'mort.xlsx', 'h2', 'media/mort.xlsx', '2026-04-03', 2, '{}', 'bello');

INSERT INTO narrativa_ia (id, analisis_id, tipo_narrativa, filtros_hash, contenido, modelo,
                          generado_en)
VALUES (7, 5, 'resumen_ejecutivo', 'f1', 'Texto', 'modelo-x', '2026-02-13');

INSERT INTO api_sivigilaimportacion (id, tipo, row_hash, event_hash, caso_id, numero_id,
                                     tipo_identificacion, creado_en, secretaria_codigo)
VALUES (30, 'morbilidad', 'r1', 'e1', 10, '1001', 'CC', '2026-02-11', 'bello'),
       (31, 'morbilidad', 'r2', 'e2', 11, '1002', 'CC', '2026-03-06', 'bello'),
       (32, 'mortalidad', 'r3', 'e3', 20, '1003', 'CC', '2026-04-02', 'bello'),
       (33, 'mortalidad', 'r4', 'e4', 21, '1004', 'CC', '2026-04-16', 'envigado');

-- Morbilidad --------------------------------------------------------------------------------
INSERT INTO antecedentes_obstetricos (id_antecedente, id_caso, num_gestaciones,
    partos_vaginales, cesareas, abortos, molas, ectopicos, muertos, vivos,
    fecha_ultima_gestacion, id_regulacion_fecundidad, num_controles_prenatales,
    semanas_inicio_cpn, id_terminacion_gestacion, edad_gestacional_sem, momento_ocurrencia,
    estado_recien_nacido, multiplicidad, peso_rn_gramos)
OVERRIDING SYSTEM VALUE VALUES
    (40, 10, 3, 1, 1, 1, 0, 0, 0, 2, '2024-05-01', 2, 6, 9, 4, 36, 'Durante', 'Vivo', false, 2900),
    (41, 11, 1, 0, 0, 0, 1, 1, 1, 0, NULL, 1, 0, NULL, 1, 12, 'Antes', NULL, NULL, NULL);

INSERT INTO causas_morbilidad (id_causa, id_caso, causa_principal_cie10, id_grupo_causa,
                               causa_asociada_2, causa_asociada_3, causa_asociada_4)
OVERRIDING SYSTEM VALUE VALUES
    -- principal con punto; asociada en minúscula con punto; «—»; asociada = principal
    (50, 10, 'O14.1', 1, 'o72.1', '—', 'O141'),
    -- asociada inexistente; vacía; válida en la tercera posición
    (51, 11, 'O150', 2, 'Z99.99X', NULL, 'O72.1');

INSERT INTO referencia (id_referencia, id_caso, remitida, institucion_ref_1, institucion_ref_2,
                        tiempo_remision_h)
OVERRIDING SYSTEM VALUE VALUES
    (60, 10, true, 'Hospital A', ' hospital a ', 4.5),
    (61, 11, true, 'Clínica Uno', 'Puesto Dos', NULL);

INSERT INTO manejo_hospitalario (id_manejo, id_caso, dias_estancia_hosp, dias_estancia_uci,
    unidades_transfundidas, cirugia_1, cirugia_1_cual, cirugia_2, cirugia_2_cual)
OVERRIDING SYSTEM VALUE VALUES
    (70, 10, 5, 2, 3, 1, 'Total', 4, 'Otra cirugía'),
    (71, 11, 2, NULL, NULL, NULL, NULL, 3, NULL);

INSERT INTO datos_sociodemograficos (id, caso_morbilidad_id, caso_mortalidad_id,
    id_zona_residencia, id_poblacion_vulnerable, id_etnia, id_tipo_afiliacion)
OVERRIDING SYSTEM VALUE VALUES
    (80, 10, NULL, 1, 1, 1, 1),
    (81, NULL, 20, 2, 1, 1, 2);

-- Mortalidad --------------------------------------------------------------------------------
INSERT INTO antecedente_materno (id_caso, id_convivencia, otro_convivencia, id_escolaridad,
    id_regulacion_fec, gestaciones, partos_vaginales, cesareas, nacidos_muertos, hijos_vivos,
    abortos)
VALUES (20, 1, NULL, 2, 3, 4, 2, 1, 0, 3, 1);

INSERT INTO control_prenatal (id_caso, num_cpn, semana_inicio_cpn, id_personal_cpn,
                              id_nivel_atencion_cpn, id_remisiones, compl_feto_rn_cie10)
VALUES (20, 5, 11, 1, 1, 1, 'p00.0'),
       -- caso sin antecedente_materno; complicación del feto que no es un código
       (21, 2, NULL, NULL, NULL, 2, 'Ninguna');

INSERT INTO causa_muerte (id_caso, causa_basica_cie10, id_fuente_causa, demora_1, demora_2,
                          demora_3, demora_4)
VALUES (20, 'O72.1', 1, true, false, false, false),
       (21, 'o85', 1, false, true, false, false);
