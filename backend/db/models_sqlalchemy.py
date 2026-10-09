"""Modelos ORM de SQLAlchemy para todas las tablas y vistas del sistema."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)

from db.database import Base


class Analisis(Base):
    """Representa un análisis cargado desde archivo.

    Attributes:
        tipo: Tipo de análisis (mortalidad o morbilidad).
        nombre_archivo: Nombre del archivo cargado.
        archivo_hash: Hash del archivo para trazabilidad y detección de duplicados.
        archivo: Archivo físico almacenado en media.
        fecha_carga: Fecha y hora de carga.
        total_registros: Cantidad total de registros procesados.
        resumen: Metadatos de resumen del proceso de análisis.
    """

    __tablename__ = 'api_analisis'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tipo = Column(String(20), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    archivo_hash = Column(String(64), nullable=False)
    archivo = Column(String(255), nullable=False)
    fecha_carga = Column(DateTime, nullable=False)
    total_registros = Column(Integer, nullable=False)
    resumen = Column(JSON, nullable=False)
    # Tenant: código de la secretaría dueña de la carga. Ningún usuario de otra
    # secretaría debe ver este análisis ni los casos que agrupa.
    secretaria_codigo = Column(String(60), index=True, nullable=True)


class NarrativaIA(Base):
    """Narrativa en lenguaje natural generada por IA-SERVICE, cacheada por análisis.

    Attributes:
        analisis_id: FK al análisis del que provienen los indicadores.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        filtros_hash: Hash de los filtros activos (year, month, tipo_clustering, n_clusters).
        contenido: Texto generado.
        modelo: Nombre del modelo LLM usado.
        generado_en: Fecha y hora de generación.
    """

    __tablename__ = 'narrativa_ia'
    __table_args__ = (UniqueConstraint(
        'analisis_id', 'tipo_narrativa', 'filtros_hash'),)

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analisis_id = Column(Integer, ForeignKey(
        'api_analisis.id'), nullable=False)
    tipo_narrativa = Column(String(30), nullable=False)
    filtros_hash = Column(String(64), nullable=False)
    contenido = Column(Text, nullable=False)
    modelo = Column(String(50), nullable=False)
    generado_en = Column(DateTime, nullable=False)


class SivigilaImportacion(Base):
    """Registra eventos de importación procesados desde SIVIGILA.

    Attributes:
        tipo: Tipo de evento importado.
        row_hash: Hash único de la fila para deduplicación.
        event_hash: Hash del evento para agrupación y consulta.
        caso_id: Identificador interno del caso.
        numero_id: Número de identificación de la persona.
        tipo_identificacion: Tipo de documento de identificación.
        creado_en: Fecha y hora de creación del registro.
    """

    __tablename__ = 'api_sivigilaimportacion'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tipo = Column(String(20), nullable=False)
    row_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False)
    caso_id = Column(Integer, nullable=False)
    numero_id = Column(String(30), nullable=False)
    tipo_identificacion = Column(String(5), nullable=False)
    creado_en = Column(DateTime, nullable=False)
    # La detección de duplicados es por secretaría: dos secretarías pueden reportar
    # filas idénticas sin que una opaque la carga de la otra.
    secretaria_codigo = Column(String(60), index=True, nullable=True)


class Usuario(Base):
    """Almacena usuarios del sistema con credenciales en hash.

    Attributes:
        nombre: Nombre completo del usuario.
        email: Correo electrónico único del usuario.
        password_hash: Hash de la contraseña del usuario.
        fecha_registro: Fecha y hora de registro en el sistema.
    """

    __tablename__ = 'api_usuario'

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(254), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    # Afiliación institucional del usuario. `secretaria_codigo` es el tenant que
    # aísla sus datos; `departamento` y `secretaria` guardan el nombre visible.
    departamento = Column(String(100), nullable=True)
    secretaria = Column(String(150), nullable=True)
    secretaria_codigo = Column(String(60), index=True, nullable=True)


# --- Tablas de catálogo ---


class CatConvivencia(Base):
    """Catálogo de tipos de convivencia."""

    __tablename__ = 'cat_convivencia'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatEscolaridad(Base):
    """Catálogo de niveles de escolaridad."""

    __tablename__ = 'cat_escolaridad'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatFuenteCausaMuerte(Base):
    """Catálogo de fuentes de causa de muerte."""

    __tablename__ = 'cat_fuente_causa_muerte'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatGrupoCausa(Base):
    """Catálogo de grupos de causa de morbilidad."""

    __tablename__ = 'cat_grupo_causa'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(60), nullable=False)


class CatMomentoMuerte(Base):
    """Catálogo de momentos de muerte materna."""

    __tablename__ = 'cat_momento_muerte'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatNivelAtencion(Base):
    """Catálogo de niveles de atención en salud."""

    __tablename__ = 'cat_nivel_atencion'

    id = Column(Integer, primary_key=True)
    nivel = Column(String(3), nullable=False)


class CatPersonalSalud(Base):
    """Catálogo de tipos de personal de salud."""

    __tablename__ = 'cat_personal_salud'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatRegulacionFecundidad(Base):
    """Catálogo de métodos de regulación de fecundidad."""

    __tablename__ = 'cat_regulacion_fecundidad'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(50), nullable=False)


class CatRemisiones(Base):
    """Catálogo de tipos de remisiones oportunas."""

    __tablename__ = 'cat_remisiones'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(15), nullable=False)


class CatSitioDefuncion(Base):
    """Catálogo de sitios de defunción."""

    __tablename__ = 'cat_sitio_defuncion'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(60), nullable=False)


class CatTerminacionGestacion(Base):
    """Catálogo de tipos de terminación de gestación."""

    __tablename__ = 'cat_terminacion_gestacion'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatTipoId(Base):
    """Catálogo de tipos de identificación."""

    __tablename__ = 'cat_tipo_id'

    id = Column(Integer, primary_key=True)
    codigo = Column(String(5), nullable=False)
    descripcion = Column(String(50), nullable=False)


class CatTipoParto(Base):
    """Catálogo de tipos de parto."""

    __tablename__ = 'cat_tipo_parto'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(20), nullable=False)


class CatZonaResidencia(Base):
    """Catálogo de zona de residencia."""

    __tablename__ = 'cat_zona_residencia'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(10), nullable=False)


class CatPoblacionVulnerable(Base):
    """Catálogo de población vulnerable."""

    __tablename__ = 'cat_poblacion_vulnerable'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(30), nullable=False)


class CatEtnia(Base):
    """Catálogo de etnia."""

    __tablename__ = 'cat_etnia'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(20), nullable=False)


class CatTipoAfiliacion(Base):
    """Catálogo de tipo de afiliación en salud."""

    __tablename__ = 'cat_tipo_afiliacion'

    id = Column(Integer, primary_key=True)
    descripcion = Column(String(20), nullable=False)


class DatosSociodemograficos(Base):
    """Datos sociodemográficos compartidos entre morbilidad y mortalidad."""

    __tablename__ = 'datos_sociodemograficos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    caso_morbilidad_id = Column(Integer, ForeignKey(
        'caso_morbilidad.id_caso'), nullable=True)
    caso_mortalidad_id = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), nullable=True)
    id_zona_residencia = Column(Integer, ForeignKey(
        'cat_zona_residencia.id'), nullable=True)
    id_poblacion_vulnerable = Column(
        Integer, ForeignKey('cat_poblacion_vulnerable.id'), nullable=True
    )
    id_etnia = Column(Integer, ForeignKey('cat_etnia.id'), nullable=True)
    id_tipo_afiliacion = Column(Integer, ForeignKey(
        'cat_tipo_afiliacion.id'), nullable=True)


# --- Tablas de paciente y casos ---


class Paciente(Base):
    """Datos de identificación del paciente."""

    __tablename__ = 'paciente'

    id_paciente = Column(Integer, primary_key=True,
                         autoincrement=True, index=True)
    nombres_apellidos = Column(String(200), nullable=False)
    id_tipo_id = Column(Integer, ForeignKey('cat_tipo_id.id'))
    numero_id = Column(String(30), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)


class CasoMorbilidad(Base):
    """Caso de morbilidad materna extrema."""

    __tablename__ = 'caso_morbilidad'

    id_caso = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'))
    fecha_egreso = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)
    secretaria_codigo = Column(String(60), index=True, nullable=True)


class Referencia(Base):
    """Datos de referencia y remisión del caso de morbilidad."""

    __tablename__ = 'referencia'

    id_referencia = Column(Integer, primary_key=True,
                           autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    remitida = Column(Boolean, nullable=False, default=False)
    institucion_ref_1 = Column(String(200), nullable=True)
    institucion_ref_2 = Column(String(200), nullable=True)
    tiempo_remision_h = Column(Numeric(precision=6, scale=1), nullable=True)


class AntecedentesObstetricos(Base):
    """Antecedentes obstétricos del caso de morbilidad."""

    __tablename__ = 'antecedentes_obstetricos'

    id_antecedente = Column(Integer, primary_key=True,
                            autoincrement=True, index=True)
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
    id_regulacion_fecundidad = Column(
        Integer, ForeignKey('cat_regulacion_fecundidad.id'))
    num_controles_prenatales = Column(Integer, nullable=True)
    semanas_inicio_cpn = Column(Integer, nullable=True)
    id_terminacion_gestacion = Column(
        Integer, ForeignKey('cat_terminacion_gestacion.id'))
    edad_gestacional_sem = Column(Integer, nullable=True)
    momento_ocurrencia = Column(String(7), nullable=True)
    estado_recien_nacido = Column(String(6), nullable=True)
    multiplicidad = Column(Boolean, nullable=True)
    peso_rn_gramos = Column(Integer, nullable=True)


class CriteriosEnfermedad(Base):
    """Criterios de enfermedad grave del caso de morbilidad."""

    __tablename__ = 'criterios_enfermedad'

    id_criterio_enf = Column(Integer, primary_key=True,
                             autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    eclampsia = Column(Boolean, nullable=False, default=False)
    sepsis_sistemica_severa = Column(Boolean, nullable=False, default=False)
    hemorragia_obstetrica = Column(Boolean, nullable=False, default=False)
    preeclampsia = Column(Boolean, nullable=False, default=False)
    ruptura_uterina = Column(Boolean, nullable=False, default=False)
    aborto_septico = Column(Boolean, nullable=False, default=False)
    embarazo_ectopico = Column(Boolean, nullable=False, default=False)
    autoinmune = Column(Boolean, nullable=False, default=False)
    hematologica = Column(Boolean, nullable=False, default=False)
    oncologica = Column(Boolean, nullable=False, default=False)
    endocrino_metabolicas = Column(Boolean, nullable=False, default=False)
    renales = Column(Boolean, nullable=False, default=False)
    gastrointestinales = Column(Boolean, nullable=False, default=False)
    tromboembolicos = Column(Boolean, nullable=False, default=False)
    cardiocerebrovasculares = Column(Boolean, nullable=False, default=False)
    otras_enfermedades = Column(Boolean, nullable=False, default=False)


class CriteriosFallaOrganica(Base):
    """Criterios de falla orgánica del caso de morbilidad."""

    __tablename__ = 'criterios_falla_organica'

    id_criterio_falla = Column(
        Integer, primary_key=True, autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    falla_cardiaca = Column(Boolean, nullable=False, default=False)
    falla_vascular = Column(Boolean, nullable=False, default=False)
    falla_renal = Column(Boolean, nullable=False, default=False)
    falla_hepatica = Column(Boolean, nullable=False, default=False)
    falla_metabolica = Column(Boolean, nullable=False, default=False)
    falla_cerebral = Column(Boolean, nullable=False, default=False)
    falla_respiratoria = Column(Boolean, nullable=False, default=False)
    falla_coagulacion = Column(Boolean, nullable=False, default=False)


class CriteriosManejo(Base):
    """Criterios de manejo del caso de morbilidad."""

    __tablename__ = 'criterios_manejo'

    id_criterio_manejo = Column(
        Integer, primary_key=True, autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    ingreso_uci = Column(Boolean, nullable=False, default=False)
    cirugia_adicional = Column(Boolean, nullable=False, default=False)
    transfusion = Column(Boolean, nullable=False, default=False)
    total_criterios = Column(Integer, nullable=True)
    accidente = Column(Boolean, nullable=False, default=False)
    intoxicacion_accidental = Column(Boolean, nullable=False, default=False)
    intento_suicida = Column(Boolean, nullable=False, default=False)
    victima_violencia = Column(Boolean, nullable=False, default=False)
    otros_eventos_sp = Column(Boolean, nullable=False, default=False)
    cual_evento_sp = Column(String(200), nullable=True)


class ManejoHospitalario(Base):
    """Datos de manejo hospitalario del caso de morbilidad."""

    __tablename__ = 'manejo_hospitalario'

    id_manejo = Column(Integer, primary_key=True,
                       autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    dias_estancia_hosp = Column(Integer, nullable=True)
    dias_estancia_uci = Column(Integer, nullable=True)
    unidades_transfundidas = Column(Integer, nullable=True)
    cirugia_1 = Column(Integer, nullable=True)
    cirugia_1_cual = Column(String(200), nullable=True)
    cirugia_2 = Column(Integer, nullable=True)
    cirugia_2_cual = Column(String(200), nullable=True)


class CausasMorbilidad(Base):
    """Causas diagnósticas del caso de morbilidad."""

    __tablename__ = 'causas_morbilidad'

    id_causa = Column(Integer, primary_key=True,
                      autoincrement=True, index=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'))
    causa_principal_cie10 = Column(String(10), nullable=False)
    id_grupo_causa = Column(Integer, ForeignKey('cat_grupo_causa.id'))
    causa_asociada_2 = Column(String(10), nullable=True)
    causa_asociada_3 = Column(String(10), nullable=True)
    causa_asociada_4 = Column(String(10), nullable=True)


# --- Mortalidad materna ---


class CasoMortalidad(Base):
    """Caso de muerte materna."""

    __tablename__ = 'caso_mortalidad'

    id_caso = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'))
    id_sitio_defuncion = Column(Integer, ForeignKey('cat_sitio_defuncion.id'))
    fecha_defuncion = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=True)
    secretaria_codigo = Column(String(60), index=True, nullable=True)


class AntecedenteMaterno(Base):
    """Antecedentes maternos del caso de mortalidad."""

    __tablename__ = 'antecedente_materno'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    id_convivencia = Column(Integer, ForeignKey('cat_convivencia.id'))
    otro_convivencia = Column(String(100), nullable=True)
    id_escolaridad = Column(Integer, ForeignKey('cat_escolaridad.id'))
    id_regulacion_fec = Column(
        Integer, ForeignKey('cat_regulacion_fecundidad.id'))
    gestaciones = Column(Integer, nullable=True)
    partos_vaginales = Column(Integer, nullable=True)
    cesareas = Column(Integer, nullable=True)
    nacidos_muertos = Column(Integer, nullable=True)
    hijos_vivos = Column(Integer, nullable=True)
    abortos = Column(Integer, nullable=True)


class AntecedenteRiesgo(Base):
    """Factores de riesgo previos al caso de mortalidad."""

    __tablename__ = 'antecedente_riesgo'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    sin_antecedentes = Column(Boolean, nullable=False, default=False)
    hipertension_cronica = Column(Boolean, nullable=False, default=False)
    cardiopatias = Column(Boolean, nullable=False, default=False)
    diabetes = Column(Boolean, nullable=False, default=False)
    mola_hidatiforme = Column(Boolean, nullable=False, default=False)
    rn_pretermino = Column(Boolean, nullable=False, default=False)
    rn_bajo_peso = Column(Boolean, nullable=False, default=False)
    rn_macrosomico = Column(Boolean, nullable=False, default=False)
    trastorno_mental = Column(Boolean, nullable=False, default=False)
    obesidad = Column(Boolean, nullable=False, default=False)
    desnutricion_cronica = Column(Boolean, nullable=False, default=False)
    intergenesis_menor_2a = Column(Boolean, nullable=False, default=False)
    its_distintas = Column(Boolean, nullable=False, default=False)
    vih_sida = Column(Boolean, nullable=False, default=False)
    otras_infecciones = Column(Boolean, nullable=False, default=False)
    rh_negativo = Column(Boolean, nullable=False, default=False)
    tabaquismo = Column(Boolean, nullable=False, default=False)
    alcoholismo = Column(Boolean, nullable=False, default=False)
    sustancias_psicoactivas = Column(Boolean, nullable=False, default=False)
    deficiencias_socioeconomicas = Column(
        Boolean, nullable=False, default=False)
    sifilis = Column(Boolean, nullable=False, default=False)
    hepatitis_b = Column(Boolean, nullable=False, default=False)
    otros_factores_riesgo = Column(Boolean, nullable=False, default=False)
    desc_otros_factores = Column(String(300), nullable=True)
    gingivitis_periodontitis = Column(Boolean, nullable=False, default=False)


class ComplicacionEmbarazo(Base):
    """Complicaciones durante el embarazo del caso de mortalidad."""

    __tablename__ = 'complicacion_embarazo'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    preeclampsia = Column(Boolean, nullable=False, default=False)
    eclampsia = Column(Boolean, nullable=False, default=False)
    sindrome_hellp = Column(Boolean, nullable=False, default=False)
    diabetes_gestacional = Column(Boolean, nullable=False, default=False)
    sepsis = Column(Boolean, nullable=False, default=False)
    hemorragia_1er_trimestre = Column(Boolean, nullable=False, default=False)
    hemorragia_2do_trimestre = Column(Boolean, nullable=False, default=False)
    hemorragia_3er_trimestre = Column(Boolean, nullable=False, default=False)
    desproporcion_cefalo_pelv = Column(Boolean, nullable=False, default=False)
    retardo_crecimiento_iu = Column(Boolean, nullable=False, default=False)
    enfermedad_autoinmune = Column(Boolean, nullable=False, default=False)
    malaria = Column(Boolean, nullable=False, default=False)
    embarazo_no_deseado = Column(Boolean, nullable=False, default=False)
    violencia_gestante = Column(Boolean, nullable=False, default=False)
    otras_complicaciones = Column(Boolean, nullable=False, default=False)
    desc_otras_complicaciones = Column(String(300), nullable=True)
    gestacion_violencia_sexual = Column(Boolean, nullable=False, default=False)
    feto_incompatible_vida = Column(Boolean, nullable=False, default=False)
    sintomas_depresivos = Column(Boolean, nullable=False, default=False)


class ControlPrenatal(Base):
    """Datos de control prenatal del caso de mortalidad."""

    __tablename__ = 'control_prenatal'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    num_cpn = Column(Integer, nullable=True)
    semana_inicio_cpn = Column(Integer, nullable=True)
    id_personal_cpn = Column(Integer, ForeignKey('cat_personal_salud.id'))
    id_nivel_atencion_cpn = Column(
        Integer, ForeignKey('cat_nivel_atencion.id'))
    id_remisiones = Column(Integer, ForeignKey('cat_remisiones.id'))
    compl_feto_rn_cie10 = Column(String(10), nullable=True)


class AntecedentePartoPuerperio(Base):
    """Antecedentes de parto y puerperio del caso de mortalidad."""

    __tablename__ = 'antecedente_parto_puerperio'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    id_momento_muerte = Column(Integer, ForeignKey('cat_momento_muerte.id'))
    semana_gestacion_muerte = Column(Integer, nullable=True)
    fecha_parto = Column(Date, nullable=True)
    hora_parto = Column(Time, nullable=True)
    id_tipo_parto = Column(Integer, ForeignKey('cat_tipo_parto.id'))
    id_atendido_por = Column(Integer, ForeignKey('cat_personal_salud.id'))
    otro_atencion_parto = Column(String(100), nullable=True)
    id_nivel_atencion_parto = Column(
        Integer, ForeignKey('cat_nivel_atencion.id'))


class CausaMuerte(Base):
    """Causa básica y demoras asociadas a la muerte materna."""

    __tablename__ = 'causa_muerte'

    id_caso = Column(Integer, ForeignKey(
        'caso_mortalidad.id_caso'), primary_key=True)
    causa_basica_cie10 = Column(String(10), nullable=False)
    id_fuente_causa = Column(Integer, ForeignKey('cat_fuente_causa_muerte.id'))
    demora_1 = Column(Boolean, nullable=False, default=False)
    demora_2 = Column(Boolean, nullable=False, default=False)
    demora_3 = Column(Boolean, nullable=False, default=False)
    demora_4 = Column(Boolean, nullable=False, default=False)


# --- Vistas (solo lectura) ---


class VMorbilidadCompleta(Base):
    """Vista consolidada de morbilidad materna extrema (solo lectura)."""

    __tablename__ = 'v_morbilidad_completa'

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
    zona_residencia = Column(String(10), nullable=True)
    poblacion_vulnerable = Column(String(30), nullable=True)
    etnia = Column(String(20), nullable=True)
    tipo_afiliacion = Column(String(20), nullable=True)
    secretaria_codigo = Column(String(60), nullable=True)


class VMortalidadCompleta(Base):
    """Vista consolidada de mortalidad materna (solo lectura)."""

    __tablename__ = 'v_mortalidad_completa'

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
    zona_residencia = Column(String(10), nullable=True)
    poblacion_vulnerable = Column(String(30), nullable=True)
    etnia = Column(String(20), nullable=True)
    tipo_afiliacion = Column(String(20), nullable=True)
    secretaria_codigo = Column(String(60), nullable=True)
