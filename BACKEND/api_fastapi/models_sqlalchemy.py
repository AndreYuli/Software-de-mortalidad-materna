# Generated SQLAlchemy models from Django models
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Date, Time, Numeric, Boolean, JSON, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Analisis(Base):
    __tablename__ = "api_analisis"
    """Representa un analisis cargado desde archivo.

    Attributes:
        tipo: Tipo de analisis (mortalidad o morbilidad).
        nombre_archivo: Nombre del archivo cargado.
        archivo_hash: Hash del archivo para trazabilidad y deteccion de duplicados.
        archivo: Archivo fisico almacenado en media.
        fecha_carga: Fecha y hora de carga.
        total_registros: Cantidad total de registros procesados.
        resumen: Metadatos de resumen del proceso de analisis."""

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    archivo_hash = Column(String(64), nullable=False)
    archivo = Column(String(255), nullable=False)
    fecha_carga = Column(DateTime, nullable=False)
    total_registros = Column(Integer, nullable=False)
    resumen = Column(JSON, nullable=False)


class SivigilaImportacion(Base):
    __tablename__ = "api_sivigilaimportacion"
    """Registra eventos de importacion procesados desde SIVIGILA.

    Attributes:
        tipo: Tipo de evento importado.
        row_hash: Hash unico de la fila para deduplicacion.
        event_hash: Hash del evento para agrupacion y consulta.
        caso_id: Identificador interno del caso.
        numero_id: Numero de identificacion de la persona.
        tipo_identificacion: Tipo de documento de identificacion.
        creado_en: Fecha y hora de creacion del registro."""

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)
    row_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)
    caso_id = Column(Integer, nullable=False)
    numero_id = Column(String(30), nullable=False)
    tipo_identificacion = Column(String(5), nullable=False)
    creado_en = Column(DateTime, nullable=False)


class Usuario(Base):
    __tablename__ = "api_usuario"
    """Almacena usuarios del sistema con credenciales en hash.

    Attributes:
        nombre: Nombre completo del usuario.
        email: Correo electronico unico del usuario.
        password_hash: Hash de la contrasena del usuario.
        fecha_registro: Fecha y hora de registro en el sistema."""

    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(254), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False)


class CatConvivencia(Base):
    __tablename__ = "cat_convivencia"
    """CatConvivencia(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatEscolaridad(Base):
    __tablename__ = "cat_escolaridad"
    """CatEscolaridad(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatFuenteCausaMuerte(Base):
    __tablename__ = "cat_fuente_causa_muerte"
    """CatFuenteCausaMuerte(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatGrupoCausa(Base):
    __tablename__ = "cat_grupo_causa"
    """CatGrupoCausa(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(60), nullable=False)


class CatMomentoMuerte(Base):
    __tablename__ = "cat_momento_muerte"
    """CatMomentoMuerte(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatNivelAtencion(Base):
    __tablename__ = "cat_nivel_atencion"
    """CatNivelAtencion(id, nivel)"""

    id = Column(Integer, primary_key=True)
    nivel = Column(String(3), nullable=False)


class CatPersonalSalud(Base):
    __tablename__ = "cat_personal_salud"
    """CatPersonalSalud(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatRegulacionFecundidad(Base):
    __tablename__ = "cat_regulacion_fecundidad"
    """CatRegulacionFecundidad(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(50), nullable=False)


class CatRemisiones(Base):
    __tablename__ = "cat_remisiones"
    """CatRemisiones(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(15), nullable=False)


class CatSitioDefuncion(Base):
    __tablename__ = "cat_sitio_defuncion"
    """CatSitioDefuncion(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(60), nullable=False)


class CatTerminacionGestacion(Base):
    __tablename__ = "cat_terminacion_gestacion"
    """CatTerminacionGestacion(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatTipoId(Base):
    __tablename__ = "cat_tipo_id"
    """CatTipoId(id, codigo, descripcion)"""

    id = Column(Integer, primary_key=True)
    codigo = Column(String(5), nullable=False)
    descripcion = Column(String(50), nullable=False)


class CatTipoParto(Base):
    __tablename__ = "cat_tipo_parto"
    """CatTipoParto(id, descripcion)"""

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(20), nullable=False)


class Paciente(Base):
    __tablename__ = "paciente"
    """Paciente(id_paciente, nombres_apellidos, id_tipo, numero_id, fecha_nacimiento, creado_en)"""

    id_paciente = Column(Integer, index=True, primary_key=True, autoincrement=True)
    nombres_apellidos = Column(String(200), nullable=False)
    id_tipo_id = Column(Integer, ForeignKey('cat_tipo_id.id'))
    numero_id = Column(String(30), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)


class CasoMorbilidad(Base):
    __tablename__ = "caso_morbilidad"
    """CasoMorbilidad(id_caso, id_paciente, fecha_egreso, creado_en)"""

    id_caso = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'))
    fecha_egreso = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)


class Referencia(Base):
    __tablename__ = "referencia"
    """Referencia(id_referencia, id_caso, remitida, institucion_ref_1, institucion_ref_2, tiempo_remision_h)"""

    id_referencia = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    remitida = Column(Integer, nullable=False)
    institucion_ref_1 = Column(String(200), nullable=True)
    institucion_ref_2 = Column(String(200), nullable=True)
    tiempo_remision_h = Column(Numeric(precision=6, scale=1), nullable=True)


class AntecedentesObstetricos(Base):
    __tablename__ = "antecedentes_obstetricos"
    """AntecedentesObstetricos(id_antecedente, id_caso, num_gestaciones, partos_vaginales, cesareas, abortos, molas, ectopicos, muertos, vivos, fecha_ultima_gestacion, id_regulacion_fecundidad, num_controles_prenatales, semanas_inicio_cpn, id_terminacion_gestacion, edad_gestacional_sem, momento_ocurrencia, estado_recien_nacido, multiplicidad, peso_rn_gramos)"""

    id_antecedente = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    num_gestaciones = Column(Integer, nullable=True)
    partos_vaginales = Column(Integer, nullable=True)
    cesareas = Column(Integer, nullable=True)
    abortos = Column(Integer, nullable=True)
    molas = Column(Integer, nullable=True)
    ectopicos = Column(Integer, nullable=True)
    muertos = Column(Integer, nullable=True)
    vivos = Column(Integer, nullable=True)
    fecha_ultima_gestacion = Column(Date, nullable=True)
    id_regulacion_fecundidad = Column(Integer, ForeignKey('cat_regulacion_fecundidad.id'))
    num_controles_prenatales = Column(Integer, nullable=True)
    semanas_inicio_cpn = Column(Integer, nullable=True)
    id_terminacion_gestacion = Column(Integer, ForeignKey('cat_terminacion_gestacion.id'))
    edad_gestacional_sem = Column(Integer, nullable=True)
    momento_ocurrencia = Column(String(7), nullable=True)
    estado_recien_nacido = Column(String(6), nullable=True)
    multiplicidad = Column(Integer, nullable=True)
    peso_rn_gramos = Column(Integer, nullable=True)


class CriteriosEnfermedad(Base):
    __tablename__ = "criterios_enfermedad"
    """CriteriosEnfermedad(id_criterio_enf, id_caso, eclampsia, sepsis_sistemica_severa, hemorragia_obstetrica, preeclampsia, ruptura_uterina, aborto_septico, embarazo_ectopico, autoinmune, hematologica, oncologica, endocrino_metabolicas, renales, gastrointestinales, tromboembolicos, cardiocerebrovasculares, otras_enfermedades)"""

    id_criterio_enf = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    eclampsia = Column(Integer, nullable=False)
    sepsis_sistemica_severa = Column(Integer, nullable=False)
    hemorragia_obstetrica = Column(Integer, nullable=False)
    preeclampsia = Column(Integer, nullable=False)
    ruptura_uterina = Column(Integer, nullable=False)
    aborto_septico = Column(Integer, nullable=False)
    embarazo_ectopico = Column(Integer, nullable=False)
    autoinmune = Column(Integer, nullable=False)
    hematologica = Column(Integer, nullable=False)
    oncologica = Column(Integer, nullable=False)
    endocrino_metabolicas = Column(Integer, nullable=False)
    renales = Column(Integer, nullable=False)
    gastrointestinales = Column(Integer, nullable=False)
    tromboembolicos = Column(Integer, nullable=False)
    cardiocerebrovasculares = Column(Integer, nullable=False)
    otras_enfermedades = Column(Integer, nullable=False)


class CriteriosFallaOrganica(Base):
    __tablename__ = "criterios_falla_organica"
    """CriteriosFallaOrganica(id_criterio_falla, id_caso, falla_cardiaca, falla_vascular, falla_renal, falla_hepatica, falla_metabolica, falla_cerebral, falla_respiratoria, falla_coagulacion)"""

    id_criterio_falla = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    falla_cardiaca = Column(Integer, nullable=False)
    falla_vascular = Column(Integer, nullable=False)
    falla_renal = Column(Integer, nullable=False)
    falla_hepatica = Column(Integer, nullable=False)
    falla_metabolica = Column(Integer, nullable=False)
    falla_cerebral = Column(Integer, nullable=False)
    falla_respiratoria = Column(Integer, nullable=False)
    falla_coagulacion = Column(Integer, nullable=False)


class CriteriosManejo(Base):
    __tablename__ = "criterios_manejo"
    """CriteriosManejo(id_criterio_manejo, id_caso, ingreso_uci, cirugia_adicional, transfusion, total_criterios, accidente, intoxicacion_accidental, intento_suicida, victima_violencia, otros_eventos_sp, cual_evento_sp)"""

    id_criterio_manejo = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    ingreso_uci = Column(Integer, nullable=False)
    cirugia_adicional = Column(Integer, nullable=False)
    transfusion = Column(Integer, nullable=False)
    total_criterios = Column(Integer, nullable=True)
    accidente = Column(Integer, nullable=False)
    intoxicacion_accidental = Column(Integer, nullable=False)
    intento_suicida = Column(Integer, nullable=False)
    victima_violencia = Column(Integer, nullable=False)
    otros_eventos_sp = Column(Integer, nullable=False)
    cual_evento_sp = Column(String(200), nullable=True)


class ManejoHospitalario(Base):
    __tablename__ = "manejo_hospitalario"
    """ManejoHospitalario(id_manejo, id_caso, dias_estancia_hosp, dias_estancia_uci, unidades_transfundidas, cirugia_1, cirugia_1_cual, cirugia_2, cirugia_2_cual)"""

    id_manejo = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    dias_estancia_hosp = Column(Integer, nullable=True)
    dias_estancia_uci = Column(Integer, nullable=True)
    unidades_transfundidas = Column(Integer, nullable=True)
    cirugia_1 = Column(Integer, nullable=True)
    cirugia_1_cual = Column(String(200), nullable=True)
    cirugia_2 = Column(Integer, nullable=True)
    cirugia_2_cual = Column(String(200), nullable=True)


class CausasMorbilidad(Base):
    __tablename__ = "causas_morbilidad"
    """CausasMorbilidad(id_causa, id_caso, causa_principal_cie10, id_grupo_causa, causa_asociada_2, causa_asociada_3, causa_asociada_4)"""

    id_causa = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    causa_principal_cie10 = Column(String(10), nullable=False)
    id_grupo_causa = Column(Integer, ForeignKey('cat_grupo_causa.id'))
    causa_asociada_2 = Column(String(10), nullable=True)
    causa_asociada_3 = Column(String(10), nullable=True)
    causa_asociada_4 = Column(String(10), nullable=True)


class CasoMortalidad(Base):
    __tablename__ = "caso_mortalidad"
    """CasoMortalidad(id_caso, id_paciente, id_sitio_defuncion, fecha_defuncion, creado_en)"""

    id_caso = Column(Integer, index=True, primary_key=True, autoincrement=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'))
    id_sitio_defuncion = Column(Integer, ForeignKey('cat_sitio_defuncion.id'))
    fecha_defuncion = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)


class AntecedenteMaterno(Base):
    __tablename__ = "antecedente_materno"
    """AntecedenteMaterno(id_caso, id_convivencia, otro_convivencia, id_escolaridad, id_regulacion_fec, gestaciones, partos_vaginales, cesareas, nacidos_muertos, hijos_vivos, abortos)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    id_convivencia = Column(Integer, ForeignKey('cat_convivencia.id'))
    otro_convivencia = Column(String(100), nullable=True)
    id_escolaridad = Column(Integer, ForeignKey('cat_escolaridad.id'))
    id_regulacion_fec = Column(Integer, ForeignKey('cat_regulacion_fecundidad.id'))
    gestaciones = Column(Integer, nullable=True)
    partos_vaginales = Column(Integer, nullable=True)
    cesareas = Column(Integer, nullable=True)
    nacidos_muertos = Column(Integer, nullable=True)
    hijos_vivos = Column(Integer, nullable=True)
    abortos = Column(Integer, nullable=True)


class AntecedenteRiesgo(Base):
    __tablename__ = "antecedente_riesgo"
    """AntecedenteRiesgo(id_caso, sin_antecedentes, hipertension_cronica, cardiopatias, diabetes, mola_hidatiforme, rn_pretermino, rn_bajo_peso, rn_macrosomico, trastorno_mental, obesidad, desnutricion_cronica, intergenesis_menor_2a, its_distintas, vih_sida, otras_infecciones, rh_negativo, tabaquismo, alcoholismo, sustancias_psicoactivas, deficiencias_socioeconomicas, sifilis, hepatitis_b, otros_factores_riesgo, desc_otros_factores, gingivitis_periodontitis)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    sin_antecedentes = Column(Integer, nullable=False)
    hipertension_cronica = Column(Integer, nullable=False)
    cardiopatias = Column(Integer, nullable=False)
    diabetes = Column(Integer, nullable=False)
    mola_hidatiforme = Column(Integer, nullable=False)
    rn_pretermino = Column(Integer, nullable=False)
    rn_bajo_peso = Column(Integer, nullable=False)
    rn_macrosomico = Column(Integer, nullable=False)
    trastorno_mental = Column(Integer, nullable=False)
    obesidad = Column(Integer, nullable=False)
    desnutricion_cronica = Column(Integer, nullable=False)
    intergenesis_menor_2a = Column(Integer, nullable=False)
    its_distintas = Column(Integer, nullable=False)
    vih_sida = Column(Integer, nullable=False)
    otras_infecciones = Column(Integer, nullable=False)
    rh_negativo = Column(Integer, nullable=False)
    tabaquismo = Column(Integer, nullable=False)
    alcoholismo = Column(Integer, nullable=False)
    sustancias_psicoactivas = Column(Integer, nullable=False)
    deficiencias_socioeconomicas = Column(Integer, nullable=False)
    sifilis = Column(Integer, nullable=False)
    hepatitis_b = Column(Integer, nullable=False)
    otros_factores_riesgo = Column(Integer, nullable=False)
    desc_otros_factores = Column(String(300), nullable=True)
    gingivitis_periodontitis = Column(Integer, nullable=False)


class ComplicacionEmbarazo(Base):
    __tablename__ = "complicacion_embarazo"
    """ComplicacionEmbarazo(id_caso, preeclampsia, eclampsia, sindrome_hellp, diabetes_gestacional, sepsis, hemorragia_1er_trimestre, hemorragia_2do_trimestre, hemorragia_3er_trimestre, desproporcion_cefalo_pelv, retardo_crecimiento_iu, enfermedad_autoinmune, malaria, embarazo_no_deseado, violencia_gestante, otras_complicaciones, desc_otras_complicaciones, gestacion_violencia_sexual, feto_incompatible_vida, sintomas_depresivos)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    preeclampsia = Column(Integer, nullable=False)
    eclampsia = Column(Integer, nullable=False)
    sindrome_hellp = Column(Integer, nullable=False)
    diabetes_gestacional = Column(Integer, nullable=False)
    sepsis = Column(Integer, nullable=False)
    hemorragia_1er_trimestre = Column(Integer, nullable=False)
    hemorragia_2do_trimestre = Column(Integer, nullable=False)
    hemorragia_3er_trimestre = Column(Integer, nullable=False)
    desproporcion_cefalo_pelv = Column(Integer, nullable=False)
    retardo_crecimiento_iu = Column(Integer, nullable=False)
    enfermedad_autoinmune = Column(Integer, nullable=False)
    malaria = Column(Integer, nullable=False)
    embarazo_no_deseado = Column(Integer, nullable=False)
    violencia_gestante = Column(Integer, nullable=False)
    otras_complicaciones = Column(Integer, nullable=False)
    desc_otras_complicaciones = Column(String(300), nullable=True)
    gestacion_violencia_sexual = Column(Integer, nullable=False)
    feto_incompatible_vida = Column(Integer, nullable=False)
    sintomas_depresivos = Column(Integer, nullable=False)


class ControlPrenatal(Base):
    __tablename__ = "control_prenatal"
    """ControlPrenatal(id_caso, num_cpn, semana_inicio_cpn, id_personal_cpn, id_nivel_atencion_cpn, id_remisiones, compl_feto_rn_cie10)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    num_cpn = Column(Integer, nullable=True)
    semana_inicio_cpn = Column(Integer, nullable=True)
    id_personal_cpn = Column(Integer, ForeignKey('cat_personal_salud.id'))
    id_nivel_atencion_cpn = Column(Integer, ForeignKey('cat_nivel_atencion.id'))
    id_remisiones = Column(Integer, ForeignKey('cat_remisiones.id'))
    compl_feto_rn_cie10 = Column(String(10), nullable=True)


class AntecedentePartoPuerperio(Base):
    __tablename__ = "antecedente_parto_puerperio"
    """AntecedentePartoPuerperio(id_caso, id_momento_muerte, semana_gestacion_muerte, fecha_parto, hora_parto, id_tipo_parto, id_atendido_por, otro_atencion_parto, id_nivel_atencion_parto)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    id_momento_muerte = Column(Integer, ForeignKey('cat_momento_muerte.id'))
    semana_gestacion_muerte = Column(Integer, nullable=True)
    fecha_parto = Column(Date, nullable=True)
    hora_parto = Column(Time, nullable=True)
    id_tipo_parto = Column(Integer, ForeignKey('cat_tipo_parto.id'))
    id_atendido_por = Column(Integer, ForeignKey('cat_personal_salud.id'))
    otro_atencion_parto = Column(String(100), nullable=True)
    id_nivel_atencion_parto = Column(Integer, ForeignKey('cat_nivel_atencion.id'))


class CausaMuerte(Base):
    __tablename__ = "causa_muerte"
    """CausaMuerte(id_caso, causa_basica_cie10, id_fuente_causa, demora_1, demora_2, demora_3, demora_4)"""

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    causa_basica_cie10 = Column(String(10), nullable=False)
    id_fuente_causa = Column(Integer, ForeignKey('cat_fuente_causa_muerte.id'))
    demora_1 = Column(Integer, nullable=False)
    demora_2 = Column(Integer, nullable=False)
    demora_3 = Column(Integer, nullable=False)
    demora_4 = Column(Integer, nullable=False)


class VMorbilidadCompleta(Base):
    __tablename__ = "v_morbilidad_completa"
    """VMorbilidadCompleta(id_caso, nombres_apellidos, tipo_id, numero_id, fecha_nacimiento, edad, fecha_egreso, remitida, institucion_ref_1, tiempo_remision_h, num_gestaciones, partos_vaginales, cesareas, abortos, num_controles_prenatales, edad_gestacional_sem, terminacion_gestacion, estado_recien_nacido, peso_rn_gramos, eclampsia, preeclampsia, hemorragia_obstetrica, sepsis_sistemica_severa, ruptura_uterina, falla_cardiaca, falla_renal, falla_hepatica, falla_respiratoria, falla_coagulacion, ingreso_uci, cirugia_adicional, transfusion, total_criterios, dias_estancia_hosp, dias_estancia_uci, unidades_transfundidas, causa_principal_cie10, grupo_causa)"""

    id_caso = Column(Integer, primary_key=True)
    nombres_apellidos = Column(String(200), nullable=True)
    tipo_id = Column(String(5), nullable=True)
    numero_id = Column(String(30), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    edad = Column(Integer, nullable=True)
    fecha_egreso = Column(Date, nullable=True)
    remitida = Column(Integer, nullable=True)
    institucion_ref_1 = Column(String(200), nullable=True)
    tiempo_remision_h = Column(Numeric(precision=6, scale=1), nullable=True)
    num_gestaciones = Column(Integer, nullable=True)
    partos_vaginales = Column(Integer, nullable=True)
    cesareas = Column(Integer, nullable=True)
    abortos = Column(Integer, nullable=True)
    num_controles_prenatales = Column(Integer, nullable=True)
    edad_gestacional_sem = Column(Integer, nullable=True)
    terminacion_gestacion = Column(String(30), nullable=True)
    estado_recien_nacido = Column(String(6), nullable=True)
    peso_rn_gramos = Column(Integer, nullable=True)
    eclampsia = Column(Integer, nullable=True)
    preeclampsia = Column(Integer, nullable=True)
    hemorragia_obstetrica = Column(Integer, nullable=True)
    sepsis_sistemica_severa = Column(Integer, nullable=True)
    ruptura_uterina = Column(Integer, nullable=True)
    falla_cardiaca = Column(Integer, nullable=True)
    falla_renal = Column(Integer, nullable=True)
    falla_hepatica = Column(Integer, nullable=True)
    falla_respiratoria = Column(Integer, nullable=True)
    falla_coagulacion = Column(Integer, nullable=True)
    ingreso_uci = Column(Integer, nullable=True)
    cirugia_adicional = Column(Integer, nullable=True)
    transfusion = Column(Integer, nullable=True)
    total_criterios = Column(Integer, nullable=True)
    dias_estancia_hosp = Column(Integer, nullable=True)
    dias_estancia_uci = Column(Integer, nullable=True)
    unidades_transfundidas = Column(Integer, nullable=True)
    causa_principal_cie10 = Column(String(10), nullable=True)
    grupo_causa = Column(String(60), nullable=True)


class VMortalidadCompleta(Base):
    __tablename__ = "v_mortalidad_completa"
    """VMortalidadCompleta(id_caso, nombres_apellidos, tipo_id, numero_id, fecha_nacimiento, edad, sitio_defuncion, fecha_defuncion, convivencia, otro_convivencia, escolaridad, regulacion_fecundidad, gestaciones, partos_vaginales, cesareas, nacidos_muertos, hijos_vivos, abortos, sin_antecedentes, hipertension_cronica, diabetes, vih_sida, tabaquismo, deficiencias_socioeconomicas, preeclampsia, eclampsia, sindrome_hellp, sepsis, hemorragia_3er_trimestre, embarazo_no_deseado, violencia_gestante, num_cpn, semana_inicio_cpn, cpn_realizado_por, nivel_atencion_cpn, remisiones_oportunas, compl_feto_rn_cie10, momento_muerte, semana_gestacion_muerte, fecha_parto, hora_parto, tipo_parto, parto_atendido_por, nivel_atencion_parto, causa_basica_cie10, fuente_causa_muerte, demora_1, demora_2, demora_3, demora_4)"""

    id_caso = Column(Integer, primary_key=True)
    nombres_apellidos = Column(String(200), nullable=True)
    tipo_id = Column(String(5), nullable=True)
    numero_id = Column(String(30), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)
    edad = Column(Integer, nullable=True)
    sitio_defuncion = Column(String(60), nullable=True)
    fecha_defuncion = Column(Date, nullable=True)
    convivencia = Column(String(30), nullable=True)
    otro_convivencia = Column(String(100), nullable=True)
    escolaridad = Column(String(30), nullable=True)
    regulacion_fecundidad = Column(String(50), nullable=True)
    gestaciones = Column(Integer, nullable=True)
    partos_vaginales = Column(Integer, nullable=True)
    cesareas = Column(Integer, nullable=True)
    nacidos_muertos = Column(Integer, nullable=True)
    hijos_vivos = Column(Integer, nullable=True)
    abortos = Column(Integer, nullable=True)
    sin_antecedentes = Column(Integer, nullable=True)
    hipertension_cronica = Column(Integer, nullable=True)
    diabetes = Column(Integer, nullable=True)
    vih_sida = Column(Integer, nullable=True)
    tabaquismo = Column(Integer, nullable=True)
    deficiencias_socioeconomicas = Column(Integer, nullable=True)
    preeclampsia = Column(Integer, nullable=True)
    eclampsia = Column(Integer, nullable=True)
    sindrome_hellp = Column(Integer, nullable=True)
    sepsis = Column(Integer, nullable=True)
    hemorragia_3er_trimestre = Column(Integer, nullable=True)
    embarazo_no_deseado = Column(Integer, nullable=True)
    violencia_gestante = Column(Integer, nullable=True)
    num_cpn = Column(Integer, nullable=True)
    semana_inicio_cpn = Column(Integer, nullable=True)
    cpn_realizado_por = Column(String(30), nullable=True)
    nivel_atencion_cpn = Column(String(3), nullable=True)
    remisiones_oportunas = Column(String(15), nullable=True)
    compl_feto_rn_cie10 = Column(String(10), nullable=True)
    momento_muerte = Column(String(30), nullable=True)
    semana_gestacion_muerte = Column(Integer, nullable=True)
    fecha_parto = Column(Date, nullable=True)
    hora_parto = Column(Time, nullable=True)
    tipo_parto = Column(String(20), nullable=True)
    parto_atendido_por = Column(String(30), nullable=True)
    nivel_atencion_parto = Column(String(3), nullable=True)
    causa_basica_cie10 = Column(String(10), nullable=True)
    fuente_causa_muerte = Column(String(30), nullable=True)
    demora_1 = Column(Integer, nullable=True)
    demora_2 = Column(Integer, nullable=True)
    demora_3 = Column(Integer, nullable=True)
    demora_4 = Column(Integer, nullable=True)

