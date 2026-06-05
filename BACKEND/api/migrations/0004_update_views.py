# Generated manually on 2026-05-26
# Updated 2026-06-05: compatible con SQLite y MySQL

from django.db import migrations


# ---------------------------------------------------------------------------
# Cuerpo de la vista de morbilidad (sin la cláusula CREATE)
# ---------------------------------------------------------------------------

_MORBILIDAD_BODY = """
    SELECT
        c.id_caso                    AS id_caso,
        p.nombres_apellidos          AS nombres_apellidos,
        ti.codigo                    AS tipo_id,
        p.numero_id                  AS numero_id,
        p.fecha_nacimiento           AS fecha_nacimiento,
        {edad_expr}                  AS edad,
        c.fecha_egreso               AS fecha_egreso,
        r.remitida                   AS remitida,
        r.institucion_ref_1          AS institucion_ref_1,
        r.tiempo_remision_h          AS tiempo_remision_h,
        a.num_gestaciones            AS num_gestaciones,
        a.partos_vaginales           AS partos_vaginales,
        a.cesareas                   AS cesareas,
        a.abortos                    AS abortos,
        a.num_controles_prenatales   AS num_controles_prenatales,
        a.edad_gestacional_sem       AS edad_gestacional_sem,
        tg.descripcion               AS terminacion_gestacion,
        a.estado_recien_nacido       AS estado_recien_nacido,
        a.peso_rn_gramos             AS peso_rn_gramos,
        ce.eclampsia                 AS eclampsia,
        ce.preeclampsia              AS preeclampsia,
        ce.hemorragia_obstetrica     AS hemorragia_obstetrica,
        ce.sepsis_sistemica_severa   AS sepsis_sistemica_severa,
        ce.ruptura_uterina           AS ruptura_uterina,
        cf.falla_cardiaca            AS falla_cardiaca,
        cf.falla_renal               AS falla_renal,
        cf.falla_hepatica            AS falla_hepatica,
        cf.falla_respiratoria        AS falla_respiratoria,
        cf.falla_coagulacion         AS falla_coagulacion,
        cm.ingreso_uci               AS ingreso_uci,
        cm.cirugia_adicional         AS cirugia_adicional,
        cm.transfusion               AS transfusion,
        cm.total_criterios           AS total_criterios,
        mh.dias_estancia_hosp        AS dias_estancia_hosp,
        mh.dias_estancia_uci         AS dias_estancia_uci,
        mh.unidades_transfundidas    AS unidades_transfundidas,
        ca.causa_principal_cie10     AS causa_principal_cie10,
        gc.descripcion               AS grupo_causa
    FROM caso_morbilidad c
    LEFT JOIN paciente p ON p.id_paciente = c.id_paciente
    LEFT JOIN cat_tipo_id ti ON ti.id = p.id_tipo_id
    LEFT JOIN referencia r ON r.id_caso = c.id_caso
    LEFT JOIN antecedentes_obstetricos a ON a.id_caso = c.id_caso
    LEFT JOIN cat_terminacion_gestacion tg ON tg.id = a.id_terminacion_gestacion
    LEFT JOIN criterios_enfermedad ce ON ce.id_caso = c.id_caso
    LEFT JOIN criterios_falla_organica cf ON cf.id_caso = c.id_caso
    LEFT JOIN criterios_manejo cm ON cm.id_caso = c.id_caso
    LEFT JOIN manejo_hospitalario mh ON mh.id_caso = c.id_caso
    LEFT JOIN causas_morbilidad ca ON ca.id_caso = c.id_caso
    LEFT JOIN cat_grupo_causa gc ON gc.id = ca.id_grupo_causa
"""

_MORTALIDAD_BODY = """
    SELECT
        c.id_caso                       AS id_caso,
        p.nombres_apellidos             AS nombres_apellidos,
        ti.codigo                       AS tipo_id,
        p.numero_id                     AS numero_id,
        p.fecha_nacimiento              AS fecha_nacimiento,
        {edad_expr}                     AS edad,
        sd.descripcion                  AS sitio_defuncion,
        c.fecha_defuncion               AS fecha_defuncion,
        cv.descripcion                  AS convivencia,
        am.otro_convivencia             AS otro_convivencia,
        es.descripcion                  AS escolaridad,
        rf.descripcion                  AS regulacion_fecundidad,
        am.gestaciones                  AS gestaciones,
        am.partos_vaginales             AS partos_vaginales,
        am.cesareas                     AS cesareas,
        am.nacidos_muertos              AS nacidos_muertos,
        am.hijos_vivos                  AS hijos_vivos,
        am.abortos                      AS abortos,
        ar.sin_antecedentes             AS sin_antecedentes,
        ar.hipertension_cronica         AS hipertension_cronica,
        ar.diabetes                     AS diabetes,
        ar.vih_sida                     AS vih_sida,
        ar.tabaquismo                   AS tabaquismo,
        ar.deficiencias_socioeconomicas AS deficiencias_socioeconomicas,
        ce.preeclampsia                 AS preeclampsia,
        ce.eclampsia                    AS eclampsia,
        ce.sindrome_hellp               AS sindrome_hellp,
        ce.sepsis                       AS sepsis,
        ce.hemorragia_3er_trimestre     AS hemorragia_3er_trimestre,
        ce.embarazo_no_deseado          AS embarazo_no_deseado,
        ce.violencia_gestante           AS violencia_gestante,
        cp.num_cpn                      AS num_cpn,
        cp.semana_inicio_cpn            AS semana_inicio_cpn,
        ps_cpn.descripcion              AS cpn_realizado_por,
        na_cpn.nivel                    AS nivel_atencion_cpn,
        re.descripcion                  AS remisiones_oportunas,
        cp.compl_feto_rn_cie10          AS compl_feto_rn_cie10,
        mm.descripcion                  AS momento_muerte,
        pp.semana_gestacion_muerte      AS semana_gestacion_muerte,
        pp.fecha_parto                  AS fecha_parto,
        pp.hora_parto                   AS hora_parto,
        tp.descripcion                  AS tipo_parto,
        ps_parto.descripcion            AS parto_atendido_por,
        na_parto.nivel                  AS nivel_atencion_parto,
        cm_causa.causa_basica_cie10     AS causa_basica_cie10,
        fc.descripcion                  AS fuente_causa_muerte,
        cm_causa.demora_1               AS demora_1,
        cm_causa.demora_2               AS demora_2,
        cm_causa.demora_3               AS demora_3,
        cm_causa.demora_4               AS demora_4
    FROM caso_mortalidad c
    LEFT JOIN paciente p ON p.id_paciente = c.id_paciente
    LEFT JOIN cat_tipo_id ti ON ti.id = p.id_tipo_id
    LEFT JOIN cat_sitio_defuncion sd ON sd.id = c.id_sitio_defuncion
    LEFT JOIN antecedente_materno am ON am.id_caso = c.id_caso
    LEFT JOIN cat_convivencia cv ON cv.id = am.id_convivencia
    LEFT JOIN cat_escolaridad es ON es.id = am.id_escolaridad
    LEFT JOIN cat_regulacion_fecundidad rf ON rf.id = am.id_regulacion_fec
    LEFT JOIN antecedente_riesgo ar ON ar.id_caso = c.id_caso
    LEFT JOIN complicacion_embarazo ce ON ce.id_caso = c.id_caso
    LEFT JOIN control_prenatal cp ON cp.id_caso = c.id_caso
    LEFT JOIN cat_personal_salud ps_cpn ON ps_cpn.id = cp.id_personal_cpn
    LEFT JOIN cat_nivel_atencion na_cpn ON na_cpn.id = cp.id_nivel_atencion_cpn
    LEFT JOIN cat_remisiones re ON re.id = cp.id_remisiones
    LEFT JOIN antecedente_parto_puerperio pp ON pp.id_caso = c.id_caso
    LEFT JOIN cat_momento_muerte mm ON mm.id = pp.id_momento_muerte
    LEFT JOIN cat_tipo_parto tp ON tp.id = pp.id_tipo_parto
    LEFT JOIN cat_personal_salud ps_parto ON ps_parto.id = pp.id_atendido_por
    LEFT JOIN cat_nivel_atencion na_parto ON na_parto.id = pp.id_nivel_atencion_parto
    LEFT JOIN causa_muerte cm_causa ON cm_causa.id_caso = c.id_caso
    LEFT JOIN cat_fuente_causa_muerte fc ON fc.id = cm_causa.id_fuente_causa
"""

# Expresiones de edad compatibles por motor de base de datos
_EDAD_MORBILIDAD_MYSQL = 'TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, c.fecha_egreso)'
_EDAD_MORTALIDAD_MYSQL = 'TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, c.fecha_defuncion)'

# PostgreSQL: usa AGE() que devuelve un intervalo, EXTRACT saca el año
_EDAD_MORBILIDAD_PG = (
    "CASE WHEN p.fecha_nacimiento IS NOT NULL AND c.fecha_egreso IS NOT NULL "
    "THEN EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::INTEGER "
    "ELSE NULL END"
)
_EDAD_MORTALIDAD_PG = (
    "CASE WHEN p.fecha_nacimiento IS NOT NULL AND c.fecha_defuncion IS NOT NULL "
    "THEN EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::INTEGER "
    "ELSE NULL END"
)

# SQLite: no soporta TIMESTAMPDIFF ni AGE; usa julianday
_EDAD_MORBILIDAD_SQLITE = (
    "CASE WHEN p.fecha_nacimiento IS NOT NULL AND c.fecha_egreso IS NOT NULL "
    "THEN CAST((julianday(c.fecha_egreso) - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER) "
    "ELSE NULL END"
)
_EDAD_MORTALIDAD_SQLITE = (
    "CASE WHEN p.fecha_nacimiento IS NOT NULL AND c.fecha_defuncion IS NOT NULL "
    "THEN CAST((julianday(c.fecha_defuncion) - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER) "
    "ELSE NULL END"
)


def _crear_vistas(schema_editor):
    """Crea las dos vistas usando sintaxis adaptada al motor de BD activo."""
    vendor = schema_editor.connection.vendor

    if vendor == 'mysql':
        edad_morb = _EDAD_MORBILIDAD_MYSQL
        edad_mort = _EDAD_MORTALIDAD_MYSQL
        schema_editor.execute(
            'CREATE OR REPLACE VIEW v_morbilidad_completa AS '
            + _MORBILIDAD_BODY.format(edad_expr=edad_morb)
        )
        schema_editor.execute(
            'CREATE OR REPLACE VIEW v_mortalidad_completa AS '
            + _MORTALIDAD_BODY.format(edad_expr=edad_mort)
        )
    elif vendor == 'postgresql':
        # PostgreSQL soporta CREATE OR REPLACE VIEW y AGE()
        edad_morb = _EDAD_MORBILIDAD_PG
        edad_mort = _EDAD_MORTALIDAD_PG
        schema_editor.execute(
            'CREATE OR REPLACE VIEW v_morbilidad_completa AS '
            + _MORBILIDAD_BODY.format(edad_expr=edad_morb)
        )
        schema_editor.execute(
            'CREATE OR REPLACE VIEW v_mortalidad_completa AS '
            + _MORTALIDAD_BODY.format(edad_expr=edad_mort)
        )
    else:
        # SQLite: no soporta CREATE OR REPLACE VIEW ni TIMESTAMPDIFF
        edad_morb = _EDAD_MORBILIDAD_SQLITE
        edad_mort = _EDAD_MORTALIDAD_SQLITE
        schema_editor.execute('DROP VIEW IF EXISTS v_morbilidad_completa')
        schema_editor.execute(
            'CREATE VIEW v_morbilidad_completa AS '
            + _MORBILIDAD_BODY.format(edad_expr=edad_morb)
        )
        schema_editor.execute('DROP VIEW IF EXISTS v_mortalidad_completa')
        schema_editor.execute(
            'CREATE VIEW v_mortalidad_completa AS '
            + _MORTALIDAD_BODY.format(edad_expr=edad_mort)
        )


def _eliminar_vistas(schema_editor):
    """Elimina las vistas al revertir la migración."""
    schema_editor.execute('DROP VIEW IF EXISTS v_morbilidad_completa')
    schema_editor.execute('DROP VIEW IF EXISTS v_mortalidad_completa')


def forward(apps, schema_editor):
    _crear_vistas(schema_editor)


def backward(apps, schema_editor):
    _eliminar_vistas(schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_analisis_archivo_hash'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
