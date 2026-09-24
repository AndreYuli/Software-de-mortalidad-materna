"""Schemas Pydantic para los endpoints de consulta SIVIGILA."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict


class PacienteResponse(BaseModel):
    """Datos de un paciente con su tipo de identificación."""

    id_paciente: int
    nombres_apellidos: str
    tipo_identificacion: str | None
    descripcion_tipo_identificacion: str | None
    numero_id: str
    fecha_nacimiento: date | None
    creado_en: datetime | None


class VMorbilidadResponse(BaseModel):
    """Fila de la vista consolidada de morbilidad materna extrema."""

    model_config = ConfigDict(from_attributes=True)

    id_caso: int
    nombres_apellidos: str | None
    tipo_id: str | None
    numero_id: str | None
    fecha_nacimiento: date | None
    edad: int | None
    fecha_egreso: date | None
    remitida: int | None
    institucion_ref_1: str | None
    tiempo_remision_h: float | None
    num_gestaciones: int | None
    partos_vaginales: int | None
    cesareas: int | None
    abortos: int | None
    num_controles_prenatales: int | None
    edad_gestacional_sem: int | None
    terminacion_gestacion: str | None
    estado_recien_nacido: str | None
    peso_rn_gramos: int | None
    eclampsia: int | None
    preeclampsia: int | None
    hemorragia_obstetrica: int | None
    sepsis_sistemica_severa: int | None
    ruptura_uterina: int | None
    falla_cardiaca: int | None
    falla_renal: int | None
    falla_hepatica: int | None
    falla_respiratoria: int | None
    falla_coagulacion: int | None
    ingreso_uci: int | None
    cirugia_adicional: int | None
    transfusion: int | None
    total_criterios: int | None
    dias_estancia_hosp: int | None
    dias_estancia_uci: int | None
    unidades_transfundidas: int | None
    causa_principal_cie10: str | None
    grupo_causa: str | None


class VMortalidadResponse(BaseModel):
    """Fila de la vista consolidada de mortalidad materna."""

    model_config = ConfigDict(from_attributes=True)

    id_caso: int
    nombres_apellidos: str | None
    tipo_id: str | None
    numero_id: str | None
    fecha_nacimiento: date | None
    edad: int | None
    sitio_defuncion: str | None
    fecha_defuncion: date | None
    convivencia: str | None
    otro_convivencia: str | None
    escolaridad: str | None
    regulacion_fecundidad: str | None
    gestaciones: int | None
    partos_vaginales: int | None
    cesareas: int | None
    nacidos_muertos: int | None
    hijos_vivos: int | None
    abortos: int | None
    sin_antecedentes: int | None
    hipertension_cronica: int | None
    diabetes: int | None
    vih_sida: int | None
    tabaquismo: int | None
    deficiencias_socioeconomicas: int | None
    preeclampsia: int | None
    eclampsia: int | None
    sindrome_hellp: int | None
    sepsis: int | None
    hemorragia_3er_trimestre: int | None
    embarazo_no_deseado: int | None
    violencia_gestante: int | None
    num_cpn: int | None
    semana_inicio_cpn: int | None
    cpn_realizado_por: str | None
    nivel_atencion_cpn: str | None
    remisiones_oportunas: str | None
    compl_feto_rn_cie10: str | None
    momento_muerte: str | None
    semana_gestacion_muerte: int | None
    fecha_parto: date | None
    hora_parto: time | None
    tipo_parto: str | None
    parto_atendido_por: str | None
    nivel_atencion_parto: str | None
    causa_basica_cie10: str | None
    fuente_causa_muerte: str | None
    demora_1: int | None
    demora_2: int | None
    demora_3: int | None
    demora_4: int | None
