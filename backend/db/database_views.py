"""Creación de vistas SQL para morbilidad y mortalidad materna.

Las vistas son la fuente de lectura del dashboard y del listado SIVIGILA. Se recrean
en cada arranque (DROP + CREATE) para que siempre reflejen el esquema actual, incluida
la columna `secretaria_codigo` que aísla los datos por secretaría (tenant).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def sentencias_vistas() -> list[str]:
    """Devuelve las sentencias CREATE VIEW del esquema actual.

    Son tres: mortalidad, morbilidad y causas asociadas de morbilidad.
    """
    edad_morbilidad = 'EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer'
    edad_mortalidad = 'EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer'

    sql_mortalidad = f"""
    CREATE OR REPLACE VIEW v_mortalidad_completa AS
    SELECT
        c.id_caso,
        c.secretaria_codigo,
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
        ao.gestaciones,
        ao.partos_vaginales,
        ao.cesareas,
        ao.nacidos_muertos,
        ao.hijos_vivos,
        ao.abortos,
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
        ao.num_controles_prenatales AS num_cpn,
        ao.semana_inicio_cpn,
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
        cm.demora_4,
        zr.descripcion AS zona_residencia,
        pv.descripcion AS poblacion_vulnerable,
        et.descripcion AS etnia,
        ta.descripcion AS tipo_afiliacion
    FROM caso_mortalidad c
        LEFT JOIN paciente p ON p.id_paciente = c.id_paciente
        LEFT JOIN cat_tipo_id ti ON ti.id = p.id_tipo_id
        LEFT JOIN cat_sitio_defuncion sd ON sd.id = c.id_sitio_defuncion
        LEFT JOIN antecedente_materno_mortalidad am ON am.id_caso = c.id_caso
        LEFT JOIN cat_convivencia cv ON cv.id = am.id_convivencia
        LEFT JOIN cat_escolaridad es ON es.id = am.id_escolaridad
        LEFT JOIN antecedente_obstetrico ao ON ao.caso_mortalidad_id = c.id_caso
        LEFT JOIN cat_regulacion_fecundidad rf ON rf.id = ao.id_regulacion_fecundidad
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
        LEFT JOIN cat_fuente_causa_muerte fc ON fc.id = cm.id_fuente_causa
        LEFT JOIN datos_sociodemograficos ds ON ds.caso_mortalidad_id = c.id_caso
        LEFT JOIN cat_zona_residencia zr ON zr.id = ds.id_zona_residencia
        LEFT JOIN cat_poblacion_vulnerable pv ON pv.id = ds.id_poblacion_vulnerable
        LEFT JOIN cat_etnia et ON et.id = ds.id_etnia
        LEFT JOIN cat_tipo_afiliacion ta ON ta.id = ds.id_tipo_afiliacion;
    """

    sql_morbilidad = f"""
    CREATE OR REPLACE VIEW v_morbilidad_completa AS
    SELECT
        c.id_caso,
        c.secretaria_codigo,
        p.nombres_apellidos,
        ti.codigo AS tipo_id,
        p.numero_id,
        p.fecha_nacimiento,
        {edad_morbilidad} AS edad,
        c.fecha_egreso,
        r.remitida,
        ri1.institucion AS institucion_ref_1,
        r.tiempo_remision_h,
        ao.gestaciones AS num_gestaciones,
        ao.partos_vaginales,
        ao.cesareas,
        ao.abortos,
        ao.num_controles_prenatales,
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
        gc.descripcion AS grupo_causa,
        zr.descripcion AS zona_residencia,
        pv.descripcion AS poblacion_vulnerable,
        et.descripcion AS etnia,
        ta.descripcion AS tipo_afiliacion
    FROM caso_morbilidad c
        LEFT JOIN paciente p ON p.id_paciente = c.id_paciente
        LEFT JOIN cat_tipo_id ti ON ti.id = p.id_tipo_id
        LEFT JOIN referencia r ON r.id_caso = c.id_caso
        LEFT JOIN referencia_institucion ri1
            ON ri1.id_referencia = r.id_referencia AND ri1.orden = 1
        LEFT JOIN antecedente_obstetrico ao ON ao.caso_morbilidad_id = c.id_caso
        LEFT JOIN antecedente_obstetrico_morbilidad a ON a.id_caso = c.id_caso
        LEFT JOIN cat_terminacion_gestacion tg ON tg.id = a.id_terminacion_gestacion
        LEFT JOIN criterios_enfermedad ce ON ce.id_caso = c.id_caso
        LEFT JOIN criterios_falla_organica cf ON cf.id_caso = c.id_caso
        LEFT JOIN criterios_manejo cm ON cm.id_caso = c.id_caso
        LEFT JOIN manejo_hospitalario mh ON mh.id_caso = c.id_caso
        LEFT JOIN causas_morbilidad ca ON ca.id_caso = c.id_caso
        LEFT JOIN cat_grupo_causa gc ON gc.id = ca.id_grupo_causa
        LEFT JOIN datos_sociodemograficos ds ON ds.caso_morbilidad_id = c.id_caso
        LEFT JOIN cat_zona_residencia zr ON zr.id = ds.id_zona_residencia
        LEFT JOIN cat_poblacion_vulnerable pv ON pv.id = ds.id_poblacion_vulnerable
        LEFT JOIN cat_etnia et ON et.id = ds.id_etnia
        LEFT JOIN cat_tipo_afiliacion ta ON ta.id = ds.id_tipo_afiliacion;
    """

    # Causas asociadas: una fila por causa (1FN), con su descripción del catálogo CIE-10.
    sql_causas_asociadas = """
    CREATE OR REPLACE VIEW v_causa_asociada_morbilidad AS
    SELECT
        ca.id,
        ca.id_caso,
        c.secretaria_codigo,
        ca.orden,
        ca.cie10,
        cie.descripcion
    FROM causa_asociada_morbilidad ca
        JOIN caso_morbilidad c ON c.id_caso = ca.id_caso
        LEFT JOIN cie10 cie ON cie.codigo = ca.cie10;
    """

    return [sql_mortalidad.strip(), sql_morbilidad.strip(), sql_causas_asociadas.strip()]


# Vistas que crea este módulo (en orden de borrado).
VISTAS: tuple[str, ...] = (
    'v_causa_asociada_morbilidad',
    'v_morbilidad_completa',
    'v_mortalidad_completa',
)


def _retirar_tablas_con_nombre_de_vista(db: Session) -> None:
    """Quita una TABLA física vacía que ocupe el nombre de una vista.

    Versiones anteriores registraban las vistas en el mismo `MetaData` que las tablas, así que
    `create_all` sobre una base vacía las creaba como tablas vacías y la vista ya no se podía
    crear. Si esa tabla tiene filas no se toca (no se borra información): se lanza un error.

    Raises:
        RuntimeError: Si una tabla con nombre de vista tiene datos.
    """
    for nombre in VISTAS:
        tipo = db.execute(
            text(
                'SELECT c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace '
                'WHERE n.nspname = current_schema() AND c.relname = :n'
            ),
            {'n': nombre},
        ).scalar()
        if tipo != 'r':
            continue
        if db.execute(text(f'SELECT EXISTS (SELECT 1 FROM {nombre})')).scalar():
            raise RuntimeError(
                f'"{nombre}" es una tabla con datos y no una vista; revísela a mano antes de '
                'arrancar (no se borra automáticamente).'
            )
        db.execute(text(f'DROP TABLE {nombre}'))


def create_database_views(db: Session):
    """Crea o recrea las vistas SQL de morbilidad y mortalidad en la base de datos.

    Args:
        db: Sesión activa de SQLAlchemy.
    """
    if db.get_bind().dialect.name != 'postgresql':
        return  # las vistas usan funciones de PostgreSQL (AGE, EXTRACT)
    try:
        _retirar_tablas_con_nombre_de_vista(db)
        for nombre in VISTAS:
            db.execute(text(f'DROP VIEW IF EXISTS {nombre}'))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f'Advertencia: No se pudieron preparar las vistas: {e}')
        return

    try:
        for sentencia in sentencias_vistas():
            db.execute(text(sentencia))
        db.commit()
        print('Vistas de base de datos creadas/actualizadas correctamente.')
    except Exception as e:
        db.rollback()
        print(f'Advertencia: No se pudieron crear las vistas: {e}')
