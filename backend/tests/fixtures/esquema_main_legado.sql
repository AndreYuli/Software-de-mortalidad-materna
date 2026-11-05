-- Estructura de la base en la rama main (commit 3ef7b84), para probar
-- scripts/migrar_estructura_anterior.py. Generado con pg_dump desde una base desechable
-- construida con el script SQL de main y el arranque de su backend. No se edita a mano.
--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: antecedente_materno; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.antecedente_materno (
    id_caso integer NOT NULL,
    id_convivencia smallint NOT NULL,
    otro_convivencia character varying(100),
    id_escolaridad smallint NOT NULL,
    id_regulacion_fec smallint NOT NULL,
    gestaciones smallint,
    partos_vaginales smallint,
    cesareas smallint,
    nacidos_muertos smallint,
    hijos_vivos smallint,
    abortos smallint,
    CONSTRAINT chk_am_abort CHECK (((abortos >= 0) AND (abortos <= 20))),
    CONSTRAINT chk_am_cesa CHECK (((cesareas >= 0) AND (cesareas <= 20))),
    CONSTRAINT chk_am_gest CHECK (((gestaciones >= 1) AND (gestaciones <= 20))),
    CONSTRAINT chk_am_hvivos CHECK (((hijos_vivos >= 0) AND (hijos_vivos <= 20))),
    CONSTRAINT chk_am_nmuert CHECK (((nacidos_muertos >= 0) AND (nacidos_muertos <= 20))),
    CONSTRAINT chk_am_pvag CHECK (((partos_vaginales >= 0) AND (partos_vaginales <= 20)))
);


--
-- Name: antecedente_parto_puerperio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.antecedente_parto_puerperio (
    id_caso integer NOT NULL,
    id_momento_muerte smallint NOT NULL,
    semana_gestacion_muerte smallint,
    fecha_parto date,
    hora_parto time without time zone,
    id_tipo_parto smallint,
    id_atendido_por smallint,
    otro_atencion_parto character varying(100),
    id_nivel_atencion_parto smallint,
    CONSTRAINT chk_pp_semana CHECK (((semana_gestacion_muerte >= 1) AND (semana_gestacion_muerte <= 45)))
);


--
-- Name: antecedente_riesgo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.antecedente_riesgo (
    id_caso integer NOT NULL,
    sin_antecedentes boolean DEFAULT false NOT NULL,
    hipertension_cronica boolean DEFAULT false NOT NULL,
    cardiopatias boolean DEFAULT false NOT NULL,
    diabetes boolean DEFAULT false NOT NULL,
    mola_hidatiforme boolean DEFAULT false NOT NULL,
    rn_pretermino boolean DEFAULT false NOT NULL,
    rn_bajo_peso boolean DEFAULT false NOT NULL,
    rn_macrosomico boolean DEFAULT false NOT NULL,
    trastorno_mental boolean DEFAULT false NOT NULL,
    obesidad boolean DEFAULT false NOT NULL,
    desnutricion_cronica boolean DEFAULT false NOT NULL,
    intergenesis_menor_2a boolean DEFAULT false NOT NULL,
    its_distintas boolean DEFAULT false NOT NULL,
    vih_sida boolean DEFAULT false NOT NULL,
    otras_infecciones boolean DEFAULT false NOT NULL,
    rh_negativo boolean DEFAULT false NOT NULL,
    tabaquismo boolean DEFAULT false NOT NULL,
    alcoholismo boolean DEFAULT false NOT NULL,
    sustancias_psicoactivas boolean DEFAULT false NOT NULL,
    deficiencias_socioeconomicas boolean DEFAULT false NOT NULL,
    sifilis boolean DEFAULT false NOT NULL,
    hepatitis_b boolean DEFAULT false NOT NULL,
    otros_factores_riesgo boolean DEFAULT false NOT NULL,
    desc_otros_factores character varying(300),
    gingivitis_periodontitis boolean DEFAULT false NOT NULL
);


--
-- Name: antecedentes_obstetricos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.antecedentes_obstetricos (
    id_antecedente integer NOT NULL,
    id_caso integer NOT NULL,
    num_gestaciones smallint,
    partos_vaginales smallint,
    cesareas smallint,
    abortos smallint,
    molas smallint,
    ectopicos smallint,
    muertos smallint,
    vivos smallint,
    fecha_ultima_gestacion date,
    id_regulacion_fecundidad smallint,
    num_controles_prenatales smallint,
    semanas_inicio_cpn smallint,
    id_terminacion_gestacion smallint,
    edad_gestacional_sem smallint,
    momento_ocurrencia character varying(8),
    estado_recien_nacido character varying(6),
    multiplicidad boolean,
    peso_rn_gramos smallint,
    CONSTRAINT antecedentes_obstetricos_estado_recien_nacido_check CHECK (((estado_recien_nacido)::text = ANY ((ARRAY['Vivo'::character varying, 'Muerto'::character varying])::text[]))),
    CONSTRAINT antecedentes_obstetricos_momento_ocurrencia_check CHECK (((momento_ocurrencia)::text = ANY ((ARRAY['Antes'::character varying, 'Durante'::character varying, 'Despues'::character varying])::text[]))),
    CONSTRAINT chk_ant_abort CHECK (((abortos >= 0) AND (abortos <= 19))),
    CONSTRAINT chk_ant_cesa CHECK (((cesareas >= 0) AND (cesareas <= 19))),
    CONSTRAINT chk_ant_ecto CHECK (((ectopicos >= 0) AND (ectopicos <= 19))),
    CONSTRAINT chk_ant_egest CHECK (((edad_gestacional_sem >= 1) AND (edad_gestacional_sem <= 50))),
    CONSTRAINT chk_ant_gest CHECK (((num_gestaciones >= 0) AND (num_gestaciones <= 19))),
    CONSTRAINT chk_ant_molas CHECK (((molas >= 0) AND (molas <= 19))),
    CONSTRAINT chk_ant_muert CHECK (((muertos >= 0) AND (muertos <= 19))),
    CONSTRAINT chk_ant_ncpn CHECK (((num_controles_prenatales >= 0) AND (num_controles_prenatales <= 50))),
    CONSTRAINT chk_ant_pesorn CHECK (((peso_rn_gramos >= 500) AND (peso_rn_gramos <= 7000))),
    CONSTRAINT chk_ant_pvag CHECK (((partos_vaginales >= 0) AND (partos_vaginales <= 19))),
    CONSTRAINT chk_ant_scpn CHECK (((semanas_inicio_cpn >= 0) AND (semanas_inicio_cpn <= 40))),
    CONSTRAINT chk_ant_vivos CHECK (((vivos >= 0) AND (vivos <= 19)))
);


--
-- Name: antecedentes_obstetricos_id_antecedente_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.antecedentes_obstetricos ALTER COLUMN id_antecedente ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.antecedentes_obstetricos_id_antecedente_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: api_analisis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_analisis (
    id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    nombre_archivo character varying(255) NOT NULL,
    archivo_hash character varying(64) NOT NULL,
    archivo character varying(255) NOT NULL,
    fecha_carga timestamp without time zone NOT NULL,
    total_registros integer NOT NULL,
    resumen json NOT NULL,
    secretaria_codigo character varying(60)
);


--
-- Name: api_analisis_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_analisis_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_analisis_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_analisis_id_seq OWNED BY public.api_analisis.id;


--
-- Name: api_sivigilaimportacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_sivigilaimportacion (
    id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    row_hash character varying(64) NOT NULL,
    event_hash character varying(64) NOT NULL,
    caso_id integer NOT NULL,
    numero_id character varying(30) NOT NULL,
    tipo_identificacion character varying(5) NOT NULL,
    creado_en timestamp without time zone NOT NULL,
    secretaria_codigo character varying(60)
);


--
-- Name: api_sivigilaimportacion_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_sivigilaimportacion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_sivigilaimportacion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_sivigilaimportacion_id_seq OWNED BY public.api_sivigilaimportacion.id;


--
-- Name: api_usuario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_usuario (
    id integer NOT NULL,
    nombre character varying(150) NOT NULL,
    email character varying(254),
    password_hash character varying(255) NOT NULL,
    fecha_registro timestamp without time zone NOT NULL,
    departamento character varying(100),
    secretaria character varying(150),
    secretaria_codigo character varying(60)
);


--
-- Name: api_usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_usuario_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_usuario_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_usuario_id_seq OWNED BY public.api_usuario.id;


--
-- Name: caso_morbilidad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.caso_morbilidad (
    id_caso integer NOT NULL,
    id_paciente integer NOT NULL,
    fecha_egreso date,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    secretaria_codigo character varying(60)
);


--
-- Name: caso_morbilidad_id_caso_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.caso_morbilidad ALTER COLUMN id_caso ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.caso_morbilidad_id_caso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: caso_mortalidad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.caso_mortalidad (
    id_caso integer NOT NULL,
    id_paciente integer NOT NULL,
    id_sitio_defuncion smallint NOT NULL,
    fecha_defuncion date,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    secretaria_codigo character varying(60)
);


--
-- Name: caso_mortalidad_id_caso_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.caso_mortalidad ALTER COLUMN id_caso ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.caso_mortalidad_id_caso_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cat_convivencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_convivencia (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_escolaridad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_escolaridad (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_etnia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_etnia (
    id smallint NOT NULL,
    descripcion character varying(20) NOT NULL
);


--
-- Name: cat_fuente_causa_muerte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_fuente_causa_muerte (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_grupo_causa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_grupo_causa (
    id smallint NOT NULL,
    descripcion character varying(60) NOT NULL
);


--
-- Name: cat_momento_muerte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_momento_muerte (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_nivel_atencion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_nivel_atencion (
    id smallint NOT NULL,
    nivel character(3) NOT NULL
);


--
-- Name: cat_personal_salud; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_personal_salud (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_poblacion_vulnerable; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_poblacion_vulnerable (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_regulacion_fecundidad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_regulacion_fecundidad (
    id smallint NOT NULL,
    descripcion character varying(50) NOT NULL
);


--
-- Name: cat_remisiones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_remisiones (
    id smallint NOT NULL,
    descripcion character varying(15) NOT NULL
);


--
-- Name: cat_sitio_defuncion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_sitio_defuncion (
    id smallint NOT NULL,
    descripcion character varying(60) NOT NULL
);


--
-- Name: cat_terminacion_gestacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_terminacion_gestacion (
    id smallint NOT NULL,
    descripcion character varying(30) NOT NULL
);


--
-- Name: cat_tipo_afiliacion; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_tipo_afiliacion (
    id smallint NOT NULL,
    descripcion character varying(20) NOT NULL
);


--
-- Name: cat_tipo_id; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_tipo_id (
    id smallint NOT NULL,
    codigo character varying(5) NOT NULL,
    descripcion character varying(50) NOT NULL
);


--
-- Name: cat_tipo_parto; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_tipo_parto (
    id smallint NOT NULL,
    descripcion character varying(20) NOT NULL
);


--
-- Name: cat_zona_residencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cat_zona_residencia (
    id smallint NOT NULL,
    descripcion character varying(10) NOT NULL
);


--
-- Name: causa_muerte; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.causa_muerte (
    id_caso integer NOT NULL,
    causa_basica_cie10 character varying(10) NOT NULL,
    id_fuente_causa smallint NOT NULL,
    demora_1 boolean DEFAULT false NOT NULL,
    demora_2 boolean DEFAULT false NOT NULL,
    demora_3 boolean DEFAULT false NOT NULL,
    demora_4 boolean DEFAULT false NOT NULL,
    CONSTRAINT chk_causa_cie10_valida CHECK ((((causa_basica_cie10)::text !~~ 'P%'::text) AND ((causa_basica_cie10)::text <> ALL ((ARRAY['8888'::character varying, '9999'::character varying])::text[]))))
);


--
-- Name: causas_morbilidad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.causas_morbilidad (
    id_causa integer NOT NULL,
    id_caso integer NOT NULL,
    causa_principal_cie10 character varying(10) NOT NULL,
    id_grupo_causa smallint,
    causa_asociada_2 character varying(10),
    causa_asociada_3 character varying(10),
    causa_asociada_4 character varying(10)
);


--
-- Name: causas_morbilidad_id_causa_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.causas_morbilidad ALTER COLUMN id_causa ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.causas_morbilidad_id_causa_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: complicacion_embarazo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.complicacion_embarazo (
    id_caso integer NOT NULL,
    preeclampsia boolean DEFAULT false NOT NULL,
    eclampsia boolean DEFAULT false NOT NULL,
    sindrome_hellp boolean DEFAULT false NOT NULL,
    diabetes_gestacional boolean DEFAULT false NOT NULL,
    sepsis boolean DEFAULT false NOT NULL,
    hemorragia_1er_trimestre boolean DEFAULT false NOT NULL,
    hemorragia_2do_trimestre boolean DEFAULT false NOT NULL,
    hemorragia_3er_trimestre boolean DEFAULT false NOT NULL,
    desproporcion_cefalo_pelv boolean DEFAULT false NOT NULL,
    retardo_crecimiento_iu boolean DEFAULT false NOT NULL,
    enfermedad_autoinmune boolean DEFAULT false NOT NULL,
    malaria boolean DEFAULT false NOT NULL,
    embarazo_no_deseado boolean DEFAULT false NOT NULL,
    violencia_gestante boolean DEFAULT false NOT NULL,
    otras_complicaciones boolean DEFAULT false NOT NULL,
    desc_otras_complicaciones character varying(300),
    gestacion_violencia_sexual boolean DEFAULT false NOT NULL,
    feto_incompatible_vida boolean DEFAULT false NOT NULL,
    sintomas_depresivos boolean DEFAULT false NOT NULL
);


--
-- Name: control_prenatal; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.control_prenatal (
    id_caso integer NOT NULL,
    num_cpn smallint,
    semana_inicio_cpn smallint,
    id_personal_cpn smallint,
    id_nivel_atencion_cpn smallint,
    id_remisiones smallint NOT NULL,
    compl_feto_rn_cie10 character varying(10),
    CONSTRAINT chk_cp_num CHECK (((num_cpn >= 0) AND (num_cpn <= 45))),
    CONSTRAINT chk_cp_sem CHECK (((semana_inicio_cpn >= 1) AND (semana_inicio_cpn <= 45)))
);


--
-- Name: criterios_enfermedad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.criterios_enfermedad (
    id_criterio_enf integer NOT NULL,
    id_caso integer NOT NULL,
    eclampsia boolean DEFAULT false NOT NULL,
    sepsis_sistemica_severa boolean DEFAULT false NOT NULL,
    hemorragia_obstetrica boolean DEFAULT false NOT NULL,
    preeclampsia boolean DEFAULT false NOT NULL,
    ruptura_uterina boolean DEFAULT false NOT NULL,
    aborto_septico boolean DEFAULT false NOT NULL,
    embarazo_ectopico boolean DEFAULT false NOT NULL,
    autoinmune boolean DEFAULT false NOT NULL,
    hematologica boolean DEFAULT false NOT NULL,
    oncologica boolean DEFAULT false NOT NULL,
    endocrino_metabolicas boolean DEFAULT false NOT NULL,
    renales boolean DEFAULT false NOT NULL,
    gastrointestinales boolean DEFAULT false NOT NULL,
    tromboembolicos boolean DEFAULT false NOT NULL,
    cardiocerebrovasculares boolean DEFAULT false NOT NULL,
    otras_enfermedades boolean DEFAULT false NOT NULL
);


--
-- Name: criterios_enfermedad_id_criterio_enf_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.criterios_enfermedad ALTER COLUMN id_criterio_enf ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.criterios_enfermedad_id_criterio_enf_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: criterios_falla_organica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.criterios_falla_organica (
    id_criterio_falla integer NOT NULL,
    id_caso integer NOT NULL,
    falla_cardiaca boolean DEFAULT false NOT NULL,
    falla_vascular boolean DEFAULT false NOT NULL,
    falla_renal boolean DEFAULT false NOT NULL,
    falla_hepatica boolean DEFAULT false NOT NULL,
    falla_metabolica boolean DEFAULT false NOT NULL,
    falla_cerebral boolean DEFAULT false NOT NULL,
    falla_respiratoria boolean DEFAULT false NOT NULL,
    falla_coagulacion boolean DEFAULT false NOT NULL
);


--
-- Name: criterios_falla_organica_id_criterio_falla_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.criterios_falla_organica ALTER COLUMN id_criterio_falla ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.criterios_falla_organica_id_criterio_falla_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: criterios_manejo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.criterios_manejo (
    id_criterio_manejo integer NOT NULL,
    id_caso integer NOT NULL,
    ingreso_uci boolean DEFAULT false NOT NULL,
    cirugia_adicional boolean DEFAULT false NOT NULL,
    transfusion boolean DEFAULT false NOT NULL,
    total_criterios smallint,
    accidente boolean DEFAULT false NOT NULL,
    intoxicacion_accidental boolean DEFAULT false NOT NULL,
    intento_suicida boolean DEFAULT false NOT NULL,
    victima_violencia boolean DEFAULT false NOT NULL,
    otros_eventos_sp boolean DEFAULT false NOT NULL,
    cual_evento_sp character varying(200),
    CONSTRAINT chk_total_crit CHECK (((total_criterios >= 1) AND (total_criterios <= 14)))
);


--
-- Name: criterios_manejo_id_criterio_manejo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.criterios_manejo ALTER COLUMN id_criterio_manejo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.criterios_manejo_id_criterio_manejo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: datos_sociodemograficos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.datos_sociodemograficos (
    id integer NOT NULL,
    caso_morbilidad_id integer,
    caso_mortalidad_id integer,
    id_zona_residencia smallint,
    id_poblacion_vulnerable smallint,
    id_etnia smallint,
    id_tipo_afiliacion smallint,
    CONSTRAINT chk_ds_un_caso CHECK ((((caso_morbilidad_id IS NOT NULL) AND (caso_mortalidad_id IS NULL)) OR ((caso_morbilidad_id IS NULL) AND (caso_mortalidad_id IS NOT NULL))))
);


--
-- Name: datos_sociodemograficos_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.datos_sociodemograficos ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.datos_sociodemograficos_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: manejo_hospitalario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.manejo_hospitalario (
    id_manejo integer NOT NULL,
    id_caso integer NOT NULL,
    dias_estancia_hosp smallint,
    dias_estancia_uci smallint,
    unidades_transfundidas smallint,
    cirugia_1 smallint,
    cirugia_1_cual character varying(200),
    cirugia_2 smallint,
    cirugia_2_cual character varying(200),
    CONSTRAINT chk_mh_cir1 CHECK (((cirugia_1 >= 1) AND (cirugia_1 <= 4))),
    CONSTRAINT chk_mh_cir2 CHECK (((cirugia_2 >= 1) AND (cirugia_2 <= 4))),
    CONSTRAINT chk_mh_estancia CHECK ((dias_estancia_hosp >= 1)),
    CONSTRAINT chk_mh_trans CHECK ((unidades_transfundidas >= 3)),
    CONSTRAINT chk_mh_uci CHECK ((dias_estancia_uci >= 1))
);


--
-- Name: manejo_hospitalario_id_manejo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.manejo_hospitalario ALTER COLUMN id_manejo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.manejo_hospitalario_id_manejo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: narrativa_ia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.narrativa_ia (
    id integer NOT NULL,
    analisis_id integer NOT NULL,
    tipo_narrativa character varying(30) NOT NULL,
    filtros_hash character varying(64) NOT NULL,
    contenido text NOT NULL,
    modelo character varying(50) NOT NULL,
    generado_en timestamp without time zone NOT NULL
);


--
-- Name: narrativa_ia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.narrativa_ia_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: narrativa_ia_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.narrativa_ia_id_seq OWNED BY public.narrativa_ia.id;


--
-- Name: paciente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paciente (
    id_paciente integer NOT NULL,
    nombres_apellidos character varying(200) NOT NULL,
    id_tipo_id smallint NOT NULL,
    numero_id character varying(30) NOT NULL,
    fecha_nacimiento date,
    creado_en timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: paciente_id_paciente_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.paciente ALTER COLUMN id_paciente ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.paciente_id_paciente_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: referencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.referencia (
    id_referencia integer NOT NULL,
    id_caso integer NOT NULL,
    remitida boolean NOT NULL,
    institucion_ref_1 character varying(200),
    institucion_ref_2 character varying(200),
    tiempo_remision_h numeric(6,1)
);


--
-- Name: referencia_id_referencia_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.referencia ALTER COLUMN id_referencia ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.referencia_id_referencia_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: v_morbilidad_completa; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_morbilidad_completa AS
 SELECT c.id_caso,
    c.secretaria_codigo,
    p.nombres_apellidos,
    ti.codigo AS tipo_id,
    p.numero_id,
    p.fecha_nacimiento,
    (EXTRACT(year FROM age((c.fecha_egreso)::timestamp with time zone, (p.fecha_nacimiento)::timestamp with time zone)))::integer AS edad,
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
    gc.descripcion AS grupo_causa,
    zr.descripcion AS zona_residencia,
    pv.descripcion AS poblacion_vulnerable,
    et.descripcion AS etnia,
    ta.descripcion AS tipo_afiliacion
   FROM ((((((((((((((((public.caso_morbilidad c
     LEFT JOIN public.paciente p ON ((p.id_paciente = c.id_paciente)))
     LEFT JOIN public.cat_tipo_id ti ON ((ti.id = p.id_tipo_id)))
     LEFT JOIN public.referencia r ON ((r.id_caso = c.id_caso)))
     LEFT JOIN public.antecedentes_obstetricos a ON ((a.id_caso = c.id_caso)))
     LEFT JOIN public.cat_terminacion_gestacion tg ON ((tg.id = a.id_terminacion_gestacion)))
     LEFT JOIN public.criterios_enfermedad ce ON ((ce.id_caso = c.id_caso)))
     LEFT JOIN public.criterios_falla_organica cf ON ((cf.id_caso = c.id_caso)))
     LEFT JOIN public.criterios_manejo cm ON ((cm.id_caso = c.id_caso)))
     LEFT JOIN public.manejo_hospitalario mh ON ((mh.id_caso = c.id_caso)))
     LEFT JOIN public.causas_morbilidad ca ON ((ca.id_caso = c.id_caso)))
     LEFT JOIN public.cat_grupo_causa gc ON ((gc.id = ca.id_grupo_causa)))
     LEFT JOIN public.datos_sociodemograficos ds ON ((ds.caso_morbilidad_id = c.id_caso)))
     LEFT JOIN public.cat_zona_residencia zr ON ((zr.id = ds.id_zona_residencia)))
     LEFT JOIN public.cat_poblacion_vulnerable pv ON ((pv.id = ds.id_poblacion_vulnerable)))
     LEFT JOIN public.cat_etnia et ON ((et.id = ds.id_etnia)))
     LEFT JOIN public.cat_tipo_afiliacion ta ON ((ta.id = ds.id_tipo_afiliacion)));


--
-- Name: v_mortalidad_completa; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_mortalidad_completa AS
 SELECT c.id_caso,
    c.secretaria_codigo,
    p.nombres_apellidos,
    ti.codigo AS tipo_id,
    p.numero_id,
    p.fecha_nacimiento,
    (EXTRACT(year FROM age((c.fecha_defuncion)::timestamp with time zone, (p.fecha_nacimiento)::timestamp with time zone)))::integer AS edad,
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
    cm.demora_4,
    zr.descripcion AS zona_residencia,
    pv.descripcion AS poblacion_vulnerable,
    et.descripcion AS etnia,
    ta.descripcion AS tipo_afiliacion
   FROM (((((((((((((((((((((((((public.caso_mortalidad c
     LEFT JOIN public.paciente p ON ((p.id_paciente = c.id_paciente)))
     LEFT JOIN public.cat_tipo_id ti ON ((ti.id = p.id_tipo_id)))
     LEFT JOIN public.cat_sitio_defuncion sd ON ((sd.id = c.id_sitio_defuncion)))
     LEFT JOIN public.antecedente_materno am ON ((am.id_caso = c.id_caso)))
     LEFT JOIN public.cat_convivencia cv ON ((cv.id = am.id_convivencia)))
     LEFT JOIN public.cat_escolaridad es ON ((es.id = am.id_escolaridad)))
     LEFT JOIN public.cat_regulacion_fecundidad rf ON ((rf.id = am.id_regulacion_fec)))
     LEFT JOIN public.antecedente_riesgo ar ON ((ar.id_caso = c.id_caso)))
     LEFT JOIN public.complicacion_embarazo ce ON ((ce.id_caso = c.id_caso)))
     LEFT JOIN public.control_prenatal cp ON ((cp.id_caso = c.id_caso)))
     LEFT JOIN public.cat_personal_salud ps_cpn ON ((ps_cpn.id = cp.id_personal_cpn)))
     LEFT JOIN public.cat_nivel_atencion na_cpn ON ((na_cpn.id = cp.id_nivel_atencion_cpn)))
     LEFT JOIN public.cat_remisiones re ON ((re.id = cp.id_remisiones)))
     LEFT JOIN public.antecedente_parto_puerperio pp ON ((pp.id_caso = c.id_caso)))
     LEFT JOIN public.cat_momento_muerte mm ON ((mm.id = pp.id_momento_muerte)))
     LEFT JOIN public.cat_tipo_parto tp ON ((tp.id = pp.id_tipo_parto)))
     LEFT JOIN public.cat_personal_salud ps_parto ON ((ps_parto.id = pp.id_atendido_por)))
     LEFT JOIN public.cat_nivel_atencion na_parto ON ((na_parto.id = pp.id_nivel_atencion_parto)))
     LEFT JOIN public.causa_muerte cm ON ((cm.id_caso = c.id_caso)))
     LEFT JOIN public.cat_fuente_causa_muerte fc ON ((fc.id = cm.id_fuente_causa)))
     LEFT JOIN public.datos_sociodemograficos ds ON ((ds.caso_mortalidad_id = c.id_caso)))
     LEFT JOIN public.cat_zona_residencia zr ON ((zr.id = ds.id_zona_residencia)))
     LEFT JOIN public.cat_poblacion_vulnerable pv ON ((pv.id = ds.id_poblacion_vulnerable)))
     LEFT JOIN public.cat_etnia et ON ((et.id = ds.id_etnia)))
     LEFT JOIN public.cat_tipo_afiliacion ta ON ((ta.id = ds.id_tipo_afiliacion)));


--
-- Name: api_analisis id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_analisis ALTER COLUMN id SET DEFAULT nextval('public.api_analisis_id_seq'::regclass);


--
-- Name: api_sivigilaimportacion id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_sivigilaimportacion ALTER COLUMN id SET DEFAULT nextval('public.api_sivigilaimportacion_id_seq'::regclass);


--
-- Name: api_usuario id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_usuario ALTER COLUMN id SET DEFAULT nextval('public.api_usuario_id_seq'::regclass);


--
-- Name: narrativa_ia id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.narrativa_ia ALTER COLUMN id SET DEFAULT nextval('public.narrativa_ia_id_seq'::regclass);


--
-- Name: antecedente_materno antecedente_materno_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_materno
    ADD CONSTRAINT antecedente_materno_pkey PRIMARY KEY (id_caso);


--
-- Name: antecedente_parto_puerperio antecedente_parto_puerperio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT antecedente_parto_puerperio_pkey PRIMARY KEY (id_caso);


--
-- Name: antecedente_riesgo antecedente_riesgo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_riesgo
    ADD CONSTRAINT antecedente_riesgo_pkey PRIMARY KEY (id_caso);


--
-- Name: antecedentes_obstetricos antecedentes_obstetricos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT antecedentes_obstetricos_pkey PRIMARY KEY (id_antecedente);


--
-- Name: api_analisis api_analisis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_analisis
    ADD CONSTRAINT api_analisis_pkey PRIMARY KEY (id);


--
-- Name: api_sivigilaimportacion api_sivigilaimportacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_sivigilaimportacion
    ADD CONSTRAINT api_sivigilaimportacion_pkey PRIMARY KEY (id);


--
-- Name: api_usuario api_usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_usuario
    ADD CONSTRAINT api_usuario_pkey PRIMARY KEY (id);


--
-- Name: caso_morbilidad caso_morbilidad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_morbilidad
    ADD CONSTRAINT caso_morbilidad_pkey PRIMARY KEY (id_caso);


--
-- Name: caso_mortalidad caso_mortalidad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_mortalidad
    ADD CONSTRAINT caso_mortalidad_pkey PRIMARY KEY (id_caso);


--
-- Name: cat_convivencia cat_convivencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_convivencia
    ADD CONSTRAINT cat_convivencia_pkey PRIMARY KEY (id);


--
-- Name: cat_escolaridad cat_escolaridad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_escolaridad
    ADD CONSTRAINT cat_escolaridad_pkey PRIMARY KEY (id);


--
-- Name: cat_etnia cat_etnia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_etnia
    ADD CONSTRAINT cat_etnia_pkey PRIMARY KEY (id);


--
-- Name: cat_fuente_causa_muerte cat_fuente_causa_muerte_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_fuente_causa_muerte
    ADD CONSTRAINT cat_fuente_causa_muerte_pkey PRIMARY KEY (id);


--
-- Name: cat_grupo_causa cat_grupo_causa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_grupo_causa
    ADD CONSTRAINT cat_grupo_causa_pkey PRIMARY KEY (id);


--
-- Name: cat_momento_muerte cat_momento_muerte_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_momento_muerte
    ADD CONSTRAINT cat_momento_muerte_pkey PRIMARY KEY (id);


--
-- Name: cat_nivel_atencion cat_nivel_atencion_nivel_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_nivel_atencion
    ADD CONSTRAINT cat_nivel_atencion_nivel_key UNIQUE (nivel);


--
-- Name: cat_nivel_atencion cat_nivel_atencion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_nivel_atencion
    ADD CONSTRAINT cat_nivel_atencion_pkey PRIMARY KEY (id);


--
-- Name: cat_personal_salud cat_personal_salud_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_personal_salud
    ADD CONSTRAINT cat_personal_salud_pkey PRIMARY KEY (id);


--
-- Name: cat_poblacion_vulnerable cat_poblacion_vulnerable_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_poblacion_vulnerable
    ADD CONSTRAINT cat_poblacion_vulnerable_pkey PRIMARY KEY (id);


--
-- Name: cat_regulacion_fecundidad cat_regulacion_fecundidad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_regulacion_fecundidad
    ADD CONSTRAINT cat_regulacion_fecundidad_pkey PRIMARY KEY (id);


--
-- Name: cat_remisiones cat_remisiones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_remisiones
    ADD CONSTRAINT cat_remisiones_pkey PRIMARY KEY (id);


--
-- Name: cat_sitio_defuncion cat_sitio_defuncion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_sitio_defuncion
    ADD CONSTRAINT cat_sitio_defuncion_pkey PRIMARY KEY (id);


--
-- Name: cat_terminacion_gestacion cat_terminacion_gestacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_terminacion_gestacion
    ADD CONSTRAINT cat_terminacion_gestacion_pkey PRIMARY KEY (id);


--
-- Name: cat_tipo_afiliacion cat_tipo_afiliacion_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_tipo_afiliacion
    ADD CONSTRAINT cat_tipo_afiliacion_pkey PRIMARY KEY (id);


--
-- Name: cat_tipo_id cat_tipo_id_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_tipo_id
    ADD CONSTRAINT cat_tipo_id_codigo_key UNIQUE (codigo);


--
-- Name: cat_tipo_id cat_tipo_id_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_tipo_id
    ADD CONSTRAINT cat_tipo_id_pkey PRIMARY KEY (id);


--
-- Name: cat_tipo_parto cat_tipo_parto_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_tipo_parto
    ADD CONSTRAINT cat_tipo_parto_pkey PRIMARY KEY (id);


--
-- Name: cat_zona_residencia cat_zona_residencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cat_zona_residencia
    ADD CONSTRAINT cat_zona_residencia_pkey PRIMARY KEY (id);


--
-- Name: causa_muerte causa_muerte_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causa_muerte
    ADD CONSTRAINT causa_muerte_pkey PRIMARY KEY (id_caso);


--
-- Name: causas_morbilidad causas_morbilidad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causas_morbilidad
    ADD CONSTRAINT causas_morbilidad_pkey PRIMARY KEY (id_causa);


--
-- Name: complicacion_embarazo complicacion_embarazo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complicacion_embarazo
    ADD CONSTRAINT complicacion_embarazo_pkey PRIMARY KEY (id_caso);


--
-- Name: control_prenatal control_prenatal_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_prenatal
    ADD CONSTRAINT control_prenatal_pkey PRIMARY KEY (id_caso);


--
-- Name: criterios_enfermedad criterios_enfermedad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_enfermedad
    ADD CONSTRAINT criterios_enfermedad_pkey PRIMARY KEY (id_criterio_enf);


--
-- Name: criterios_falla_organica criterios_falla_organica_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_falla_organica
    ADD CONSTRAINT criterios_falla_organica_pkey PRIMARY KEY (id_criterio_falla);


--
-- Name: criterios_manejo criterios_manejo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_manejo
    ADD CONSTRAINT criterios_manejo_pkey PRIMARY KEY (id_criterio_manejo);


--
-- Name: datos_sociodemograficos datos_sociodemograficos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT datos_sociodemograficos_pkey PRIMARY KEY (id);


--
-- Name: manejo_hospitalario manejo_hospitalario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manejo_hospitalario
    ADD CONSTRAINT manejo_hospitalario_pkey PRIMARY KEY (id_manejo);


--
-- Name: narrativa_ia narrativa_ia_analisis_id_tipo_narrativa_filtros_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.narrativa_ia
    ADD CONSTRAINT narrativa_ia_analisis_id_tipo_narrativa_filtros_hash_key UNIQUE (analisis_id, tipo_narrativa, filtros_hash);


--
-- Name: narrativa_ia narrativa_ia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.narrativa_ia
    ADD CONSTRAINT narrativa_ia_pkey PRIMARY KEY (id);


--
-- Name: paciente paciente_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paciente
    ADD CONSTRAINT paciente_pkey PRIMARY KEY (id_paciente);


--
-- Name: referencia referencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referencia
    ADD CONSTRAINT referencia_pkey PRIMARY KEY (id_referencia);


--
-- Name: paciente uq_paciente_numero_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paciente
    ADD CONSTRAINT uq_paciente_numero_id UNIQUE (numero_id);


--
-- Name: idx_causa_cie10_morb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_causa_cie10_morb ON public.causas_morbilidad USING btree (causa_principal_cie10);


--
-- Name: idx_causa_cie10_mort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_causa_cie10_mort ON public.causa_muerte USING btree (causa_basica_cie10);


--
-- Name: idx_causa_grupo_morb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_causa_grupo_morb ON public.causas_morbilidad USING btree (id_grupo_causa);


--
-- Name: idx_ds_caso_morb; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ds_caso_morb ON public.datos_sociodemograficos USING btree (caso_morbilidad_id);


--
-- Name: idx_ds_caso_mort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ds_caso_mort ON public.datos_sociodemograficos USING btree (caso_mortalidad_id);


--
-- Name: idx_manejo_uci; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_manejo_uci ON public.criterios_manejo USING btree (ingreso_uci);


--
-- Name: idx_momento_muerte; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_momento_muerte ON public.antecedente_parto_puerperio USING btree (id_momento_muerte);


--
-- Name: idx_morb_fecha_egreso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_morb_fecha_egreso ON public.caso_morbilidad USING btree (fecha_egreso);


--
-- Name: idx_morb_paciente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_morb_paciente ON public.caso_morbilidad USING btree (id_paciente);


--
-- Name: idx_mort_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mort_fecha ON public.caso_mortalidad USING btree (fecha_defuncion);


--
-- Name: idx_mort_paciente; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mort_paciente ON public.caso_mortalidad USING btree (id_paciente);


--
-- Name: idx_paciente_nombre; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_paciente_nombre ON public.paciente USING btree (nombres_apellidos);


--
-- Name: idx_paciente_numero; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_paciente_numero ON public.paciente USING btree (numero_id);


--
-- Name: ix_api_analisis_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_analisis_id ON public.api_analisis USING btree (id);


--
-- Name: ix_api_analisis_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_analisis_secretaria_codigo ON public.api_analisis USING btree (secretaria_codigo);


--
-- Name: ix_api_sivigilaimportacion_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_sivigilaimportacion_id ON public.api_sivigilaimportacion USING btree (id);


--
-- Name: ix_api_sivigilaimportacion_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_sivigilaimportacion_secretaria_codigo ON public.api_sivigilaimportacion USING btree (secretaria_codigo);


--
-- Name: ix_api_usuario_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_api_usuario_email ON public.api_usuario USING btree (email);


--
-- Name: ix_api_usuario_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_usuario_id ON public.api_usuario USING btree (id);


--
-- Name: ix_api_usuario_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_usuario_secretaria_codigo ON public.api_usuario USING btree (secretaria_codigo);


--
-- Name: ix_caso_morbilidad_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_caso_morbilidad_secretaria_codigo ON public.caso_morbilidad USING btree (secretaria_codigo);


--
-- Name: ix_caso_mortalidad_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_caso_mortalidad_secretaria_codigo ON public.caso_mortalidad USING btree (secretaria_codigo);


--
-- Name: ix_narrativa_ia_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_narrativa_ia_id ON public.narrativa_ia USING btree (id);


--
-- Name: ix_sivigilaimportacion_secretaria_codigo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sivigilaimportacion_secretaria_codigo ON public.api_sivigilaimportacion USING btree (secretaria_codigo);


--
-- Name: antecedente_materno fk_am_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_materno
    ADD CONSTRAINT fk_am_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: antecedente_materno fk_am_conv; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_materno
    ADD CONSTRAINT fk_am_conv FOREIGN KEY (id_convivencia) REFERENCES public.cat_convivencia(id);


--
-- Name: antecedente_materno fk_am_esc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_materno
    ADD CONSTRAINT fk_am_esc FOREIGN KEY (id_escolaridad) REFERENCES public.cat_escolaridad(id);


--
-- Name: antecedente_materno fk_am_reg; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_materno
    ADD CONSTRAINT fk_am_reg FOREIGN KEY (id_regulacion_fec) REFERENCES public.cat_regulacion_fecundidad(id);


--
-- Name: antecedentes_obstetricos fk_ant_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT fk_ant_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: antecedentes_obstetricos fk_ant_regul; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT fk_ant_regul FOREIGN KEY (id_regulacion_fecundidad) REFERENCES public.cat_regulacion_fecundidad(id);


--
-- Name: antecedentes_obstetricos fk_ant_termin; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedentes_obstetricos
    ADD CONSTRAINT fk_ant_termin FOREIGN KEY (id_terminacion_gestacion) REFERENCES public.cat_terminacion_gestacion(id);


--
-- Name: antecedente_riesgo fk_ar_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_riesgo
    ADD CONSTRAINT fk_ar_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: complicacion_embarazo fk_ce_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.complicacion_embarazo
    ADD CONSTRAINT fk_ce_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: criterios_enfermedad fk_cenf_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_enfermedad
    ADD CONSTRAINT fk_cenf_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: criterios_falla_organica fk_cfo_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_falla_organica
    ADD CONSTRAINT fk_cfo_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: causas_morbilidad fk_cm_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causas_morbilidad
    ADD CONSTRAINT fk_cm_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: causas_morbilidad fk_cm_grupo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causas_morbilidad
    ADD CONSTRAINT fk_cm_grupo FOREIGN KEY (id_grupo_causa) REFERENCES public.cat_grupo_causa(id);


--
-- Name: criterios_manejo fk_cman_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.criterios_manejo
    ADD CONSTRAINT fk_cman_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: causa_muerte fk_cmu_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causa_muerte
    ADD CONSTRAINT fk_cmu_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: causa_muerte fk_cmu_fuente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.causa_muerte
    ADD CONSTRAINT fk_cmu_fuente FOREIGN KEY (id_fuente_causa) REFERENCES public.cat_fuente_causa_muerte(id);


--
-- Name: control_prenatal fk_cp_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_prenatal
    ADD CONSTRAINT fk_cp_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: control_prenatal fk_cp_nivel; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_prenatal
    ADD CONSTRAINT fk_cp_nivel FOREIGN KEY (id_nivel_atencion_cpn) REFERENCES public.cat_nivel_atencion(id);


--
-- Name: control_prenatal fk_cp_personal; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_prenatal
    ADD CONSTRAINT fk_cp_personal FOREIGN KEY (id_personal_cpn) REFERENCES public.cat_personal_salud(id);


--
-- Name: control_prenatal fk_cp_remis; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_prenatal
    ADD CONSTRAINT fk_cp_remis FOREIGN KEY (id_remisiones) REFERENCES public.cat_remisiones(id);


--
-- Name: datos_sociodemograficos fk_ds_afiliacion; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_afiliacion FOREIGN KEY (id_tipo_afiliacion) REFERENCES public.cat_tipo_afiliacion(id);


--
-- Name: datos_sociodemograficos fk_ds_etnia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_etnia FOREIGN KEY (id_etnia) REFERENCES public.cat_etnia(id);


--
-- Name: datos_sociodemograficos fk_ds_morb; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_morb FOREIGN KEY (caso_morbilidad_id) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: datos_sociodemograficos fk_ds_mort; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_mort FOREIGN KEY (caso_mortalidad_id) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: datos_sociodemograficos fk_ds_pobvuln; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_pobvuln FOREIGN KEY (id_poblacion_vulnerable) REFERENCES public.cat_poblacion_vulnerable(id);


--
-- Name: datos_sociodemograficos fk_ds_zona; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.datos_sociodemograficos
    ADD CONSTRAINT fk_ds_zona FOREIGN KEY (id_zona_residencia) REFERENCES public.cat_zona_residencia(id);


--
-- Name: manejo_hospitalario fk_mh_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.manejo_hospitalario
    ADD CONSTRAINT fk_mh_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: caso_morbilidad fk_morb_paciente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_morbilidad
    ADD CONSTRAINT fk_morb_paciente FOREIGN KEY (id_paciente) REFERENCES public.paciente(id_paciente);


--
-- Name: caso_mortalidad fk_mort_paciente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_mortalidad
    ADD CONSTRAINT fk_mort_paciente FOREIGN KEY (id_paciente) REFERENCES public.paciente(id_paciente);


--
-- Name: caso_mortalidad fk_mort_sitio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_mortalidad
    ADD CONSTRAINT fk_mort_sitio FOREIGN KEY (id_sitio_defuncion) REFERENCES public.cat_sitio_defuncion(id);


--
-- Name: paciente fk_paciente_tipo_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paciente
    ADD CONSTRAINT fk_paciente_tipo_id FOREIGN KEY (id_tipo_id) REFERENCES public.cat_tipo_id(id);


--
-- Name: antecedente_parto_puerperio fk_pp_atend; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT fk_pp_atend FOREIGN KEY (id_atendido_por) REFERENCES public.cat_personal_salud(id);


--
-- Name: antecedente_parto_puerperio fk_pp_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT fk_pp_caso FOREIGN KEY (id_caso) REFERENCES public.caso_mortalidad(id_caso);


--
-- Name: antecedente_parto_puerperio fk_pp_momento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT fk_pp_momento FOREIGN KEY (id_momento_muerte) REFERENCES public.cat_momento_muerte(id);


--
-- Name: antecedente_parto_puerperio fk_pp_nivel; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT fk_pp_nivel FOREIGN KEY (id_nivel_atencion_parto) REFERENCES public.cat_nivel_atencion(id);


--
-- Name: antecedente_parto_puerperio fk_pp_tipo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.antecedente_parto_puerperio
    ADD CONSTRAINT fk_pp_tipo FOREIGN KEY (id_tipo_parto) REFERENCES public.cat_tipo_parto(id);


--
-- Name: referencia fk_ref_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.referencia
    ADD CONSTRAINT fk_ref_caso FOREIGN KEY (id_caso) REFERENCES public.caso_morbilidad(id_caso);


--
-- Name: narrativa_ia narrativa_ia_analisis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.narrativa_ia
    ADD CONSTRAINT narrativa_ia_analisis_id_fkey FOREIGN KEY (analisis_id) REFERENCES public.api_analisis(id);


--
-- PostgreSQL database dump complete
--


--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: cat_convivencia; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_convivencia VALUES (1, 'Cónyuge');
INSERT INTO public.cat_convivencia VALUES (2, 'Familia');
INSERT INTO public.cat_convivencia VALUES (3, 'Sola');
INSERT INTO public.cat_convivencia VALUES (4, 'Otro');


--
-- Data for Name: cat_escolaridad; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_escolaridad VALUES (1, 'Ninguna');
INSERT INTO public.cat_escolaridad VALUES (2, 'Primaria');
INSERT INTO public.cat_escolaridad VALUES (3, 'Secundaria');
INSERT INTO public.cat_escolaridad VALUES (4, 'Superior');
INSERT INTO public.cat_escolaridad VALUES (5, 'Sin información');


--
-- Data for Name: cat_etnia; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_etnia VALUES (1, 'Ninguna');
INSERT INTO public.cat_etnia VALUES (2, 'Indígena');
INSERT INTO public.cat_etnia VALUES (3, 'Afrocolombiana');
INSERT INTO public.cat_etnia VALUES (4, 'Rrom');
INSERT INTO public.cat_etnia VALUES (5, 'Raizal');
INSERT INTO public.cat_etnia VALUES (6, 'Otra');


--
-- Data for Name: cat_fuente_causa_muerte; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_fuente_causa_muerte VALUES (1, 'Historia clínica');
INSERT INTO public.cat_fuente_causa_muerte VALUES (2, 'Autopsia verbal');
INSERT INTO public.cat_fuente_causa_muerte VALUES (3, 'Necropsia');


--
-- Data for Name: cat_grupo_causa; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_grupo_causa VALUES (1, 'Trastornos hipertensivos');
INSERT INTO public.cat_grupo_causa VALUES (2, 'Hemorragia obstétrica');
INSERT INTO public.cat_grupo_causa VALUES (3, 'Sepsis de origen obstétrico');
INSERT INTO public.cat_grupo_causa VALUES (4, 'Aborto');
INSERT INTO public.cat_grupo_causa VALUES (5, 'Complicaciones del parto y puerperio');
INSERT INTO public.cat_grupo_causa VALUES (6, 'Enfermedades concurrentes');
INSERT INTO public.cat_grupo_causa VALUES (7, 'Causas no obstétricas');
INSERT INTO public.cat_grupo_causa VALUES (8, 'Otras');


--
-- Data for Name: cat_momento_muerte; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_momento_muerte VALUES (1, 'Gestación');
INSERT INTO public.cat_momento_muerte VALUES (2, 'Parto');
INSERT INTO public.cat_momento_muerte VALUES (3, 'Puerperio < 24 horas');
INSERT INTO public.cat_momento_muerte VALUES (4, 'Puerperio > 24 horas');


--
-- Data for Name: cat_nivel_atencion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_nivel_atencion VALUES (1, 'I  ');
INSERT INTO public.cat_nivel_atencion VALUES (2, 'II ');
INSERT INTO public.cat_nivel_atencion VALUES (3, 'III');
INSERT INTO public.cat_nivel_atencion VALUES (4, 'IV ');


--
-- Data for Name: cat_personal_salud; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_personal_salud VALUES (1, 'Médico general');
INSERT INTO public.cat_personal_salud VALUES (2, 'Médico obstetra');
INSERT INTO public.cat_personal_salud VALUES (3, 'Enfermera');
INSERT INTO public.cat_personal_salud VALUES (4, 'Aux. enfermería');
INSERT INTO public.cat_personal_salud VALUES (5, 'Promotor');
INSERT INTO public.cat_personal_salud VALUES (6, 'Partera');
INSERT INTO public.cat_personal_salud VALUES (7, 'Otro');


--
-- Data for Name: cat_poblacion_vulnerable; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_poblacion_vulnerable VALUES (1, 'Ninguna');
INSERT INTO public.cat_poblacion_vulnerable VALUES (2, 'Migrante');
INSERT INTO public.cat_poblacion_vulnerable VALUES (3, 'Indígena');
INSERT INTO public.cat_poblacion_vulnerable VALUES (4, 'Afro');
INSERT INTO public.cat_poblacion_vulnerable VALUES (5, 'Discapacidad');
INSERT INTO public.cat_poblacion_vulnerable VALUES (6, 'Víctima de conflicto');
INSERT INTO public.cat_poblacion_vulnerable VALUES (7, 'Desplazada');


--
-- Data for Name: cat_regulacion_fecundidad; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_regulacion_fecundidad VALUES (1, 'No usó métodos por desconocimiento');
INSERT INTO public.cat_regulacion_fecundidad VALUES (2, 'No usó métodos por acceso');
INSERT INTO public.cat_regulacion_fecundidad VALUES (3, 'No usó métodos porque no deseaba');
INSERT INTO public.cat_regulacion_fecundidad VALUES (4, 'Natural');
INSERT INTO public.cat_regulacion_fecundidad VALUES (5, 'Dispositivo intrauterino');
INSERT INTO public.cat_regulacion_fecundidad VALUES (6, 'Hormonal');
INSERT INTO public.cat_regulacion_fecundidad VALUES (7, 'Barrera');
INSERT INTO public.cat_regulacion_fecundidad VALUES (8, 'Quirúrgico');
INSERT INTO public.cat_regulacion_fecundidad VALUES (9, 'Otro');


--
-- Data for Name: cat_remisiones; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_remisiones VALUES (1, 'Sí');
INSERT INTO public.cat_remisiones VALUES (2, 'No');
INSERT INTO public.cat_remisiones VALUES (3, 'No aplica');


--
-- Data for Name: cat_sitio_defuncion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_sitio_defuncion VALUES (1, 'IPS (hospital/clínica)');
INSERT INTO public.cat_sitio_defuncion VALUES (2, 'IPS (centro/puesto de salud)');
INSERT INTO public.cat_sitio_defuncion VALUES (3, 'Lugar de trabajo');
INSERT INTO public.cat_sitio_defuncion VALUES (4, 'Vía pública');
INSERT INTO public.cat_sitio_defuncion VALUES (5, 'Durante el traslado');
INSERT INTO public.cat_sitio_defuncion VALUES (6, 'Domicilio');
INSERT INTO public.cat_sitio_defuncion VALUES (7, 'Otro');


--
-- Data for Name: cat_terminacion_gestacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_terminacion_gestacion VALUES (1, 'Aborto');
INSERT INTO public.cat_terminacion_gestacion VALUES (2, 'Parto');
INSERT INTO public.cat_terminacion_gestacion VALUES (3, 'Parto instrumentado');
INSERT INTO public.cat_terminacion_gestacion VALUES (4, 'Cesárea');
INSERT INTO public.cat_terminacion_gestacion VALUES (5, 'Continúa embarazada');


--
-- Data for Name: cat_tipo_afiliacion; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_tipo_afiliacion VALUES (1, 'Contributivo');
INSERT INTO public.cat_tipo_afiliacion VALUES (2, 'Subsidiado');
INSERT INTO public.cat_tipo_afiliacion VALUES (3, 'No afiliada');


--
-- Data for Name: cat_tipo_id; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_tipo_id VALUES (1, 'CC', 'Cédula de Ciudadanía');
INSERT INTO public.cat_tipo_id VALUES (2, 'CE', 'Cédula de Extranjería');
INSERT INTO public.cat_tipo_id VALUES (3, 'PA', 'Pasaporte');
INSERT INTO public.cat_tipo_id VALUES (4, 'PPT', 'Permiso por Protección Temporal');
INSERT INTO public.cat_tipo_id VALUES (5, 'TI', 'Tarjeta de Identidad');
INSERT INTO public.cat_tipo_id VALUES (6, 'RC', 'Registro Civil');
INSERT INTO public.cat_tipo_id VALUES (7, 'MS', 'Menor sin ID');
INSERT INTO public.cat_tipo_id VALUES (8, 'AS', 'Adulto sin ID');


--
-- Data for Name: cat_tipo_parto; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_tipo_parto VALUES (1, 'Vaginal');
INSERT INTO public.cat_tipo_parto VALUES (2, 'Cesárea');
INSERT INTO public.cat_tipo_parto VALUES (3, 'Instrumentado');
INSERT INTO public.cat_tipo_parto VALUES (4, 'Ignorado');


--
-- Data for Name: cat_zona_residencia; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.cat_zona_residencia VALUES (1, 'Urbana');
INSERT INTO public.cat_zona_residencia VALUES (2, 'Rural');


--
-- PostgreSQL database dump complete
--


