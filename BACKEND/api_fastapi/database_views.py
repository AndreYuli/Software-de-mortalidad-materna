from sqlalchemy import text
from sqlalchemy.orm import Session

def create_database_views(db: Session, dialect: str):
    dialect = dialect.lower()
    
    # Age calculation logic depending on SQL dialect
    if "postgresql" in dialect or "postgres" in dialect:
        edad_morbilidad = "EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer"
        edad_mortalidad = "EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer"
    else:
        # SQLite (fallback para desarrollo local)
        edad_morbilidad = "CAST(strftime('%Y', c.fecha_egreso) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_egreso) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"
        edad_mortalidad = "CAST(strftime('%Y', c.fecha_defuncion) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_defuncion) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"

    # Drop existing views to recreate them correctly
    try:
        db.execute(text("DROP VIEW IF EXISTS v_morbilidad_completa"))
        db.execute(text("DROP VIEW IF EXISTS v_mortalidad_completa"))
        db.commit()
    except Exception:
        db.rollback()

    # View v_morbilidad_completa
    sql_morbilidad = f"""
    CREATE VIEW v_morbilidad_completa AS 
    select 
        c.id_caso AS id_caso,
        p.nombres_apellidos AS nombres_apellidos,
        ti.codigo AS tipo_id,
        p.numero_id AS numero_id,
        p.fecha_nacimiento AS fecha_nacimiento,
        {edad_morbilidad} AS edad,
        c.fecha_egreso AS fecha_egreso,
        r.remitida AS remitida,
        r.institucion_ref_1 AS institucion_ref_1,
        r.tiempo_remision_h AS tiempo_remision_h,
        a.num_gestaciones AS num_gestaciones,
        a.partos_vaginales AS partos_vaginales,
        a.cesareas AS cesareas,
        a.abortos AS abortos,
        a.num_controles_prenatales AS num_controles_prenatales,
        a.edad_gestacional_sem AS edad_gestacional_sem,
        tg.descripcion AS terminacion_gestacion,
        a.estado_recien_nacido AS estado_recien_nacido,
        a.peso_rn_gramos AS peso_rn_gramos,
        ce.eclampsia AS eclampsia,
        ce.preeclampsia AS preeclampsia,
        ce.hemorragia_obstetrica AS hemorragia_obstetrica,
        ce.sepsis_sistemica_severa AS sepsis_sistemica_severa,
        ce.ruptura_uterina AS ruptura_uterina,
        cf.falla_cardiaca AS falla_cardiaca,
        cf.falla_renal AS falla_renal,
        cf.falla_hepatica AS falla_hepatica,
        cf.falla_respiratoria AS falla_respiratoria,
        cf.falla_coagulacion AS falla_coagulacion,
        cm.ingreso_uci AS ingreso_uci,
        cm.cirugia_adicional AS cirugia_adicional,
        cm.transfusion AS transfusion,
        cm.total_criterios AS total_criterios,
        mh.dias_estancia_hosp AS dias_estancia_hosp,
        mh.dias_estancia_uci AS dias_estancia_uci,
        mh.unidades_transfundidas AS unidades_transfundidas,
        ca.causa_principal_cie10 AS causa_principal_cie10,
        gc.descripcion AS grupo_causa 
    from 
        caso_morbilidad c
        left join paciente p on p.id_paciente = c.id_paciente
        left join cat_tipo_id ti on ti.id = p.id_tipo_id
        left join referencia r on r.id_caso = c.id_caso
        left join antecedentes_obstetricos a on a.id_caso = c.id_caso
        left join cat_terminacion_gestacion tg on tg.id = a.id_terminacion_gestacion
        left join criterios_enfermedad ce on ce.id_caso = c.id_caso
        left join criterios_falla_organica cf on cf.id_caso = c.id_caso
        left join criterios_manejo cm on cm.id_caso = c.id_caso
        left join manejo_hospitalario mh on mh.id_caso = c.id_caso
        left join causas_morbilidad ca on ca.id_caso = c.id_caso
        left join cat_grupo_causa gc on gc.id = ca.id_grupo_causa;
    """

    # View v_mortalidad_completa
    sql_mortalidad = f"""
    CREATE VIEW v_mortalidad_completa AS 
    select 
        c.id_caso AS id_caso,
        p.nombres_apellidos AS nombres_apellidos,
        ti.codigo AS tipo_id,
        p.numero_id AS numero_id,
        p.fecha_nacimiento AS fecha_nacimiento,
        {edad_mortalidad} AS edad,
        sd.descripcion AS sitio_defuncion,
        c.fecha_defuncion AS fecha_defuncion,
        cv.descripcion AS convivencia,
        am.otro_convivencia AS otro_convivencia,
        es.descripcion AS escolaridad,
        rf.descripcion AS regulacion_fecundidad,
        am.gestaciones AS gestaciones,
        am.partos_vaginales AS partos_vaginales,
        am.cesareas AS cesareas,
        am.nacidos_muertos AS nacidos_muertos,
        am.hijos_vivos AS hijos_vivos,
        am.abortos AS abortos,
        ar.sin_antecedentes AS sin_antecedentes,
        ar.hipertension_cronica AS hipertension_cronica,
        ar.diabetes AS diabetes,
        ar.vih_sida AS vih_sida,
        ar.tabaquismo AS tabaquismo,
        ar.deficiencias_socioeconomicas AS deficiencias_socioeconomicas,
        ce.preeclampsia AS preeclampsia,
        ce.eclampsia AS eclampsia,
        ce.sindrome_hellp AS sindrome_hellp,
        ce.sepsis AS sepsis,
        ce.hemorragia_3er_trimestre AS hemorragia_3er_trimestre,
        ce.embarazo_no_deseado AS embarazo_no_deseado,
        ce.violencia_gestante AS violencia_gestante,
        cp.num_cpn AS num_cpn,
        cp.semana_inicio_cpn AS semana_inicio_cpn,
        ps_cpn.descripcion AS cpn_realizado_por,
        na_cpn.nivel AS nivel_atencion_cpn,
        re.descripcion AS remisiones_oportunas,
        cp.compl_feto_rn_cie10 AS compl_feto_rn_cie10,
        mm.descripcion AS momento_muerte,
        pp.semana_gestacion_muerte AS semana_gestacion_muerte,
        pp.fecha_parto AS fecha_parto,
        pp.hora_parto AS hora_parto,
        tp.descripcion AS tipo_parto,
        ps_parto.descripcion AS parto_atendido_por,
        na_parto.nivel AS nivel_atencion_parto,
        cm.causa_basica_cie10 AS causa_basica_cie10,
        fc.descripcion AS fuente_causa_muerte,
        cm.demora_1 AS demora_1,
        cm.demora_2 AS demora_2,
        cm.demora_3 AS demora_3,
        cm.demora_4 AS demora_4 
    from 
        caso_mortalidad c
        left join paciente p on p.id_paciente = c.id_paciente
        left join cat_tipo_id ti on ti.id = p.id_tipo_id
        left join cat_sitio_defuncion sd on sd.id = c.id_sitio_defuncion
        left join antecedente_materno am on am.id_caso = c.id_caso
        left join cat_convivencia cv on cv.id = am.id_convivencia
        left join cat_escolaridad es on es.id = am.id_escolaridad
        left join cat_regulacion_fecundidad rf on rf.id = am.id_regulacion_fec
        left join antecedente_riesgo ar on ar.id_caso = c.id_caso
        left join complicacion_embarazo ce on ce.id_caso = c.id_caso
        left join control_prenatal cp on cp.id_caso = c.id_caso
        left join cat_personal_salud ps_cpn on ps_cpn.id = cp.id_personal_cpn
        left join cat_nivel_atencion na_cpn on na_cpn.id = cp.id_nivel_atencion_cpn
        left join cat_remisiones re on re.id = cp.id_remisiones
        left join antecedente_parto_puerperio pp on pp.id_caso = c.id_caso
        left join cat_momento_muerte mm on mm.id = pp.id_momento_muerte
        left join cat_tipo_parto tp on tp.id = pp.id_tipo_parto
        left join cat_personal_salud ps_parto on ps_parto.id = pp.id_atendido_por
        left join cat_nivel_atencion na_parto on na_parto.id = pp.id_nivel_atencion_parto
        left join causa_muerte cm on cm.id_caso = c.id_caso
        left join cat_fuente_causa_muerte fc on fc.id = cm.id_fuente_causa;
    """

    try:
        db.execute(text(sql_morbilidad))
        db.execute(text(sql_mortalidad))
        db.commit()
        print("Database views created/updated successfully.")
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not create database views: {e}")
