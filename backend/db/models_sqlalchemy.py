"""Modelos ORM de SQLAlchemy para todas las tablas y vistas del sistema."""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)

from db.database import Base

# --- Tablas maestras (catálogos controlados por la plataforma) ---


class CatEvento(Base):
    """Tipos de evento de vigilancia (mortalidad, morbilidad)."""

    __tablename__ = 'cat_evento'

    codigo = Column(String(20), primary_key=True)
    nombre = Column(String(60), nullable=False)


class Departamento(Base):
    """Departamentos habilitados en la plataforma (maestra de afiliación)."""

    __tablename__ = 'departamento'

    codigo = Column(String(60), primary_key=True)
    nombre = Column(String(100), nullable=False)


class Secretaria(Base):
    """Secretarías de salud habilitadas; su `codigo` es el tenant que aísla los datos."""

    __tablename__ = 'secretaria'

    codigo = Column(String(60), primary_key=True)
    nombre = Column(String(150), nullable=False)
    departamento_codigo = Column(
        String(60), ForeignKey('departamento.codigo'), nullable=False, index=True
    )


class Cie10(Base):
    """Tabla de referencia CIE-10 (códigos válidos para las causas)."""

    __tablename__ = 'cie10'

    codigo = Column(String(10), primary_key=True)
    descripcion = Column(Text, nullable=False)


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
    tipo = Column(String(20), ForeignKey('cat_evento.codigo'), nullable=False, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    archivo_hash = Column(String(64), nullable=False, index=True)
    archivo = Column(String(255), nullable=False)
    fecha_carga = Column(DateTime, nullable=False)
    total_registros = Column(Integer, nullable=False)
    resumen = Column(JSON, nullable=False)
    # Tenant: código de la secretaría dueña de la carga. Ningún usuario de otra
    # secretaría debe ver este análisis ni los casos que agrupa.
    secretaria_codigo = Column(
        String(60), ForeignKey('secretaria.codigo'), index=True, nullable=True
    )
    # Auditoría: la mantiene el trigger trg_tiempos (db/auditoria.py).
    actualizado_en = Column(DateTime, nullable=True)


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
    __table_args__ = (UniqueConstraint('analisis_id', 'tipo_narrativa', 'filtros_hash'),)

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analisis_id = Column(Integer, ForeignKey('api_analisis.id', ondelete='CASCADE'), nullable=False)
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
    tipo = Column(String(20), ForeignKey('cat_evento.codigo'), nullable=False, index=True)
    row_hash = Column(String(64), nullable=False, index=True)
    event_hash = Column(String(64), nullable=False, index=True)
    # Apunta al caso de mortalidad o de morbilidad según `tipo`; el trigger
    # trg_importacion_caso (db/auditoria.py) comprueba que el caso exista.
    caso_id = Column(Integer, nullable=False)
    numero_id = Column(String(30), nullable=False)
    tipo_identificacion = Column(String(5), nullable=False)
    creado_en = Column(DateTime, nullable=False, server_default=func.now())
    # La detección de duplicados es por secretaría: dos secretarías pueden reportar
    # filas idénticas sin que una opaque la carga de la otra.
    secretaria_codigo = Column(
        String(60), ForeignKey('secretaria.codigo'), index=True, nullable=True
    )


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
    email = Column(String(254), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime, nullable=True)
    # Afiliación institucional: `secretaria_codigo` es el tenant que aísla sus datos. El
    # nombre de la secretaría y del departamento se obtienen de las tablas maestras.
    secretaria_codigo = Column(
        String(60), ForeignKey('secretaria.codigo'), index=True, nullable=True
    )


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
    """Datos sociodemográficos compartidos entre morbilidad y mortalidad.

    Asociación excluyente: cada fila pertenece a un caso de morbilidad o a uno de
    mortalidad, nunca a ambos (CHECK) y como máximo una fila por caso (índice único).
    """

    __tablename__ = 'datos_sociodemograficos'
    __table_args__ = (
        CheckConstraint(
            '(caso_morbilidad_id IS NOT NULL AND caso_mortalidad_id IS NULL) OR '
            '(caso_morbilidad_id IS NULL AND caso_mortalidad_id IS NOT NULL)',
            name='chk_ds_un_caso',
        ),
        Index('uq_ds_caso_morb', 'caso_morbilidad_id', unique=True),
        Index('uq_ds_caso_mort', 'caso_mortalidad_id', unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    caso_morbilidad_id = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=True)
    caso_mortalidad_id = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), nullable=True)
    id_zona_residencia = Column(
        Integer, ForeignKey('cat_zona_residencia.id'), nullable=True, index=True
    )
    id_poblacion_vulnerable = Column(
        Integer, ForeignKey('cat_poblacion_vulnerable.id'), nullable=True, index=True
    )
    id_etnia = Column(Integer, ForeignKey('cat_etnia.id'), nullable=True, index=True)
    id_tipo_afiliacion = Column(
        Integer, ForeignKey('cat_tipo_afiliacion.id'), nullable=True, index=True
    )


# --- Tablas de paciente y casos ---


class Paciente(Base):
    """Datos de identificación del paciente (un registro por número de documento)."""

    __tablename__ = 'paciente'
    __table_args__ = (UniqueConstraint('numero_id', name='uq_paciente_numero_id'),)

    id_paciente = Column(Integer, primary_key=True, autoincrement=True)
    nombres_apellidos = Column(String(200), nullable=False, index=True)
    id_tipo_id = Column(Integer, ForeignKey('cat_tipo_id.id'), nullable=False, index=True)
    numero_id = Column(String(30), nullable=False)
    fecha_nacimiento = Column(Date, nullable=True)
    creado_en = Column(DateTime, nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime, nullable=True)


class CasoMorbilidad(Base):
    """Caso de morbilidad materna extrema (ficha 549)."""

    __tablename__ = 'caso_morbilidad'
    __table_args__ = (
        UniqueConstraint(
            'secretaria_codigo', 'id_paciente', 'fecha_egreso', name='uq_morb_secretaria_pac_fecha'
        ),
    )

    id_caso = Column(Integer, primary_key=True, autoincrement=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'), nullable=False, index=True)
    fecha_egreso = Column(Date, nullable=True, index=True)
    creado_en = Column(DateTime, nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime, nullable=True)
    secretaria_codigo = Column(
        String(60), ForeignKey('secretaria.codigo'), index=True, nullable=True
    )


class Referencia(Base):
    """Datos de referencia y remisión del caso de morbilidad (uno por caso)."""

    __tablename__ = 'referencia'

    id_referencia = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
    remitida = Column(Boolean, nullable=False, default=False)
    tiempo_remision_h = Column(Numeric(precision=6, scale=1), nullable=True)


class ReferenciaInstitucion(Base):
    """Institución a la que se remitió el caso (hasta 2, una fila por posición).

    Reemplaza a `referencia.institucion_ref_1/2` (grupo repetido, incumple 1FN).
    """

    __tablename__ = 'referencia_institucion'
    __table_args__ = (
        UniqueConstraint('id_referencia', 'orden', name='uq_refinst_ref_orden'),
        CheckConstraint('orden BETWEEN 1 AND 2', name='chk_refinst_orden'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_referencia = Column(
        Integer, ForeignKey('referencia.id_referencia', ondelete='CASCADE'), nullable=False
    )
    orden = Column(SmallInteger, nullable=False)
    institucion = Column(String(200), nullable=False)


class AntecedenteObstetrico(Base):
    """Antecedentes obstétricos COMUNES a morbilidad y mortalidad (una tabla, dos eventos).

    Unifica los campos que antes estaban repetidos en `antecedente_obstetrico_morbilidad`
    (morbilidad) y `antecedente_materno_mortalidad` / `control_prenatal` (mortalidad). Lo propio de
    cada evento queda en su tabla de extensión. Asociación excluyente: cada fila cuelga
    de un caso de morbilidad o de uno de mortalidad, nunca de ambos (CHECK), y hay como
    máximo una fila por caso (índice único).
    """

    __tablename__ = 'antecedente_obstetrico'
    __table_args__ = (
        CheckConstraint(
            '(caso_morbilidad_id IS NOT NULL AND caso_mortalidad_id IS NULL) OR '
            '(caso_morbilidad_id IS NULL AND caso_mortalidad_id IS NOT NULL)',
            name='chk_ao_un_caso',
        ),
        Index('uq_ao_caso_morb', 'caso_morbilidad_id', unique=True),
        Index('uq_ao_caso_mort', 'caso_mortalidad_id', unique=True),
        CheckConstraint('gestaciones BETWEEN 0 AND 20', name='chk_ao_gest'),
        CheckConstraint('partos_vaginales BETWEEN 0 AND 20', name='chk_ao_pvag'),
        CheckConstraint('cesareas BETWEEN 0 AND 20', name='chk_ao_cesa'),
        CheckConstraint('abortos BETWEEN 0 AND 20', name='chk_ao_abort'),
        CheckConstraint('nacidos_muertos BETWEEN 0 AND 20', name='chk_ao_nmuert'),
        CheckConstraint('hijos_vivos BETWEEN 0 AND 20', name='chk_ao_hvivos'),
        CheckConstraint('num_controles_prenatales BETWEEN 0 AND 50', name='chk_ao_ncpn'),
        CheckConstraint('semana_inicio_cpn BETWEEN 0 AND 45', name='chk_ao_scpn'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    caso_morbilidad_id = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=True)
    caso_mortalidad_id = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), nullable=True)
    gestaciones = Column(SmallInteger, nullable=True)
    partos_vaginales = Column(SmallInteger, nullable=True)
    cesareas = Column(SmallInteger, nullable=True)
    abortos = Column(SmallInteger, nullable=True)
    nacidos_muertos = Column(SmallInteger, nullable=True)
    hijos_vivos = Column(SmallInteger, nullable=True)
    id_regulacion_fecundidad = Column(
        Integer, ForeignKey('cat_regulacion_fecundidad.id'), nullable=True, index=True
    )
    num_controles_prenatales = Column(SmallInteger, nullable=True)
    semana_inicio_cpn = Column(SmallInteger, nullable=True)


class AntecedenteObstetricoMorbilidad(Base):
    """Datos obstétricos PROPIOS del caso de morbilidad (el resto: `antecedente_obstetrico`)."""

    __tablename__ = 'antecedente_obstetrico_morbilidad'
    __table_args__ = (
        CheckConstraint(
            "momento_ocurrencia IN ('Antes','Durante','Despues')", name='chk_ant_momento'
        ),
        CheckConstraint("estado_recien_nacido IN ('Vivo','Muerto')", name='chk_ant_estado_rn'),
        CheckConstraint('molas BETWEEN 0 AND 20', name='chk_ant_molas'),
        CheckConstraint('ectopicos BETWEEN 0 AND 20', name='chk_ant_ecto'),
        CheckConstraint('edad_gestacional_sem BETWEEN 1 AND 50', name='chk_ant_egest'),
        CheckConstraint('peso_rn_gramos BETWEEN 500 AND 7000', name='chk_ant_pesorn'),
    )

    id_antecedente = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
    molas = Column(SmallInteger, nullable=True)
    ectopicos = Column(SmallInteger, nullable=True)
    fecha_ultima_gestacion = Column(Date, nullable=True)
    id_terminacion_gestacion = Column(
        Integer, ForeignKey('cat_terminacion_gestacion.id'), index=True
    )
    edad_gestacional_sem = Column(SmallInteger, nullable=True)
    momento_ocurrencia = Column(String(8), nullable=True)
    estado_recien_nacido = Column(String(6), nullable=True)
    multiplicidad = Column(Boolean, nullable=True)
    peso_rn_gramos = Column(SmallInteger, nullable=True)


class CriteriosEnfermedad(Base):
    """Criterios de enfermedad grave del caso de morbilidad (uno por caso)."""

    __tablename__ = 'criterios_enfermedad'

    id_criterio_enf = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
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
    """Criterios de falla orgánica del caso de morbilidad (uno por caso)."""

    __tablename__ = 'criterios_falla_organica'

    id_criterio_falla = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
    falla_cardiaca = Column(Boolean, nullable=False, default=False)
    falla_vascular = Column(Boolean, nullable=False, default=False)
    falla_renal = Column(Boolean, nullable=False, default=False)
    falla_hepatica = Column(Boolean, nullable=False, default=False)
    falla_metabolica = Column(Boolean, nullable=False, default=False)
    falla_cerebral = Column(Boolean, nullable=False, default=False)
    falla_respiratoria = Column(Boolean, nullable=False, default=False)
    falla_coagulacion = Column(Boolean, nullable=False, default=False)


class CriteriosManejo(Base):
    """Criterios de manejo del caso de morbilidad (uno por caso)."""

    __tablename__ = 'criterios_manejo'

    id_criterio_manejo = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
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
    """Datos de manejo hospitalario del caso de morbilidad (uno por caso)."""

    __tablename__ = 'manejo_hospitalario'
    __table_args__ = (
        CheckConstraint('dias_estancia_hosp >= 0', name='chk_mh_hosp'),
        CheckConstraint('dias_estancia_uci >= 0', name='chk_mh_uci'),
        CheckConstraint('unidades_transfundidas >= 0', name='chk_mh_transf'),
    )

    id_manejo = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
    dias_estancia_hosp = Column(Integer, nullable=True)
    dias_estancia_uci = Column(Integer, nullable=True)
    unidades_transfundidas = Column(Integer, nullable=True)


class CirugiaAdicionalMorbilidad(Base):
    """Cirugía adicional del caso (hasta 2, una fila por posición).

    Reemplaza a `manejo_hospitalario.cirugia_1/_cual/2/_cual` (grupo repetido, 1FN).
    `id_tipo_cirugia`: 1=Histerectomía, 2=Laparotomía, 3=Legrado, 4=Otra (ficha 549).
    """

    __tablename__ = 'cirugia_adicional_morbilidad'
    __table_args__ = (
        UniqueConstraint('id_manejo', 'orden', name='uq_cirugia_manejo_orden'),
        CheckConstraint('orden BETWEEN 1 AND 2', name='chk_cirugia_orden'),
        CheckConstraint('id_tipo_cirugia BETWEEN 1 AND 4', name='chk_cirugia_tipo'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_manejo = Column(
        Integer, ForeignKey('manejo_hospitalario.id_manejo', ondelete='CASCADE'), nullable=False
    )
    orden = Column(SmallInteger, nullable=False)
    id_tipo_cirugia = Column(SmallInteger, nullable=False)
    cual = Column(String(200), nullable=True)


class CausasMorbilidad(Base):
    """Causa diagnóstica principal del caso de morbilidad (una por caso)."""

    __tablename__ = 'causas_morbilidad'

    id_causa = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(Integer, ForeignKey('caso_morbilidad.id_caso'), nullable=False, unique=True)
    causa_principal_cie10 = Column(
        String(10), ForeignKey('cie10.codigo'), nullable=False, index=True
    )
    id_grupo_causa = Column(Integer, ForeignKey('cat_grupo_causa.id'), index=True)


class CausaAsociadaMorbilidad(Base):
    """Causa CIE-10 asociada del caso (hasta 3, una fila por posición).

    Reemplaza a `causas_morbilidad.causa_asociada_2/3/4` (grupo repetido, incumple 1FN).
    `orden` 1..3 equivale a las antiguas columnas 2..4 de la ficha 549.
    """

    __tablename__ = 'causa_asociada_morbilidad'
    __table_args__ = (
        UniqueConstraint('id_caso', 'orden', name='uq_causaaso_caso_orden'),
        CheckConstraint('orden BETWEEN 1 AND 3', name='chk_causaaso_orden'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_caso = Column(
        Integer,
        ForeignKey('caso_morbilidad.id_caso', ondelete='CASCADE'),
        nullable=False,
    )
    orden = Column(SmallInteger, nullable=False)
    cie10 = Column(String(10), ForeignKey('cie10.codigo'), nullable=False, index=True)


# --- Mortalidad materna ---


class CasoMortalidad(Base):
    """Caso de muerte materna (ficha 550)."""

    __tablename__ = 'caso_mortalidad'
    __table_args__ = (
        UniqueConstraint(
            'secretaria_codigo',
            'id_paciente',
            'fecha_defuncion',
            name='uq_mort_secretaria_pac_fecha',
        ),
    )

    id_caso = Column(Integer, primary_key=True, autoincrement=True)
    id_paciente = Column(Integer, ForeignKey('paciente.id_paciente'), nullable=False, index=True)
    id_sitio_defuncion = Column(
        Integer, ForeignKey('cat_sitio_defuncion.id'), nullable=False, index=True
    )
    fecha_defuncion = Column(Date, nullable=True, index=True)
    creado_en = Column(DateTime, nullable=False, server_default=func.now())
    actualizado_en = Column(DateTime, nullable=True)
    secretaria_codigo = Column(
        String(60), ForeignKey('secretaria.codigo'), index=True, nullable=True
    )


class AntecedenteMaternoMortalidad(Base):
    """Datos maternos PROPIOS del caso de mortalidad (convivencia y escolaridad)."""

    __tablename__ = 'antecedente_materno_mortalidad'

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    id_convivencia = Column(Integer, ForeignKey('cat_convivencia.id'), nullable=False, index=True)
    otro_convivencia = Column(String(100), nullable=True)
    id_escolaridad = Column(Integer, ForeignKey('cat_escolaridad.id'), nullable=False, index=True)


class AntecedenteRiesgo(Base):
    """Factores de riesgo previos al caso de mortalidad."""

    __tablename__ = 'antecedente_riesgo'

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
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
    deficiencias_socioeconomicas = Column(Boolean, nullable=False, default=False)
    sifilis = Column(Boolean, nullable=False, default=False)
    hepatitis_b = Column(Boolean, nullable=False, default=False)
    otros_factores_riesgo = Column(Boolean, nullable=False, default=False)
    desc_otros_factores = Column(String(300), nullable=True)
    gingivitis_periodontitis = Column(Boolean, nullable=False, default=False)


class ComplicacionEmbarazo(Base):
    """Complicaciones durante el embarazo del caso de mortalidad."""

    __tablename__ = 'complicacion_embarazo'

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
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
    """Atención del control prenatal del caso de mortalidad (quién y dónde)."""

    __tablename__ = 'control_prenatal'

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    id_personal_cpn = Column(Integer, ForeignKey('cat_personal_salud.id'), index=True)
    id_nivel_atencion_cpn = Column(Integer, ForeignKey('cat_nivel_atencion.id'), index=True)
    id_remisiones = Column(Integer, ForeignKey('cat_remisiones.id'), nullable=False, index=True)
    compl_feto_rn_cie10 = Column(String(10), nullable=True)


class AntecedentePartoPuerperio(Base):
    """Antecedentes de parto y puerperio del caso de mortalidad."""

    __tablename__ = 'antecedente_parto_puerperio'
    __table_args__ = (
        CheckConstraint('semana_gestacion_muerte BETWEEN 1 AND 45', name='chk_pp_semana'),
    )

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    id_momento_muerte = Column(
        Integer, ForeignKey('cat_momento_muerte.id'), nullable=False, index=True
    )
    semana_gestacion_muerte = Column(Integer, nullable=True)
    fecha_parto = Column(Date, nullable=True)
    hora_parto = Column(Time, nullable=True)
    id_tipo_parto = Column(Integer, ForeignKey('cat_tipo_parto.id'), index=True)
    id_atendido_por = Column(Integer, ForeignKey('cat_personal_salud.id'), index=True)
    otro_atencion_parto = Column(String(100), nullable=True)
    id_nivel_atencion_parto = Column(Integer, ForeignKey('cat_nivel_atencion.id'), index=True)


class CausaMuerte(Base):
    """Causa básica y demoras asociadas a la muerte materna."""

    __tablename__ = 'causa_muerte'
    __table_args__ = (
        CheckConstraint(
            "causa_basica_cie10 NOT LIKE 'P%' AND causa_basica_cie10 NOT IN ('8888', '9999')",
            name='chk_causa_cie10_valida',
        ),
    )

    id_caso = Column(Integer, ForeignKey('caso_mortalidad.id_caso'), primary_key=True)
    causa_basica_cie10 = Column(String(10), nullable=False, index=True)
    id_fuente_causa = Column(
        Integer, ForeignKey('cat_fuente_causa_muerte.id'), nullable=False, index=True
    )
    demora_1 = Column(Boolean, nullable=False, default=False)
    demora_2 = Column(Boolean, nullable=False, default=False)
    demora_3 = Column(Boolean, nullable=False, default=False)
    demora_4 = Column(Boolean, nullable=False, default=False)


class AuditoriaCambio(Base):
    """Bitácora de cambios mantenida por triggers (ver db/auditoria.py).

    No guarda valores de columnas (los datos de pacientes no se copian): solo la tabla,
    el registro, la operación, el momento, el usuario de base de datos y los NOMBRES de
    las columnas modificadas.
    """

    __tablename__ = 'auditoria_cambio'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tabla = Column(String(60), nullable=False)
    registro_id = Column(String(40), nullable=False)
    operacion = Column(String(6), nullable=False)
    columnas_modificadas = Column(JSON, nullable=True)
    ocurrio_en = Column(DateTime, nullable=False, server_default=func.now())
    usuario_bd = Column(String(60), nullable=True)

    __table_args__ = (
        CheckConstraint("operacion IN ('INSERT','UPDATE','DELETE')", name='chk_audit_operacion'),
        Index('ix_auditoria_tabla_registro', 'tabla', 'registro_id'),
        Index('ix_auditoria_ocurrio_en', 'ocurrio_en'),
    )


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
