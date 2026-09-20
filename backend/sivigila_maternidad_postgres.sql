-- =====================================================================
--  SIVIGILA – VIGILANCIA EN SALUD MATERNA
--  Base de datos unificada: Morbilidad Materna Extrema (549)
--                         + Mortalidad Materna (550)
--  Motor: PostgreSQL 14+
--  Modelo: Paciente único compartido entre ambos módulos
-- =====================================================================
--
--  INSTRUCCIONES DE EJECUCIÓN EN DBEAVER:
--    Paso 1 – Conectado a la base "postgres" (u otra existente),
--             ejecutar SOLO las dos líneas DROP/CREATE de abajo.
--    Paso 2 – En DBeaver, cambiar la conexión activa a
--             "sivigila_maternidad" y ejecutar el resto del script.
--
-- =====================================================================

DROP DATABASE IF EXISTS sivigila_maternidad;
CREATE DATABASE sivigila_maternidad
    ENCODING 'UTF8';

-- =====================================================================
-- SECCIÓN 1 · CATÁLOGOS COMPARTIDOS
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1.1 Tipos de identificación
-- ---------------------------------------------------------------------
CREATE TABLE cat_tipo_id (
    id           SMALLINT      PRIMARY KEY,
    codigo       VARCHAR(5)    NOT NULL UNIQUE,
    descripcion  VARCHAR(50)   NOT NULL
);

INSERT INTO cat_tipo_id VALUES
    (1,'CC' ,'Cédula de Ciudadanía'),
    (2,'CE' ,'Cédula de Extranjería'),
    (3,'PA' ,'Pasaporte'),
    (4,'PPT','Permiso por Protección Temporal'),
    (5,'TI' ,'Tarjeta de Identidad'),
    (6,'RC' ,'Registro Civil'),
    (7,'MS' ,'Menor sin ID'),
    (8,'AS' ,'Adulto sin ID');

-- ---------------------------------------------------------------------
-- 1.2 Sitio de defunción
-- ---------------------------------------------------------------------
CREATE TABLE cat_sitio_defuncion (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(60)   NOT NULL
);

INSERT INTO cat_sitio_defuncion VALUES
    (1,'IPS (hospital/clínica)'),
    (2,'IPS (centro/puesto de salud)'),
    (3,'Lugar de trabajo'),
    (4,'Vía pública'),
    (5,'Durante el traslado'),
    (6,'Domicilio'),
    (7,'Otro');

-- ---------------------------------------------------------------------
-- 1.3 Convivencia
-- ---------------------------------------------------------------------
CREATE TABLE cat_convivencia (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_convivencia VALUES
    (1,'Cónyuge'),(2,'Familia'),(3,'Sola'),(4,'Otro');

-- ---------------------------------------------------------------------
-- 1.4 Escolaridad
-- ---------------------------------------------------------------------
CREATE TABLE cat_escolaridad (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_escolaridad VALUES
    (1,'Ninguna'),(2,'Primaria'),(3,'Secundaria'),
    (4,'Superior'),(5,'Sin información');

-- ---------------------------------------------------------------------
-- 1.5 Regulación de fecundidad
-- ---------------------------------------------------------------------
CREATE TABLE cat_regulacion_fecundidad (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(50)   NOT NULL
);

INSERT INTO cat_regulacion_fecundidad VALUES
    (1,'No usó métodos por desconocimiento'),
    (2,'No usó métodos por acceso'),
    (3,'No usó métodos porque no deseaba'),
    (4,'Natural'),(5,'Dispositivo intrauterino'),(6,'Hormonal'),
    (7,'Barrera'),(8,'Quirúrgico'),(9,'Otro');

-- ---------------------------------------------------------------------
-- 1.6 Nivel de atención
-- ---------------------------------------------------------------------
CREATE TABLE cat_nivel_atencion (
    id     SMALLINT  PRIMARY KEY,
    nivel  CHAR(3)   NOT NULL UNIQUE
);

INSERT INTO cat_nivel_atencion VALUES (1,'I'),(2,'II'),(3,'III'),(4,'IV');

-- ---------------------------------------------------------------------
-- 1.7 Personal de salud
-- ---------------------------------------------------------------------
CREATE TABLE cat_personal_salud (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_personal_salud VALUES
    (1,'Médico general'),(2,'Médico obstetra'),
    (3,'Enfermera'),(4,'Aux. enfermería'),(5,'Promotor'),
    (6,'Partera'),(7,'Otro');

-- ---------------------------------------------------------------------
-- 1.8 Momento de la muerte
-- ---------------------------------------------------------------------
CREATE TABLE cat_momento_muerte (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_momento_muerte VALUES
    (1,'Gestación'),
    (2,'Parto'),
    (3,'Puerperio < 24 horas'),
    (4,'Puerperio > 24 horas');

-- ---------------------------------------------------------------------
-- 1.9 Tipo de parto
-- ---------------------------------------------------------------------
CREATE TABLE cat_tipo_parto (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(20)   NOT NULL
);

INSERT INTO cat_tipo_parto VALUES
    (1,'Vaginal'),(2,'Cesárea'),(3,'Instrumentado'),(4,'Ignorado');

-- ---------------------------------------------------------------------
-- 1.10 Fuente de la causa de muerte
-- ---------------------------------------------------------------------
CREATE TABLE cat_fuente_causa_muerte (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_fuente_causa_muerte VALUES
    (1,'Historia clínica'),(2,'Autopsia verbal'),(3,'Necropsia');

-- ---------------------------------------------------------------------
-- 1.11 Remisiones
-- ---------------------------------------------------------------------
CREATE TABLE cat_remisiones (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(15)   NOT NULL
);

INSERT INTO cat_remisiones VALUES (1,'Sí'),(2,'No'),(3,'No aplica');

-- ---------------------------------------------------------------------
-- 1.12 Terminación de la gestación  (módulo morbilidad)
-- ---------------------------------------------------------------------
CREATE TABLE cat_terminacion_gestacion (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_terminacion_gestacion VALUES
    (1,'Aborto'),(2,'Parto'),(3,'Parto instrumentado'),
    (4,'Cesárea'),(5,'Continúa embarazada');

-- ---------------------------------------------------------------------
-- 1.13 Grupo de causa principal (CIE-10 agrupado)
-- ---------------------------------------------------------------------
CREATE TABLE cat_grupo_causa (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(60)   NOT NULL
);

INSERT INTO cat_grupo_causa VALUES
    (1,'Trastornos hipertensivos'),
    (2,'Hemorragia obstétrica'),
    (3,'Sepsis de origen obstétrico'),
    (4,'Aborto'),
    (5,'Complicaciones del parto y puerperio'),
    (6,'Enfermedades concurrentes'),
    (7,'Causas no obstétricas'),
    (8,'Otras');

-- ---------------------------------------------------------------------
-- 1.14 Zona de residencia
-- ---------------------------------------------------------------------
CREATE TABLE cat_zona_residencia (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(10)   NOT NULL
);

INSERT INTO cat_zona_residencia VALUES
    (1,'Urbana'),(2,'Rural');

-- ---------------------------------------------------------------------
-- 1.15 Población vulnerable
-- ---------------------------------------------------------------------
CREATE TABLE cat_poblacion_vulnerable (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(30)   NOT NULL
);

INSERT INTO cat_poblacion_vulnerable VALUES
    (1,'Ninguna'),(2,'Migrante'),(3,'Indígena'),(4,'Afro'),
    (5,'Discapacidad'),(6,'Víctima de conflicto'),(7,'Desplazada');

-- ---------------------------------------------------------------------
-- 1.16 Etnia
-- ---------------------------------------------------------------------
CREATE TABLE cat_etnia (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(20)   NOT NULL
);

INSERT INTO cat_etnia VALUES
    (1,'Ninguna'),(2,'Indígena'),(3,'Afrocolombiana'),
    (4,'Rrom'),(5,'Raizal'),(6,'Otra');

-- ---------------------------------------------------------------------
-- 1.17 Tipo de afiliación en salud
-- ---------------------------------------------------------------------
CREATE TABLE cat_tipo_afiliacion (
    id           SMALLINT      PRIMARY KEY,
    descripcion  VARCHAR(20)   NOT NULL
);

INSERT INTO cat_tipo_afiliacion VALUES
    (1,'Contributivo'),(2,'Subsidiado'),(3,'No afiliada');

-- =====================================================================
-- SECCIÓN 2 · PACIENTE (ENTIDAD CENTRAL COMPARTIDA)
-- =====================================================================
CREATE TABLE paciente (
    id_paciente        INT           GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombres_apellidos  VARCHAR(200)  NOT NULL,
    id_tipo_id         SMALLINT      NOT NULL,
    numero_id          VARCHAR(30)   NOT NULL,
    fecha_nacimiento   DATE          NULL,
    creado_en          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_paciente_numero_id UNIQUE (numero_id),
    CONSTRAINT fk_paciente_tipo_id
        FOREIGN KEY (id_tipo_id) REFERENCES cat_tipo_id(id)
);

CREATE INDEX idx_paciente_numero ON paciente(numero_id);
CREATE INDEX idx_paciente_nombre ON paciente(nombres_apellidos);

-- =====================================================================
-- SECCIÓN 3 · MÓDULO MORBILIDAD MATERNA EXTREMA (Cód. INS 549)
-- =====================================================================

-- 3.1 Caso de morbilidad ----------------------------------------------
CREATE TABLE caso_morbilidad (
    id_caso         INT         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente     INT         NOT NULL,
    fecha_egreso    DATE        NULL,
    creado_en       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_morb_paciente
        FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente)
);

CREATE INDEX idx_morb_paciente     ON caso_morbilidad(id_paciente);
CREATE INDEX idx_morb_fecha_egreso ON caso_morbilidad(fecha_egreso);

-- 3.2 Referencia / remisión -------------------------------------------
CREATE TABLE referencia (
    id_referencia      INT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso            INT          NOT NULL,
    remitida           BOOLEAN      NOT NULL,
    institucion_ref_1  VARCHAR(200) NULL,
    institucion_ref_2  VARCHAR(200) NULL,
    tiempo_remision_h  DECIMAL(6,1) NULL,
    CONSTRAINT fk_ref_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso)
);

-- 3.3 Antecedentes obstétricos ----------------------------------------
CREATE TABLE antecedentes_obstetricos (
    id_antecedente            INT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso                   INT       NOT NULL,
    num_gestaciones           SMALLINT,
    partos_vaginales          SMALLINT,
    cesareas                  SMALLINT,
    abortos                   SMALLINT,
    molas                     SMALLINT,
    ectopicos                 SMALLINT,
    muertos                   SMALLINT,
    vivos                     SMALLINT,
    fecha_ultima_gestacion    DATE,
    id_regulacion_fecundidad  SMALLINT,
    num_controles_prenatales  SMALLINT,
    semanas_inicio_cpn        SMALLINT,
    id_terminacion_gestacion  SMALLINT,
    edad_gestacional_sem      SMALLINT,
    momento_ocurrencia        VARCHAR(8)  CHECK (momento_ocurrencia IN ('Antes','Durante','Despues')),
    estado_recien_nacido      VARCHAR(6)  CHECK (estado_recien_nacido IN ('Vivo','Muerto')),
    multiplicidad             BOOLEAN,
    peso_rn_gramos            SMALLINT,
    CONSTRAINT fk_ant_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso),
    CONSTRAINT fk_ant_regul
        FOREIGN KEY (id_regulacion_fecundidad)
        REFERENCES cat_regulacion_fecundidad(id),
    CONSTRAINT fk_ant_termin
        FOREIGN KEY (id_terminacion_gestacion)
        REFERENCES cat_terminacion_gestacion(id),
    CONSTRAINT chk_ant_gest      CHECK (num_gestaciones  BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_pvag      CHECK (partos_vaginales BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_cesa      CHECK (cesareas         BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_abort     CHECK (abortos          BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_molas     CHECK (molas            BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_ecto      CHECK (ectopicos        BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_muert     CHECK (muertos          BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_vivos     CHECK (vivos            BETWEEN 0 AND 19),
    CONSTRAINT chk_ant_ncpn      CHECK (num_controles_prenatales BETWEEN 0 AND 50),
    CONSTRAINT chk_ant_scpn      CHECK (semanas_inicio_cpn BETWEEN 0 AND 40),
    CONSTRAINT chk_ant_egest     CHECK (edad_gestacional_sem BETWEEN 1 AND 50),
    CONSTRAINT chk_ant_pesorn    CHECK (peso_rn_gramos BETWEEN 500 AND 7000)
);

-- 3.4 Criterios de enfermedad (7.1) -----------------------------------
CREATE TABLE criterios_enfermedad (
    id_criterio_enf          INT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso                  INT      NOT NULL,
    eclampsia                BOOLEAN  NOT NULL DEFAULT FALSE,
    sepsis_sistemica_severa  BOOLEAN  NOT NULL DEFAULT FALSE,
    hemorragia_obstetrica    BOOLEAN  NOT NULL DEFAULT FALSE,
    preeclampsia             BOOLEAN  NOT NULL DEFAULT FALSE,
    ruptura_uterina          BOOLEAN  NOT NULL DEFAULT FALSE,
    aborto_septico           BOOLEAN  NOT NULL DEFAULT FALSE,
    embarazo_ectopico        BOOLEAN  NOT NULL DEFAULT FALSE,
    autoinmune               BOOLEAN  NOT NULL DEFAULT FALSE,
    hematologica             BOOLEAN  NOT NULL DEFAULT FALSE,
    oncologica               BOOLEAN  NOT NULL DEFAULT FALSE,
    endocrino_metabolicas    BOOLEAN  NOT NULL DEFAULT FALSE,
    renales                  BOOLEAN  NOT NULL DEFAULT FALSE,
    gastrointestinales       BOOLEAN  NOT NULL DEFAULT FALSE,
    tromboembolicos          BOOLEAN  NOT NULL DEFAULT FALSE,
    cardiocerebrovasculares  BOOLEAN  NOT NULL DEFAULT FALSE,
    otras_enfermedades       BOOLEAN  NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_cenf_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso)
);

-- 3.5 Criterios de falla orgánica (7.2) -------------------------------
CREATE TABLE criterios_falla_organica (
    id_criterio_falla   INT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso             INT      NOT NULL,
    falla_cardiaca      BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_vascular      BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_renal         BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_hepatica      BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_metabolica    BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_cerebral      BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_respiratoria  BOOLEAN  NOT NULL DEFAULT FALSE,
    falla_coagulacion   BOOLEAN  NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_cfo_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso)
);

-- 3.6 Criterios de manejo + lesiones externas (7.3 y 7.4) -------------
CREATE TABLE criterios_manejo (
    id_criterio_manejo       INT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso                  INT          NOT NULL,
    ingreso_uci              BOOLEAN      NOT NULL DEFAULT FALSE,
    cirugia_adicional        BOOLEAN      NOT NULL DEFAULT FALSE,
    transfusion              BOOLEAN      NOT NULL DEFAULT FALSE,
    total_criterios          SMALLINT,
    accidente                BOOLEAN      NOT NULL DEFAULT FALSE,
    intoxicacion_accidental  BOOLEAN      NOT NULL DEFAULT FALSE,
    intento_suicida          BOOLEAN      NOT NULL DEFAULT FALSE,
    victima_violencia        BOOLEAN      NOT NULL DEFAULT FALSE,
    otros_eventos_sp         BOOLEAN      NOT NULL DEFAULT FALSE,
    cual_evento_sp           VARCHAR(200),
    CONSTRAINT fk_cman_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso),
    CONSTRAINT chk_total_crit CHECK (total_criterios BETWEEN 1 AND 14)
);

CREATE INDEX idx_manejo_uci ON criterios_manejo(ingreso_uci);

-- 3.7 Manejo hospitalario ---------------------------------------------
CREATE TABLE manejo_hospitalario (
    id_manejo               INT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso                 INT          NOT NULL,
    dias_estancia_hosp      SMALLINT,
    dias_estancia_uci       SMALLINT,
    unidades_transfundidas  SMALLINT,
    cirugia_1               SMALLINT,
    cirugia_1_cual          VARCHAR(200),
    cirugia_2               SMALLINT,
    cirugia_2_cual          VARCHAR(200),
    CONSTRAINT fk_mh_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso),
    CONSTRAINT chk_mh_estancia    CHECK (dias_estancia_hosp     >= 1),
    CONSTRAINT chk_mh_uci         CHECK (dias_estancia_uci      >= 1),
    CONSTRAINT chk_mh_trans       CHECK (unidades_transfundidas >= 3),
    CONSTRAINT chk_mh_cir1        CHECK (cirugia_1 BETWEEN 1 AND 4),
    CONSTRAINT chk_mh_cir2        CHECK (cirugia_2 BETWEEN 1 AND 4)
);

-- 3.8 Causas de morbilidad (CIE-10) -----------------------------------
CREATE TABLE causas_morbilidad (
    id_causa               INT          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_caso                INT          NOT NULL,
    causa_principal_cie10  VARCHAR(10)  NOT NULL,
    id_grupo_causa         SMALLINT     NULL,
    causa_asociada_2       VARCHAR(10),
    causa_asociada_3       VARCHAR(10),
    causa_asociada_4       VARCHAR(10),
    CONSTRAINT fk_cm_caso
        FOREIGN KEY (id_caso) REFERENCES caso_morbilidad(id_caso),
    CONSTRAINT fk_cm_grupo
        FOREIGN KEY (id_grupo_causa) REFERENCES cat_grupo_causa(id)
);

CREATE INDEX idx_causa_cie10_morb ON causas_morbilidad(causa_principal_cie10);
CREATE INDEX idx_causa_grupo_morb ON causas_morbilidad(id_grupo_causa);

-- =====================================================================
-- SECCIÓN 4 · MÓDULO MORTALIDAD MATERNA (Cód. INS 550)
-- =====================================================================

-- 4.1 Caso mortalidad materna -----------------------------------------
CREATE TABLE caso_mortalidad (
    id_caso             INT         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente         INT         NOT NULL,
    id_sitio_defuncion  SMALLINT    NOT NULL,
    fecha_defuncion     DATE        NULL,
    creado_en           TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mort_paciente
        FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente),
    CONSTRAINT fk_mort_sitio
        FOREIGN KEY (id_sitio_defuncion) REFERENCES cat_sitio_defuncion(id)
);

CREATE INDEX idx_mort_paciente ON caso_mortalidad(id_paciente);
CREATE INDEX idx_mort_fecha    ON caso_mortalidad(fecha_defuncion);

-- 4.2 Antecedente materno ---------------------------------------------
CREATE TABLE antecedente_materno (
    id_caso            INT       PRIMARY KEY,
    id_convivencia     SMALLINT  NOT NULL,
    otro_convivencia   VARCHAR(100),
    id_escolaridad     SMALLINT  NOT NULL,
    id_regulacion_fec  SMALLINT  NOT NULL,
    gestaciones        SMALLINT,
    partos_vaginales   SMALLINT,
    cesareas           SMALLINT,
    nacidos_muertos    SMALLINT,
    hijos_vivos        SMALLINT,
    abortos            SMALLINT,
    CONSTRAINT fk_am_caso
        FOREIGN KEY (id_caso) REFERENCES caso_mortalidad(id_caso),
    CONSTRAINT fk_am_conv  FOREIGN KEY (id_convivencia)    REFERENCES cat_convivencia(id),
    CONSTRAINT fk_am_esc   FOREIGN KEY (id_escolaridad)    REFERENCES cat_escolaridad(id),
    CONSTRAINT fk_am_reg   FOREIGN KEY (id_regulacion_fec) REFERENCES cat_regulacion_fecundidad(id),
    CONSTRAINT chk_am_gest    CHECK (gestaciones      BETWEEN 1 AND 20),
    CONSTRAINT chk_am_pvag    CHECK (partos_vaginales BETWEEN 0 AND 20),
    CONSTRAINT chk_am_cesa    CHECK (cesareas         BETWEEN 0 AND 20),
    CONSTRAINT chk_am_nmuert  CHECK (nacidos_muertos  BETWEEN 0 AND 20),
    CONSTRAINT chk_am_hvivos  CHECK (hijos_vivos      BETWEEN 0 AND 20),
    CONSTRAINT chk_am_abort   CHECK (abortos          BETWEEN 0 AND 20)
);

-- 4.3 Antecedentes de riesgo (7.1) ------------------------------------
CREATE TABLE antecedente_riesgo (
    id_caso                       INT      PRIMARY KEY,
    sin_antecedentes              BOOLEAN  NOT NULL DEFAULT FALSE,
    hipertension_cronica          BOOLEAN  NOT NULL DEFAULT FALSE,
    cardiopatias                  BOOLEAN  NOT NULL DEFAULT FALSE,
    diabetes                      BOOLEAN  NOT NULL DEFAULT FALSE,
    mola_hidatiforme              BOOLEAN  NOT NULL DEFAULT FALSE,
    rn_pretermino                 BOOLEAN  NOT NULL DEFAULT FALSE,
    rn_bajo_peso                  BOOLEAN  NOT NULL DEFAULT FALSE,
    rn_macrosomico                BOOLEAN  NOT NULL DEFAULT FALSE,
    trastorno_mental              BOOLEAN  NOT NULL DEFAULT FALSE,
    obesidad                      BOOLEAN  NOT NULL DEFAULT FALSE,
    desnutricion_cronica          BOOLEAN  NOT NULL DEFAULT FALSE,
    intergenesis_menor_2a         BOOLEAN  NOT NULL DEFAULT FALSE,
    its_distintas                 BOOLEAN  NOT NULL DEFAULT FALSE,
    vih_sida                      BOOLEAN  NOT NULL DEFAULT FALSE,
    otras_infecciones             BOOLEAN  NOT NULL DEFAULT FALSE,
    rh_negativo                   BOOLEAN  NOT NULL DEFAULT FALSE,
    tabaquismo                    BOOLEAN  NOT NULL DEFAULT FALSE,
    alcoholismo                   BOOLEAN  NOT NULL DEFAULT FALSE,
    sustancias_psicoactivas       BOOLEAN  NOT NULL DEFAULT FALSE,
    deficiencias_socioeconomicas  BOOLEAN  NOT NULL DEFAULT FALSE,
    sifilis                       BOOLEAN  NOT NULL DEFAULT FALSE,
    hepatitis_b                   BOOLEAN  NOT NULL DEFAULT FALSE,
    otros_factores_riesgo         BOOLEAN  NOT NULL DEFAULT FALSE,
    desc_otros_factores           VARCHAR(300),
    gingivitis_periodontitis      BOOLEAN  NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_ar_caso
        FOREIGN KEY (id_caso) REFERENCES caso_mortalidad(id_caso)
);

-- 4.4 Complicaciones del embarazo actual (7.2) ------------------------
CREATE TABLE complicacion_embarazo (
    id_caso                     INT      PRIMARY KEY,
    preeclampsia                BOOLEAN  NOT NULL DEFAULT FALSE,
    eclampsia                   BOOLEAN  NOT NULL DEFAULT FALSE,
    sindrome_hellp              BOOLEAN  NOT NULL DEFAULT FALSE,
    diabetes_gestacional        BOOLEAN  NOT NULL DEFAULT FALSE,
    sepsis                      BOOLEAN  NOT NULL DEFAULT FALSE,
    hemorragia_1er_trimestre    BOOLEAN  NOT NULL DEFAULT FALSE,
    hemorragia_2do_trimestre    BOOLEAN  NOT NULL DEFAULT FALSE,
    hemorragia_3er_trimestre    BOOLEAN  NOT NULL DEFAULT FALSE,
    desproporcion_cefalo_pelv   BOOLEAN  NOT NULL DEFAULT FALSE,
    retardo_crecimiento_iu      BOOLEAN  NOT NULL DEFAULT FALSE,
    enfermedad_autoinmune       BOOLEAN  NOT NULL DEFAULT FALSE,
    malaria                     BOOLEAN  NOT NULL DEFAULT FALSE,
    embarazo_no_deseado         BOOLEAN  NOT NULL DEFAULT FALSE,
    violencia_gestante          BOOLEAN  NOT NULL DEFAULT FALSE,
    otras_complicaciones        BOOLEAN  NOT NULL DEFAULT FALSE,
    desc_otras_complicaciones   VARCHAR(300),
    gestacion_violencia_sexual  BOOLEAN  NOT NULL DEFAULT FALSE,
    feto_incompatible_vida      BOOLEAN  NOT NULL DEFAULT FALSE,
    sintomas_depresivos         BOOLEAN  NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_ce_caso
        FOREIGN KEY (id_caso) REFERENCES caso_mortalidad(id_caso)
);

-- 4.5 Control prenatal (8) --------------------------------------------
CREATE TABLE control_prenatal (
    id_caso                INT       PRIMARY KEY,
    num_cpn                SMALLINT,
    semana_inicio_cpn      SMALLINT,
    id_personal_cpn        SMALLINT,
    id_nivel_atencion_cpn  SMALLINT,
    id_remisiones          SMALLINT  NOT NULL,
    compl_feto_rn_cie10    VARCHAR(10),
    CONSTRAINT fk_cp_caso     FOREIGN KEY (id_caso)               REFERENCES caso_mortalidad(id_caso),
    CONSTRAINT fk_cp_personal FOREIGN KEY (id_personal_cpn)       REFERENCES cat_personal_salud(id),
    CONSTRAINT fk_cp_nivel    FOREIGN KEY (id_nivel_atencion_cpn) REFERENCES cat_nivel_atencion(id),
    CONSTRAINT fk_cp_remis    FOREIGN KEY (id_remisiones)         REFERENCES cat_remisiones(id),
    CONSTRAINT chk_cp_num     CHECK (num_cpn           BETWEEN 0 AND 45),
    CONSTRAINT chk_cp_sem     CHECK (semana_inicio_cpn BETWEEN 1 AND 45)
);

-- 4.6 Parto y puerperio (9) -------------------------------------------
CREATE TABLE antecedente_parto_puerperio (
    id_caso                  INT       PRIMARY KEY,
    id_momento_muerte        SMALLINT  NOT NULL,
    semana_gestacion_muerte  SMALLINT,
    fecha_parto              DATE,
    hora_parto               TIME,
    id_tipo_parto            SMALLINT,
    id_atendido_por          SMALLINT,
    otro_atencion_parto      VARCHAR(100),
    id_nivel_atencion_parto  SMALLINT,
    CONSTRAINT fk_pp_caso     FOREIGN KEY (id_caso)                 REFERENCES caso_mortalidad(id_caso),
    CONSTRAINT fk_pp_momento  FOREIGN KEY (id_momento_muerte)       REFERENCES cat_momento_muerte(id),
    CONSTRAINT fk_pp_tipo     FOREIGN KEY (id_tipo_parto)           REFERENCES cat_tipo_parto(id),
    CONSTRAINT fk_pp_atend    FOREIGN KEY (id_atendido_por)         REFERENCES cat_personal_salud(id),
    CONSTRAINT fk_pp_nivel    FOREIGN KEY (id_nivel_atencion_parto) REFERENCES cat_nivel_atencion(id),
    CONSTRAINT chk_pp_semana  CHECK (semana_gestacion_muerte BETWEEN 1 AND 45)
);

CREATE INDEX idx_momento_muerte ON antecedente_parto_puerperio(id_momento_muerte);

-- 4.7 Causa de muerte (10) --------------------------------------------
CREATE TABLE causa_muerte (
    id_caso             INT          PRIMARY KEY,
    causa_basica_cie10  VARCHAR(10)  NOT NULL,
    id_fuente_causa     SMALLINT     NOT NULL,
    demora_1            BOOLEAN      NOT NULL DEFAULT FALSE,
    demora_2            BOOLEAN      NOT NULL DEFAULT FALSE,
    demora_3            BOOLEAN      NOT NULL DEFAULT FALSE,
    demora_4            BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_cmu_caso    FOREIGN KEY (id_caso)         REFERENCES caso_mortalidad(id_caso),
    CONSTRAINT fk_cmu_fuente  FOREIGN KEY (id_fuente_causa) REFERENCES cat_fuente_causa_muerte(id),
    CONSTRAINT chk_causa_cie10_valida CHECK (causa_basica_cie10 NOT LIKE 'P%' AND causa_basica_cie10 NOT IN ('8888', '9999'))
);

CREATE INDEX idx_causa_cie10_mort ON causa_muerte(causa_basica_cie10);

-- =====================================================================
-- SECCIÓN 4B · DATOS SOCIODEMOGRÁFICOS (compartido morb/mort)
-- =====================================================================

CREATE TABLE datos_sociodemograficos (
    id                     INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    caso_morbilidad_id     INT       NULL,
    caso_mortalidad_id     INT       NULL,
    id_zona_residencia     SMALLINT,
    id_poblacion_vulnerable SMALLINT,
    id_etnia               SMALLINT,
    id_tipo_afiliacion     SMALLINT,
    CONSTRAINT fk_ds_morb
        FOREIGN KEY (caso_morbilidad_id) REFERENCES caso_morbilidad(id_caso),
    CONSTRAINT fk_ds_mort
        FOREIGN KEY (caso_mortalidad_id) REFERENCES caso_mortalidad(id_caso),
    CONSTRAINT fk_ds_zona
        FOREIGN KEY (id_zona_residencia) REFERENCES cat_zona_residencia(id),
    CONSTRAINT fk_ds_pobvuln
        FOREIGN KEY (id_poblacion_vulnerable) REFERENCES cat_poblacion_vulnerable(id),
    CONSTRAINT fk_ds_etnia
        FOREIGN KEY (id_etnia) REFERENCES cat_etnia(id),
    CONSTRAINT fk_ds_afiliacion
        FOREIGN KEY (id_tipo_afiliacion) REFERENCES cat_tipo_afiliacion(id),
    CONSTRAINT chk_ds_un_caso
        CHECK (
            (caso_morbilidad_id IS NOT NULL AND caso_mortalidad_id IS NULL) OR
            (caso_morbilidad_id IS NULL AND caso_mortalidad_id IS NOT NULL)
        )
);

CREATE INDEX idx_ds_caso_morb ON datos_sociodemograficos(caso_morbilidad_id);
CREATE INDEX idx_ds_caso_mort ON datos_sociodemograficos(caso_mortalidad_id);

-- =====================================================================
-- SECCIÓN 5 · VISTAS CONSOLIDADAS
-- =====================================================================

-- 5.1 Vista completa de mortalidad materna ----------------------------
CREATE OR REPLACE VIEW v_mortalidad_completa AS
SELECT  c.id_caso,
        p.nombres_apellidos,
        ti.codigo            AS tipo_id,
        p.numero_id,
        p.fecha_nacimiento,
        EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer AS edad,
        sd.descripcion       AS sitio_defuncion,
        c.fecha_defuncion,
        cv.descripcion       AS convivencia, am.otro_convivencia,
        es.descripcion       AS escolaridad,
        rf.descripcion       AS regulacion_fecundidad,
        am.gestaciones, am.partos_vaginales, am.cesareas,
        am.nacidos_muertos, am.hijos_vivos, am.abortos,
        ar.sin_antecedentes, ar.hipertension_cronica, ar.diabetes,
        ar.vih_sida, ar.tabaquismo, ar.deficiencias_socioeconomicas,
        ce.preeclampsia, ce.eclampsia, ce.sindrome_hellp, ce.sepsis,
        ce.hemorragia_3er_trimestre, ce.embarazo_no_deseado,
        ce.violencia_gestante,
        cp.num_cpn, cp.semana_inicio_cpn,
        ps_cpn.descripcion   AS cpn_realizado_por,
        na_cpn.nivel         AS nivel_atencion_cpn,
        re.descripcion       AS remisiones_oportunas,
        cp.compl_feto_rn_cie10,
        mm.descripcion       AS momento_muerte,
        pp.semana_gestacion_muerte,
        pp.fecha_parto, pp.hora_parto,
        tp.descripcion       AS tipo_parto,
        ps_parto.descripcion AS parto_atendido_por,
        na_parto.nivel       AS nivel_atencion_parto,
        cm.causa_basica_cie10,
        fc.descripcion       AS fuente_causa_muerte,
        cm.demora_1, cm.demora_2, cm.demora_3, cm.demora_4,
        zr.descripcion       AS zona_residencia,
        pv.descripcion       AS poblacion_vulnerable,
        et.descripcion       AS etnia,
        ta.descripcion       AS tipo_afiliacion
FROM caso_mortalidad c
LEFT JOIN paciente                    p        ON p.id_paciente = c.id_paciente
LEFT JOIN cat_tipo_id                 ti       ON ti.id       = p.id_tipo_id
LEFT JOIN cat_sitio_defuncion         sd       ON sd.id       = c.id_sitio_defuncion
LEFT JOIN antecedente_materno         am       ON am.id_caso  = c.id_caso
LEFT JOIN cat_convivencia             cv       ON cv.id       = am.id_convivencia
LEFT JOIN cat_escolaridad             es       ON es.id       = am.id_escolaridad
LEFT JOIN cat_regulacion_fecundidad   rf       ON rf.id       = am.id_regulacion_fec
LEFT JOIN antecedente_riesgo          ar       ON ar.id_caso  = c.id_caso
LEFT JOIN complicacion_embarazo       ce       ON ce.id_caso  = c.id_caso
LEFT JOIN control_prenatal            cp       ON cp.id_caso  = c.id_caso
LEFT JOIN cat_personal_salud          ps_cpn   ON ps_cpn.id   = cp.id_personal_cpn
LEFT JOIN cat_nivel_atencion          na_cpn   ON na_cpn.id   = cp.id_nivel_atencion_cpn
LEFT JOIN cat_remisiones              re       ON re.id       = cp.id_remisiones
LEFT JOIN antecedente_parto_puerperio pp       ON pp.id_caso  = c.id_caso
LEFT JOIN cat_momento_muerte          mm       ON mm.id       = pp.id_momento_muerte
LEFT JOIN cat_tipo_parto              tp       ON tp.id       = pp.id_tipo_parto
LEFT JOIN cat_personal_salud          ps_parto ON ps_parto.id = pp.id_atendido_por
LEFT JOIN cat_nivel_atencion          na_parto ON na_parto.id = pp.id_nivel_atencion_parto
LEFT JOIN causa_muerte                cm       ON cm.id_caso  = c.id_caso
LEFT JOIN cat_fuente_causa_muerte     fc       ON fc.id       = cm.id_fuente_causa
LEFT JOIN datos_sociodemograficos     ds       ON ds.caso_mortalidad_id = c.id_caso
LEFT JOIN cat_zona_residencia         zr       ON zr.id       = ds.id_zona_residencia
LEFT JOIN cat_poblacion_vulnerable    pv       ON pv.id       = ds.id_poblacion_vulnerable
LEFT JOIN cat_etnia                   et       ON et.id       = ds.id_etnia
LEFT JOIN cat_tipo_afiliacion         ta       ON ta.id       = ds.id_tipo_afiliacion;

-- 5.2 Vista completa de morbilidad materna extrema --------------------
CREATE OR REPLACE VIEW v_morbilidad_completa AS
SELECT  c.id_caso,
        p.nombres_apellidos,
        ti.codigo  AS tipo_id,
        p.numero_id,
        p.fecha_nacimiento,
        EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer AS edad,
        c.fecha_egreso,
        r.remitida, r.institucion_ref_1, r.tiempo_remision_h,
        a.num_gestaciones, a.partos_vaginales, a.cesareas, a.abortos,
        a.num_controles_prenatales, a.edad_gestacional_sem,
        tg.descripcion AS terminacion_gestacion,
        a.estado_recien_nacido, a.peso_rn_gramos,
        ce.eclampsia, ce.preeclampsia, ce.hemorragia_obstetrica,
        ce.sepsis_sistemica_severa, ce.ruptura_uterina,
        cf.falla_cardiaca, cf.falla_renal, cf.falla_hepatica,
        cf.falla_respiratoria, cf.falla_coagulacion,
        cm.ingreso_uci, cm.cirugia_adicional, cm.transfusion,
        cm.total_criterios,
        mh.dias_estancia_hosp, mh.dias_estancia_uci,
        mh.unidades_transfundidas,
        ca.causa_principal_cie10, gc.descripcion AS grupo_causa,
        zr.descripcion       AS zona_residencia,
        pv.descripcion       AS poblacion_vulnerable,
        et.descripcion       AS etnia,
        ta.descripcion       AS tipo_afiliacion
FROM caso_morbilidad c
LEFT JOIN paciente                  p   ON p.id_paciente = c.id_paciente
LEFT JOIN cat_tipo_id               ti  ON ti.id         = p.id_tipo_id
LEFT JOIN referencia                r   ON r.id_caso     = c.id_caso
LEFT JOIN antecedentes_obstetricos  a   ON a.id_caso     = c.id_caso
LEFT JOIN cat_terminacion_gestacion tg  ON tg.id         = a.id_terminacion_gestacion
LEFT JOIN criterios_enfermedad      ce  ON ce.id_caso    = c.id_caso
LEFT JOIN criterios_falla_organica  cf  ON cf.id_caso    = c.id_caso
LEFT JOIN criterios_manejo          cm  ON cm.id_caso    = c.id_caso
LEFT JOIN manejo_hospitalario       mh  ON mh.id_caso    = c.id_caso
LEFT JOIN causas_morbilidad         ca  ON ca.id_caso    = c.id_caso
LEFT JOIN cat_grupo_causa           gc  ON gc.id         = ca.id_grupo_causa
LEFT JOIN datos_sociodemograficos   ds  ON ds.caso_morbilidad_id = c.id_caso
LEFT JOIN cat_zona_residencia       zr  ON zr.id         = ds.id_zona_residencia
LEFT JOIN cat_poblacion_vulnerable  pv  ON pv.id         = ds.id_poblacion_vulnerable
LEFT JOIN cat_etnia                 et  ON et.id         = ds.id_etnia
LEFT JOIN cat_tipo_afiliacion       ta  ON ta.id         = ds.id_tipo_afiliacion;

-- =====================================================================
-- SECCIÓN 6 · DATOS FICTICIOS DE PRUEBA
-- =====================================================================

-- 6.1 Pacientes -------------------------------------------------------
INSERT INTO paciente (nombres_apellidos, id_tipo_id, numero_id, fecha_nacimiento) VALUES
    ('María Fernanda Mosquera Palacios', 1, '1077429815', '1995-03-12'),
    ('Luz Marina Córdoba Rentería',      1, '1077501234', '1988-11-04'),
    ('Yeisi Paola Asprilla Mena',        1, '1077612378', '2001-07-22'),
    ('Sandra Milena Perea Hinestroza',   1, '1077733456', '1992-01-30'),
    ('Diana Carolina Valencia Murillo',  1, '1077854321', '1985-09-18'),
    ('Yurany Andrea Lozano Caicedo',     5, '1077965432', '2006-05-10');

-- 6.2 Casos de MORBILIDAD MATERNA EXTREMA (paciente 1, 2, 3, 6) -------
INSERT INTO caso_morbilidad (id_paciente, fecha_egreso) VALUES
    (1, '2025-08-15'),
    (2, '2025-09-02'),
    (3, '2025-10-20'),
    (6, '2026-01-08');

-- 6.2.1 Referencia / remisión
INSERT INTO referencia (id_caso, remitida, institucion_ref_1, institucion_ref_2, tiempo_remision_h) VALUES
    (1, TRUE,  'Hospital Local Quibdó', 'Hospital San Francisco de Asís', 4.5),
    (2, FALSE,  NULL, NULL, NULL),
    (3, TRUE,  'Centro de Salud Istmina', 'Hospital San Francisco de Asís', 6.0),
    (4, TRUE,  'Hospital Bahía Solano',   'Hospital San Francisco de Asís', 12.0);

-- 6.2.2 Antecedentes obstétricos
INSERT INTO antecedentes_obstetricos
    (id_caso, num_gestaciones, partos_vaginales, cesareas, abortos, molas, ectopicos,
     muertos, vivos, fecha_ultima_gestacion, id_regulacion_fecundidad,
     num_controles_prenatales, semanas_inicio_cpn, id_terminacion_gestacion,
     edad_gestacional_sem, momento_ocurrencia, estado_recien_nacido,
     multiplicidad, peso_rn_gramos)
VALUES
    (1, 3, 1, 1, 0, 0, 0, 0, 2, '2025-08-10', 5, 5, 12, 2, 38, 'Durante', 'Vivo',   FALSE, 3100),
    (2, 2, 1, 0, 1, 0, 0, 0, 1, '2025-08-28', 6, 7, 10, 1, 39, 'Despues', 'Vivo',   FALSE, 2900),
    (3, 1, 0, 0, 0, 0, 0, 0, 0, '2025-10-15', 1, 2, 22, 3, 18, 'Durante', 'Muerto', FALSE,  650),
    (4, 4, 2, 1, 0, 0, 0, 0, 3, '2026-01-05', 8, 6, 14, 2, 37, 'Antes',   'Vivo',   FALSE, 2800);

-- 6.2.3 Criterios de enfermedad
INSERT INTO criterios_enfermedad
    (id_caso, eclampsia, preeclampsia, hemorragia_obstetrica, sepsis_sistemica_severa)
VALUES
    (1, TRUE,  TRUE,  FALSE, FALSE),
    (2, FALSE, FALSE, TRUE,  FALSE),
    (3, FALSE, FALSE, FALSE, TRUE),
    (4, FALSE, TRUE,  TRUE,  FALSE);

-- 6.2.4 Criterios de falla orgánica
INSERT INTO criterios_falla_organica
    (id_caso, falla_renal, falla_hepatica, falla_coagulacion, falla_respiratoria)
VALUES
    (1, TRUE,  TRUE,  FALSE, FALSE),
    (2, FALSE, FALSE, TRUE,  FALSE),
    (3, TRUE,  FALSE, FALSE, TRUE),
    (4, FALSE, FALSE, TRUE,  FALSE);

-- 6.2.5 Criterios de manejo
INSERT INTO criterios_manejo
    (id_caso, ingreso_uci, cirugia_adicional, transfusion, total_criterios,
     victima_violencia)
VALUES
    (1, TRUE,  FALSE, TRUE, 5, FALSE),
    (2, TRUE,  TRUE,  TRUE, 6, FALSE),
    (3, TRUE,  TRUE,  TRUE, 7, FALSE),
    (4, TRUE,  FALSE, TRUE, 5, TRUE);

-- 6.2.6 Manejo hospitalario
INSERT INTO manejo_hospitalario
    (id_caso, dias_estancia_hosp, dias_estancia_uci, unidades_transfundidas,
     cirugia_1, cirugia_1_cual, cirugia_2, cirugia_2_cual)
VALUES
    (1, 8,  3, 4, 1, 'Cesárea de urgencia',     NULL, NULL),
    (2, 12, 5, 6, 2, 'Histerectomía obstétrica', 1,   'Legrado uterino'),
    (3, 15, 7, 5, 3, 'Salpingectomía',           NULL, NULL),
    (4, 9,  4, 3, 1, 'Cesárea de urgencia',      NULL, NULL);

-- 6.2.7 Causas de morbilidad (CIE-10)
INSERT INTO causas_morbilidad
    (id_caso, causa_principal_cie10, id_grupo_causa,
     causa_asociada_2, causa_asociada_3, causa_asociada_4)
VALUES
    (1, 'O15.1', 1, 'O14.1', NULL,    NULL),
    (2, 'O72.1', 2, 'D62',   NULL,    NULL),
    (3, 'O08.0', 4, 'O03.5', 'A41.9', NULL),
    (4, 'O14.0', 1, 'O67.9', NULL,    NULL);

-- 6.3 Casos de MORTALIDAD MATERNA (paciente 4 y 5) --------------------
INSERT INTO caso_mortalidad (id_paciente, id_sitio_defuncion, fecha_defuncion) VALUES
    (4, 1, '2025-11-12'),
    (5, 5, '2025-12-03');

-- 6.3.1 Antecedente materno
INSERT INTO antecedente_materno
    (id_caso, id_convivencia, otro_convivencia, id_escolaridad,
     id_regulacion_fec, gestaciones, partos_vaginales, cesareas,
     nacidos_muertos, hijos_vivos, abortos)
VALUES
    (1, 2, NULL, 3, 5, 4, 2, 1, 0, 3, 0),
    (2, 1, NULL, 2, 1, 5, 3, 1, 1, 3, 1);

-- 6.3.2 Antecedentes de riesgo
INSERT INTO antecedente_riesgo
    (id_caso, hipertension_cronica, diabetes, obesidad,
     deficiencias_socioeconomicas, tabaquismo)
VALUES
    (1, TRUE,  FALSE, TRUE,  TRUE,  FALSE),
    (2, FALSE, TRUE,  FALSE, TRUE,  FALSE);

-- 6.3.3 Complicaciones del embarazo actual
INSERT INTO complicacion_embarazo
    (id_caso, preeclampsia, eclampsia, sindrome_hellp,
     hemorragia_3er_trimestre, sepsis)
VALUES
    (1, TRUE,  TRUE,  TRUE,  FALSE, FALSE),
    (2, FALSE, FALSE, FALSE, TRUE,  TRUE);

-- 6.3.4 Control prenatal
INSERT INTO control_prenatal
    (id_caso, num_cpn, semana_inicio_cpn, id_personal_cpn,
     id_nivel_atencion_cpn, id_remisiones, compl_feto_rn_cie10)
VALUES
    (1, 4, 16, 1, 2, 2, NULL),
    (2, 2, 24, 3, 1, 1, 'O36.4');

-- 6.3.5 Parto y puerperio
INSERT INTO antecedente_parto_puerperio
    (id_caso, id_momento_muerte, semana_gestacion_muerte, fecha_parto, hora_parto,
     id_tipo_parto, id_atendido_por, otro_atencion_parto, id_nivel_atencion_parto)
VALUES
    (1, 3, 36, '2025-11-12', '04:35:00', 2, 2, NULL, 3),
    (2, 1, 32, NULL,         NULL,       4, 6, 'Partera tradicional comunitaria', 1);

-- 6.3.6 Causa de muerte
INSERT INTO causa_muerte
    (id_caso, causa_basica_cie10, id_fuente_causa,
     demora_1, demora_2, demora_3, demora_4)
VALUES
    (1, 'O15.0', 1, FALSE, FALSE, TRUE,  TRUE),
    (2, 'O72.0', 2, TRUE,  TRUE,  TRUE,  FALSE);

-- =====================================================================
-- SECCIÓN 7 · VERIFICACIÓN
-- =====================================================================
-- SELECT * FROM v_morbilidad_completa;
-- SELECT * FROM v_mortalidad_completa;
-- SELECT COUNT(*) AS total_pacientes        FROM paciente;
-- SELECT COUNT(*) AS total_casos_morbilidad FROM caso_morbilidad;
-- SELECT COUNT(*) AS total_casos_mortalidad FROM caso_mortalidad;

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================
