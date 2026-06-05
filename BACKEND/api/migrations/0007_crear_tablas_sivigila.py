# Migration 0007: crea las tablas SIVIGILA no gestionadas por Django
# y las puebla con los valores de catálogo estándar del INS Colombia.
# Solo se ejecuta en SQLite (desarrollo); en MySQL estas tablas existen
# en el esquema SIVIGILA externo.

from django.db import migrations


# ---------------------------------------------------------------------------
# SQL de creación de tablas (compatible con SQLite y MySQL)
# ---------------------------------------------------------------------------

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS cat_tipo_id (
    id          SMALLINT PRIMARY KEY,
    codigo      VARCHAR(5) UNIQUE NOT NULL,
    descripcion VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_convivencia (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_escolaridad (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_regulacion_fecundidad (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_sitio_defuncion (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_momento_muerte (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_remisiones (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(15) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_tipo_parto (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_terminacion_gestacion (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_personal_salud (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_nivel_atencion (
    id          SMALLINT PRIMARY KEY,
    nivel       VARCHAR(3) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_fuente_causa_muerte (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_grupo_causa (
    id          SMALLINT PRIMARY KEY,
    descripcion VARCHAR(60) NOT NULL
);

CREATE TABLE IF NOT EXISTS paciente (
    id_paciente       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres_apellidos VARCHAR(200) NOT NULL,
    id_tipo_id        SMALLINT NOT NULL REFERENCES cat_tipo_id(id),
    numero_id         VARCHAR(30) NOT NULL,
    fecha_nacimiento  DATE,
    creado_en         DATETIME,
    UNIQUE (id_tipo_id, numero_id)
);

CREATE TABLE IF NOT EXISTS caso_morbilidad (
    id_caso      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paciente  INTEGER NOT NULL REFERENCES paciente(id_paciente),
    fecha_egreso DATE,
    creado_en    DATETIME
);

CREATE TABLE IF NOT EXISTS referencia (
    id_referencia      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso            INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    remitida           INTEGER NOT NULL DEFAULT 0,
    institucion_ref_1  VARCHAR(200),
    institucion_ref_2  VARCHAR(200),
    tiempo_remision_h  DECIMAL(6,1)
);

CREATE TABLE IF NOT EXISTS antecedentes_obstetricos (
    id_antecedente              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso                     INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    num_gestaciones             SMALLINT,
    partos_vaginales            SMALLINT,
    cesareas                    SMALLINT,
    abortos                     SMALLINT,
    molas                       SMALLINT,
    ectopicos                   SMALLINT,
    muertos                     SMALLINT,
    vivos                       SMALLINT,
    fecha_ultima_gestacion      DATE,
    id_regulacion_fecundidad    SMALLINT REFERENCES cat_regulacion_fecundidad(id),
    num_controles_prenatales    SMALLINT,
    semanas_inicio_cpn          SMALLINT,
    id_terminacion_gestacion    SMALLINT REFERENCES cat_terminacion_gestacion(id),
    edad_gestacional_sem        SMALLINT,
    momento_ocurrencia          VARCHAR(7),
    estado_recien_nacido        VARCHAR(6),
    multiplicidad               INTEGER,
    peso_rn_gramos              SMALLINT
);

CREATE TABLE IF NOT EXISTS criterios_enfermedad (
    id_criterio_enf         INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso                 INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    eclampsia               INTEGER NOT NULL DEFAULT 0,
    sepsis_sistemica_severa INTEGER NOT NULL DEFAULT 0,
    hemorragia_obstetrica   INTEGER NOT NULL DEFAULT 0,
    preeclampsia            INTEGER NOT NULL DEFAULT 0,
    ruptura_uterina         INTEGER NOT NULL DEFAULT 0,
    aborto_septico          INTEGER NOT NULL DEFAULT 0,
    embarazo_ectopico       INTEGER NOT NULL DEFAULT 0,
    autoinmune              INTEGER NOT NULL DEFAULT 0,
    hematologica            INTEGER NOT NULL DEFAULT 0,
    oncologica              INTEGER NOT NULL DEFAULT 0,
    endocrino_metabolicas   INTEGER NOT NULL DEFAULT 0,
    renales                 INTEGER NOT NULL DEFAULT 0,
    gastrointestinales      INTEGER NOT NULL DEFAULT 0,
    tromboembolicos         INTEGER NOT NULL DEFAULT 0,
    cardiocerebrovasculares INTEGER NOT NULL DEFAULT 0,
    otras_enfermedades      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS criterios_falla_organica (
    id_criterio_falla  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso            INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    falla_cardiaca     INTEGER NOT NULL DEFAULT 0,
    falla_vascular     INTEGER NOT NULL DEFAULT 0,
    falla_renal        INTEGER NOT NULL DEFAULT 0,
    falla_hepatica     INTEGER NOT NULL DEFAULT 0,
    falla_metabolica   INTEGER NOT NULL DEFAULT 0,
    falla_cerebral     INTEGER NOT NULL DEFAULT 0,
    falla_respiratoria INTEGER NOT NULL DEFAULT 0,
    falla_coagulacion  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS criterios_manejo (
    id_criterio_manejo      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso                 INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    ingreso_uci             INTEGER NOT NULL DEFAULT 0,
    cirugia_adicional       INTEGER NOT NULL DEFAULT 0,
    transfusion             INTEGER NOT NULL DEFAULT 0,
    total_criterios         SMALLINT,
    accidente               INTEGER NOT NULL DEFAULT 0,
    intoxicacion_accidental INTEGER NOT NULL DEFAULT 0,
    intento_suicida         INTEGER NOT NULL DEFAULT 0,
    victima_violencia       INTEGER NOT NULL DEFAULT 0,
    otros_eventos_sp        INTEGER NOT NULL DEFAULT 0,
    cual_evento_sp          VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS manejo_hospitalario (
    id_manejo              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso                INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    dias_estancia_hosp     SMALLINT,
    dias_estancia_uci      SMALLINT,
    unidades_transfundidas SMALLINT,
    cirugia_1              SMALLINT,
    cirugia_1_cual         VARCHAR(200),
    cirugia_2              SMALLINT,
    cirugia_2_cual         VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS causas_morbilidad (
    id_causa             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_caso              INTEGER NOT NULL REFERENCES caso_morbilidad(id_caso),
    causa_principal_cie10 VARCHAR(10) NOT NULL,
    id_grupo_causa        SMALLINT REFERENCES cat_grupo_causa(id),
    causa_asociada_2      VARCHAR(10),
    causa_asociada_3      VARCHAR(10),
    causa_asociada_4      VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS caso_mortalidad (
    id_caso              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paciente          INTEGER NOT NULL REFERENCES paciente(id_paciente),
    id_sitio_defuncion   SMALLINT NOT NULL REFERENCES cat_sitio_defuncion(id),
    fecha_defuncion      DATE,
    creado_en            DATETIME
);

CREATE TABLE IF NOT EXISTS antecedente_materno (
    id_caso                INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    id_convivencia         SMALLINT NOT NULL REFERENCES cat_convivencia(id),
    otro_convivencia       VARCHAR(100),
    id_escolaridad         SMALLINT NOT NULL REFERENCES cat_escolaridad(id),
    id_regulacion_fec      SMALLINT NOT NULL REFERENCES cat_regulacion_fecundidad(id),
    gestaciones            SMALLINT,
    partos_vaginales       SMALLINT,
    cesareas               SMALLINT,
    nacidos_muertos        SMALLINT,
    hijos_vivos            SMALLINT,
    abortos                SMALLINT
);

CREATE TABLE IF NOT EXISTS antecedente_riesgo (
    id_caso                     INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    sin_antecedentes            INTEGER NOT NULL DEFAULT 0,
    hipertension_cronica        INTEGER NOT NULL DEFAULT 0,
    cardiopatias                INTEGER NOT NULL DEFAULT 0,
    diabetes                    INTEGER NOT NULL DEFAULT 0,
    mola_hidatiforme            INTEGER NOT NULL DEFAULT 0,
    rn_pretermino               INTEGER NOT NULL DEFAULT 0,
    rn_bajo_peso                INTEGER NOT NULL DEFAULT 0,
    rn_macrosomico              INTEGER NOT NULL DEFAULT 0,
    trastorno_mental            INTEGER NOT NULL DEFAULT 0,
    obesidad                    INTEGER NOT NULL DEFAULT 0,
    desnutricion_cronica        INTEGER NOT NULL DEFAULT 0,
    intergenesis_menor_2a       INTEGER NOT NULL DEFAULT 0,
    its_distintas               INTEGER NOT NULL DEFAULT 0,
    vih_sida                    INTEGER NOT NULL DEFAULT 0,
    otras_infecciones           INTEGER NOT NULL DEFAULT 0,
    rh_negativo                 INTEGER NOT NULL DEFAULT 0,
    tabaquismo                  INTEGER NOT NULL DEFAULT 0,
    alcoholismo                 INTEGER NOT NULL DEFAULT 0,
    sustancias_psicoactivas     INTEGER NOT NULL DEFAULT 0,
    deficiencias_socioeconomicas INTEGER NOT NULL DEFAULT 0,
    sifilis                     INTEGER NOT NULL DEFAULT 0,
    hepatitis_b                 INTEGER NOT NULL DEFAULT 0,
    otros_factores_riesgo       INTEGER NOT NULL DEFAULT 0,
    desc_otros_factores         VARCHAR(300),
    gingivitis_periodontitis    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS complicacion_embarazo (
    id_caso                    INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    preeclampsia               INTEGER NOT NULL DEFAULT 0,
    eclampsia                  INTEGER NOT NULL DEFAULT 0,
    sindrome_hellp             INTEGER NOT NULL DEFAULT 0,
    diabetes_gestacional       INTEGER NOT NULL DEFAULT 0,
    sepsis                     INTEGER NOT NULL DEFAULT 0,
    hemorragia_1er_trimestre   INTEGER NOT NULL DEFAULT 0,
    hemorragia_2do_trimestre   INTEGER NOT NULL DEFAULT 0,
    hemorragia_3er_trimestre   INTEGER NOT NULL DEFAULT 0,
    desproporcion_cefalo_pelv  INTEGER NOT NULL DEFAULT 0,
    retardo_crecimiento_iu     INTEGER NOT NULL DEFAULT 0,
    enfermedad_autoinmune      INTEGER NOT NULL DEFAULT 0,
    malaria                    INTEGER NOT NULL DEFAULT 0,
    embarazo_no_deseado        INTEGER NOT NULL DEFAULT 0,
    violencia_gestante         INTEGER NOT NULL DEFAULT 0,
    otras_complicaciones       INTEGER NOT NULL DEFAULT 0,
    desc_otras_complicaciones  VARCHAR(300),
    gestacion_violencia_sexual INTEGER NOT NULL DEFAULT 0,
    feto_incompatible_vida     INTEGER NOT NULL DEFAULT 0,
    sintomas_depresivos        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS control_prenatal (
    id_caso                INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    num_cpn                SMALLINT,
    semana_inicio_cpn      SMALLINT,
    id_personal_cpn        SMALLINT REFERENCES cat_personal_salud(id),
    id_nivel_atencion_cpn  SMALLINT REFERENCES cat_nivel_atencion(id),
    id_remisiones          SMALLINT NOT NULL REFERENCES cat_remisiones(id),
    compl_feto_rn_cie10    VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS antecedente_parto_puerperio (
    id_caso                 INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    id_momento_muerte       SMALLINT NOT NULL REFERENCES cat_momento_muerte(id),
    semana_gestacion_muerte SMALLINT,
    fecha_parto             DATE,
    hora_parto              TIME,
    id_tipo_parto           SMALLINT REFERENCES cat_tipo_parto(id),
    id_atendido_por         SMALLINT REFERENCES cat_personal_salud(id),
    otro_atencion_parto     VARCHAR(100),
    id_nivel_atencion_parto SMALLINT REFERENCES cat_nivel_atencion(id)
);

CREATE TABLE IF NOT EXISTS causa_muerte (
    id_caso           INTEGER PRIMARY KEY REFERENCES caso_mortalidad(id_caso),
    causa_basica_cie10 VARCHAR(10) NOT NULL,
    id_fuente_causa    SMALLINT NOT NULL REFERENCES cat_fuente_causa_muerte(id),
    demora_1           INTEGER NOT NULL DEFAULT 0,
    demora_2           INTEGER NOT NULL DEFAULT 0,
    demora_3           INTEGER NOT NULL DEFAULT 0,
    demora_4           INTEGER NOT NULL DEFAULT 0
);
"""

# ---------------------------------------------------------------------------
# Datos de catálogos estándar SIVIGILA (INS Colombia)
# ---------------------------------------------------------------------------

_CATALOG_DATA = """
INSERT OR IGNORE INTO cat_tipo_id VALUES
    (1,'CC','Cédula de ciudadanía'),
    (2,'CE','Cédula de extranjería'),
    (3,'PA','Pasaporte'),
    (4,'TI','Tarjeta de identidad'),
    (5,'RC','Registro civil'),
    (6,'MS','Menor sin identificación'),
    (7,'AS','Adulto sin identificación'),
    (8,'PPT','Permiso por protección temporal'),
    (9,'PE','Permiso especial de permanencia');

INSERT OR IGNORE INTO cat_convivencia VALUES
    (1,'Solo/a'),
    (2,'Con pareja'),
    (3,'Con familia'),
    (4,'Con otros'),
    (5,'No aplica'),
    (9,'Sin dato');

INSERT OR IGNORE INTO cat_escolaridad VALUES
    (1,'Ninguno'),
    (2,'Preescolar'),
    (3,'Primaria incompleta'),
    (4,'Primaria completa'),
    (5,'Secundaria incompleta'),
    (6,'Secundaria completa'),
    (7,'Técnico/Tecnológico'),
    (8,'Universitario'),
    (9,'Posgrado');

INSERT OR IGNORE INTO cat_regulacion_fecundidad VALUES
    (1,'Ninguno'),
    (2,'Anticonceptivo oral'),
    (3,'Anticonceptivo inyectable'),
    (4,'DIU'),
    (5,'Implante subdérmico'),
    (6,'Preservativo masculino'),
    (7,'Ligadura de trompas'),
    (8,'Vasectomía'),
    (9,'Otro método'),
    (10,'No sabe');

INSERT OR IGNORE INTO cat_sitio_defuncion VALUES
    (1,'Hospital/Clínica'),
    (2,'Centro/Puesto de salud'),
    (3,'Domicilio'),
    (4,'Vía pública'),
    (5,'Otro');

INSERT OR IGNORE INTO cat_momento_muerte VALUES
    (1,'Durante el embarazo'),
    (2,'Durante el parto'),
    (3,'Puerperio (hasta 42 días)'),
    (4,'Tardía (43 días - 1 año)');

INSERT OR IGNORE INTO cat_remisiones VALUES
    (1,'Si'),
    (2,'No'),
    (3,'No aplica');

INSERT OR IGNORE INTO cat_tipo_parto VALUES
    (1,'Vaginal espontáneo'),
    (2,'Vaginal instrumentado'),
    (3,'Cesárea'),
    (4,'Aborto');

INSERT OR IGNORE INTO cat_terminacion_gestacion VALUES
    (1,'Parto'),
    (2,'Cesárea'),
    (3,'Aborto espontáneo'),
    (4,'Aborto inducido'),
    (5,'Parto prematuro');

INSERT OR IGNORE INTO cat_personal_salud VALUES
    (1,'Médico/a'),
    (2,'Enfermero/a'),
    (3,'Auxiliar de enfermería'),
    (4,'Partera tradicional'),
    (5,'Otro personal');

INSERT OR IGNORE INTO cat_nivel_atencion VALUES
    (1,'I'),
    (2,'II'),
    (3,'III'),
    (4,'IV');

INSERT OR IGNORE INTO cat_fuente_causa_muerte VALUES
    (1,'Autopsia verbal'),
    (2,'Historia clínica'),
    (3,'Certificado de defunción'),
    (4,'Ambas');

INSERT OR IGNORE INTO cat_grupo_causa VALUES
    (1,'Causa directa'),
    (2,'Causa indirecta'),
    (3,'Causa no obstétrica'),
    (4,'Causa no clasificada');
"""


def forward(apps, schema_editor):
    """Crea tablas SIVIGILA y puebla catálogos solo si no existen.

    Solo se ejecuta en SQLite (desarrollo local). En MySQL y PostgreSQL
    las tablas SIVIGILA ya existen en el esquema externo.
    """
    vendor = schema_editor.connection.vendor
    conn = schema_editor.connection

    # En MySQL y PostgreSQL las tablas SIVIGILA ya existen
    if vendor in ('mysql', 'postgresql'):
        return

    with conn.cursor() as cursor:
        for statement in _CREATE_TABLES.strip().split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

        for statement in _CATALOG_DATA.strip().split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)


def backward(apps, schema_editor):
    """No revertir en producción; en SQLite solo borramos las tablas de datos."""
    if schema_editor.connection.vendor == 'mysql':
        return

    tables = [
        'causa_muerte', 'antecedente_parto_puerperio', 'control_prenatal',
        'complicacion_embarazo', 'antecedente_riesgo', 'antecedente_materno',
        'caso_mortalidad', 'causas_morbilidad', 'manejo_hospitalario',
        'criterios_manejo', 'criterios_falla_organica', 'criterios_enfermedad',
        'antecedentes_obstetricos', 'referencia', 'caso_morbilidad', 'paciente',
        'cat_grupo_causa', 'cat_fuente_causa_muerte', 'cat_nivel_atencion',
        'cat_personal_salud', 'cat_terminacion_gestacion', 'cat_tipo_parto',
        'cat_remisiones', 'cat_momento_muerte', 'cat_sitio_defuncion',
        'cat_regulacion_fecundidad', 'cat_escolaridad', 'cat_convivencia',
        'cat_tipo_id',
    ]
    with schema_editor.connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_casomortalidad_antecedentesobstetricos_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
