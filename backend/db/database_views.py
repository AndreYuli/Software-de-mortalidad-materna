"""Creación de vistas SQL para morbilidad y mortalidad materna."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_database_views(db: Session):
    """Crea o recrea las vistas SQL de morbilidad y mortalidad en la base de datos.

    Args:
        db: Sesión activa de SQLAlchemy.
    """
    edad_morbilidad = 'EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer'
    edad_mortalidad = 'EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer'

    try:
        db.execute(text('DROP VIEW IF EXISTS v_morbilidad_completa'))
        db.execute(text('DROP VIEW IF EXISTS v_mortalidad_completa'))
        db.commit()
    except Exception:
        db.rollback()

    sql_morbilidad = f"""
    CREATE VIEW v_morbilidad_completa AS
    SELECT
        c.id_caso,
        p.nombres_apellidos,
        ti.codigo AS tipo_id,
        p.numero_id,
        p.fecha_nacimiento,
        {edad_morbilidad} AS edad,
        c.fecha_egreso,
        r.remitida,
        r.institucion_ref_1,
        r.tiempo_remision_h,
        a.num_gestaciones,
        a.partos_vaginales,
        a.cesareas,
        a.abortos,
        a.num_controles_prenatales,
        a.edad_gestacional_sem,
        tg.descripcion AS terminacion_gestacion,
        a.estado_recien_nacido,
        a.peso_rn_gramos,
        ce.eclampsia,
        ce.preeclampsia,
        ce.hemorragia_obstetrica,
        ce.sepsis_sistemica_severa,
        ce.ruptura_uterina,
        cf.falla_cardiaca,
        cf.falla_renal,
        cf.falla_hepatica,
        cf.falla_respiratoria,
        cf.falla_coagulacion,
        cm.ingreso_uci,
        cm.cirugia_adicional,
        cm.transfusion,
        cm.total_criterios,
        mh.dias_estancia_hosp,
        mh.dias_estancia_uci,
        mh.unidades_transfundidas,
        ca.causa_principal_cie10,
        gc.descripcion AS grupo_causa
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
        LEFT JOIN cat_grupo_causa gc ON gc.id = ca.id_grupo_causa;
    """

    sql_mortalidad = f"""
    CREATE VIEW v_mortalidad_completa AS
    SELECT
        c.id_caso,
        p.nombres_apellidos,
        ti.codigo AS tipo_id,
        p.numero_id,
        p.fecha_nacimiento,
        {edad_mortalidad} AS edad,
        sd.descripcion AS sitio_defuncion,
        c.fecha_defuncion,
        cv.descripcion AS convivencia,
        am.otro_convivencia,
        es.descripcion AS escolaridad,
        rf.descripcion AS regulacion_fecundidad,
        am.gestaciones,
        am.partos_vaginales,
        am.cesareas,
        am.nacidos_muertos,
        am.hijos_vivos,
        am.abortos,
        ar.sin_antecedentes,
        ar.hipertension_cronica,
        ar.diabetes,
        ar.vih_sida,
        ar.tabaquismo,
        ar.deficiencias_socioeconomicas,
        ce.preeclampsia,
        ce.eclampsia,
        ce.sindrome_hellp,
        ce.sepsis,
        ce.hemorragia_3er_trimestre,
        ce.embarazo_no_deseado,
        ce.violencia_gestante,
        cp.num_cpn,
        cp.semana_inicio_cpn,
        ps_cpn.descripcion AS cpn_realizado_por,
        na_cpn.nivel AS nivel_atencion_cpn,
        re.descripcion AS remisiones_oportunas,
        cp.compl_feto_rn_cie10,
        mm.descripcion AS momento_muerte,
        pp.semana_gestacion_muerte,
        pp.fecha_parto,
        pp.hora_parto,
        tp.descripcion AS tipo_parto,
        ps_parto.descripcion AS parto_atendido_por,
        na_parto.nivel AS nivel_atencion_parto,
        cm.causa_basica_cie10,
        fc.descripcion AS fuente_causa_muerte,
        cm.demora_1,
        cm.demora_2,
        cm.demora_3,
        cm.demora_4
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
        LEFT JOIN causa_muerte cm ON cm.id_caso = c.id_caso
        LEFT JOIN cat_fuente_causa_muerte fc ON fc.id = cm.id_fuente_causa;
    """

    try:
        db.execute(text(sql_morbilidad))
        db.execute(text(sql_mortalidad))
        db.commit()
        print('Vistas de base de datos creadas/actualizadas correctamente.')
    except Exception as e:
        db.rollback()
        print(f'Advertencia: No se pudieron crear las vistas: {e}')
