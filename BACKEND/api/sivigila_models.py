from django.db import models


class CatConvivencia(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_convivencia'


class CatEscolaridad(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_escolaridad'


class CatFuenteCausaMuerte(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_fuente_causa_muerte'


class CatGrupoCausa(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=60)

    class Meta:
        managed = False
        db_table = 'cat_grupo_causa'


class CatMomentoMuerte(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_momento_muerte'


class CatNivelAtencion(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    nivel = models.CharField(max_length=3, unique=True)

    class Meta:
        managed = False
        db_table = 'cat_nivel_atencion'


class CatPersonalSalud(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_personal_salud'


class CatRegulacionFecundidad(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'cat_regulacion_fecundidad'


class CatRemisiones(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'cat_remisiones'


class CatSitioDefuncion(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=60)

    class Meta:
        managed = False
        db_table = 'cat_sitio_defuncion'


class CatTerminacionGestacion(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'cat_terminacion_gestacion'


class CatTipoId(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    codigo = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'cat_tipo_id'


class CatTipoParto(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    descripcion = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'cat_tipo_parto'


class Paciente(models.Model):
    id_paciente = models.AutoField(primary_key=True)
    nombres_apellidos = models.CharField(max_length=200)
    id_tipo = models.ForeignKey(CatTipoId, models.DO_NOTHING)
    numero_id = models.CharField(max_length=30)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    creado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paciente'
        unique_together = (('id_tipo', 'numero_id'),)


class CasoMorbilidad(models.Model):
    id_caso = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='id_paciente')
    fecha_egreso = models.DateField(blank=True, null=True)
    creado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'caso_morbilidad'


class Referencia(models.Model):
    id_referencia = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    remitida = models.IntegerField()
    institucion_ref_1 = models.CharField(max_length=200, blank=True, null=True)
    institucion_ref_2 = models.CharField(max_length=200, blank=True, null=True)
    tiempo_remision_h = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'referencia'


class AntecedentesObstetricos(models.Model):
    id_antecedente = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    num_gestaciones = models.SmallIntegerField(blank=True, null=True)
    partos_vaginales = models.SmallIntegerField(blank=True, null=True)
    cesareas = models.SmallIntegerField(blank=True, null=True)
    abortos = models.SmallIntegerField(blank=True, null=True)
    molas = models.SmallIntegerField(blank=True, null=True)
    ectopicos = models.SmallIntegerField(blank=True, null=True)
    muertos = models.SmallIntegerField(blank=True, null=True)
    vivos = models.SmallIntegerField(blank=True, null=True)
    fecha_ultima_gestacion = models.DateField(blank=True, null=True)
    id_regulacion_fecundidad = models.ForeignKey(CatRegulacionFecundidad, models.DO_NOTHING, db_column='id_regulacion_fecundidad', blank=True, null=True)
    num_controles_prenatales = models.SmallIntegerField(blank=True, null=True)
    semanas_inicio_cpn = models.SmallIntegerField(blank=True, null=True)
    id_terminacion_gestacion = models.ForeignKey(CatTerminacionGestacion, models.DO_NOTHING, db_column='id_terminacion_gestacion', blank=True, null=True)
    edad_gestacional_sem = models.SmallIntegerField(blank=True, null=True)
    momento_ocurrencia = models.CharField(max_length=7, blank=True, null=True)
    estado_recien_nacido = models.CharField(max_length=6, blank=True, null=True)
    multiplicidad = models.IntegerField(blank=True, null=True)
    peso_rn_gramos = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'antecedentes_obstetricos'


class CriteriosEnfermedad(models.Model):
    id_criterio_enf = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    eclampsia = models.IntegerField()
    sepsis_sistemica_severa = models.IntegerField()
    hemorragia_obstetrica = models.IntegerField()
    preeclampsia = models.IntegerField()
    ruptura_uterina = models.IntegerField()
    aborto_septico = models.IntegerField()
    embarazo_ectopico = models.IntegerField()
    autoinmune = models.IntegerField()
    hematologica = models.IntegerField()
    oncologica = models.IntegerField()
    endocrino_metabolicas = models.IntegerField()
    renales = models.IntegerField()
    gastrointestinales = models.IntegerField()
    tromboembolicos = models.IntegerField()
    cardiocerebrovasculares = models.IntegerField()
    otras_enfermedades = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'criterios_enfermedad'


class CriteriosFallaOrganica(models.Model):
    id_criterio_falla = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    falla_cardiaca = models.IntegerField()
    falla_vascular = models.IntegerField()
    falla_renal = models.IntegerField()
    falla_hepatica = models.IntegerField()
    falla_metabolica = models.IntegerField()
    falla_cerebral = models.IntegerField()
    falla_respiratoria = models.IntegerField()
    falla_coagulacion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'criterios_falla_organica'


class CriteriosManejo(models.Model):
    id_criterio_manejo = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    ingreso_uci = models.IntegerField()
    cirugia_adicional = models.IntegerField()
    transfusion = models.IntegerField()
    total_criterios = models.SmallIntegerField(blank=True, null=True)
    accidente = models.IntegerField()
    intoxicacion_accidental = models.IntegerField()
    intento_suicida = models.IntegerField()
    victima_violencia = models.IntegerField()
    otros_eventos_sp = models.IntegerField()
    cual_evento_sp = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'criterios_manejo'


class ManejoHospitalario(models.Model):
    id_manejo = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    dias_estancia_hosp = models.SmallIntegerField(blank=True, null=True)
    dias_estancia_uci = models.SmallIntegerField(blank=True, null=True)
    unidades_transfundidas = models.SmallIntegerField(blank=True, null=True)
    cirugia_1 = models.SmallIntegerField(blank=True, null=True)
    cirugia_1_cual = models.CharField(max_length=200, blank=True, null=True)
    cirugia_2 = models.SmallIntegerField(blank=True, null=True)
    cirugia_2_cual = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'manejo_hospitalario'


class CausasMorbilidad(models.Model):
    id_causa = models.AutoField(primary_key=True)
    id_caso = models.ForeignKey(CasoMorbilidad, models.DO_NOTHING, db_column='id_caso')
    causa_principal_cie10 = models.CharField(max_length=10)
    id_grupo_causa = models.ForeignKey(CatGrupoCausa, models.DO_NOTHING, db_column='id_grupo_causa', blank=True, null=True)
    causa_asociada_2 = models.CharField(max_length=10, blank=True, null=True)
    causa_asociada_3 = models.CharField(max_length=10, blank=True, null=True)
    causa_asociada_4 = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'causas_morbilidad'


class CasoMortalidad(models.Model):
    id_caso = models.AutoField(primary_key=True)
    id_paciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='id_paciente')
    id_sitio_defuncion = models.ForeignKey(CatSitioDefuncion, models.DO_NOTHING, db_column='id_sitio_defuncion')
    fecha_defuncion = models.DateField(blank=True, null=True)
    creado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'caso_mortalidad'


class AntecedenteMaterno(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    id_convivencia = models.ForeignKey(CatConvivencia, models.DO_NOTHING, db_column='id_convivencia')
    otro_convivencia = models.CharField(max_length=100, blank=True, null=True)
    id_escolaridad = models.ForeignKey(CatEscolaridad, models.DO_NOTHING, db_column='id_escolaridad')
    id_regulacion_fec = models.ForeignKey(CatRegulacionFecundidad, models.DO_NOTHING, db_column='id_regulacion_fec')
    gestaciones = models.SmallIntegerField(blank=True, null=True)
    partos_vaginales = models.SmallIntegerField(blank=True, null=True)
    cesareas = models.SmallIntegerField(blank=True, null=True)
    nacidos_muertos = models.SmallIntegerField(blank=True, null=True)
    hijos_vivos = models.SmallIntegerField(blank=True, null=True)
    abortos = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'antecedente_materno'


class AntecedenteRiesgo(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    sin_antecedentes = models.IntegerField()
    hipertension_cronica = models.IntegerField()
    cardiopatias = models.IntegerField()
    diabetes = models.IntegerField()
    mola_hidatiforme = models.IntegerField()
    rn_pretermino = models.IntegerField()
    rn_bajo_peso = models.IntegerField()
    rn_macrosomico = models.IntegerField()
    trastorno_mental = models.IntegerField()
    obesidad = models.IntegerField()
    desnutricion_cronica = models.IntegerField()
    intergenesis_menor_2a = models.IntegerField()
    its_distintas = models.IntegerField()
    vih_sida = models.IntegerField()
    otras_infecciones = models.IntegerField()
    rh_negativo = models.IntegerField()
    tabaquismo = models.IntegerField()
    alcoholismo = models.IntegerField()
    sustancias_psicoactivas = models.IntegerField()
    deficiencias_socioeconomicas = models.IntegerField()
    sifilis = models.IntegerField()
    hepatitis_b = models.IntegerField()
    otros_factores_riesgo = models.IntegerField()
    desc_otros_factores = models.CharField(max_length=300, blank=True, null=True)
    gingivitis_periodontitis = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'antecedente_riesgo'


class ComplicacionEmbarazo(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    preeclampsia = models.IntegerField()
    eclampsia = models.IntegerField()
    sindrome_hellp = models.IntegerField()
    diabetes_gestacional = models.IntegerField()
    sepsis = models.IntegerField()
    hemorragia_1er_trimestre = models.IntegerField()
    hemorragia_2do_trimestre = models.IntegerField()
    hemorragia_3er_trimestre = models.IntegerField()
    desproporcion_cefalo_pelv = models.IntegerField()
    retardo_crecimiento_iu = models.IntegerField()
    enfermedad_autoinmune = models.IntegerField()
    malaria = models.IntegerField()
    embarazo_no_deseado = models.IntegerField()
    violencia_gestante = models.IntegerField()
    otras_complicaciones = models.IntegerField()
    desc_otras_complicaciones = models.CharField(max_length=300, blank=True, null=True)
    gestacion_violencia_sexual = models.IntegerField()
    feto_incompatible_vida = models.IntegerField()
    sintomas_depresivos = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'complicacion_embarazo'


class ControlPrenatal(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    num_cpn = models.SmallIntegerField(blank=True, null=True)
    semana_inicio_cpn = models.SmallIntegerField(blank=True, null=True)
    id_personal_cpn = models.ForeignKey(CatPersonalSalud, models.DO_NOTHING, db_column='id_personal_cpn', blank=True, null=True)
    id_nivel_atencion_cpn = models.ForeignKey(CatNivelAtencion, models.DO_NOTHING, db_column='id_nivel_atencion_cpn', blank=True, null=True)
    id_remisiones = models.ForeignKey(CatRemisiones, models.DO_NOTHING, db_column='id_remisiones')
    compl_feto_rn_cie10 = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'control_prenatal'


class AntecedentePartoPuerperio(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    id_momento_muerte = models.ForeignKey(CatMomentoMuerte, models.DO_NOTHING, db_column='id_momento_muerte')
    semana_gestacion_muerte = models.SmallIntegerField(blank=True, null=True)
    fecha_parto = models.DateField(blank=True, null=True)
    hora_parto = models.TimeField(blank=True, null=True)
    id_tipo_parto = models.ForeignKey(CatTipoParto, models.DO_NOTHING, db_column='id_tipo_parto', blank=True, null=True)
    id_atendido_por = models.ForeignKey(CatPersonalSalud, models.DO_NOTHING, db_column='id_atendido_por', blank=True, null=True)
    otro_atencion_parto = models.CharField(max_length=100, blank=True, null=True)
    id_nivel_atencion_parto = models.ForeignKey(CatNivelAtencion, models.DO_NOTHING, db_column='id_nivel_atencion_parto', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'antecedente_parto_puerperio'


class CausaMuerte(models.Model):
    id_caso = models.OneToOneField(CasoMortalidad, models.DO_NOTHING, db_column='id_caso', primary_key=True)
    causa_basica_cie10 = models.CharField(max_length=10)
    id_fuente_causa = models.ForeignKey(CatFuenteCausaMuerte, models.DO_NOTHING, db_column='id_fuente_causa')
    demora_1 = models.IntegerField()
    demora_2 = models.IntegerField()
    demora_3 = models.IntegerField()
    demora_4 = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'causa_muerte'


class VMorbilidadCompleta(models.Model):
    id_caso = models.IntegerField(primary_key=True)
    nombres_apellidos = models.CharField(max_length=200, blank=True, null=True)
    tipo_id = models.CharField(max_length=5, blank=True, null=True)
    numero_id = models.CharField(max_length=30, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    edad = models.IntegerField(blank=True, null=True)
    fecha_egreso = models.DateField(blank=True, null=True)
    remitida = models.IntegerField(blank=True, null=True)
    institucion_ref_1 = models.CharField(max_length=200, blank=True, null=True)
    tiempo_remision_h = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    num_gestaciones = models.SmallIntegerField(blank=True, null=True)
    partos_vaginales = models.SmallIntegerField(blank=True, null=True)
    cesareas = models.SmallIntegerField(blank=True, null=True)
    abortos = models.SmallIntegerField(blank=True, null=True)
    num_controles_prenatales = models.SmallIntegerField(blank=True, null=True)
    edad_gestacional_sem = models.SmallIntegerField(blank=True, null=True)
    terminacion_gestacion = models.CharField(max_length=30, blank=True, null=True)
    estado_recien_nacido = models.CharField(max_length=6, blank=True, null=True)
    peso_rn_gramos = models.SmallIntegerField(blank=True, null=True)
    eclampsia = models.IntegerField(blank=True, null=True)
    preeclampsia = models.IntegerField(blank=True, null=True)
    hemorragia_obstetrica = models.IntegerField(blank=True, null=True)
    sepsis_sistemica_severa = models.IntegerField(blank=True, null=True)
    ruptura_uterina = models.IntegerField(blank=True, null=True)
    falla_cardiaca = models.IntegerField(blank=True, null=True)
    falla_renal = models.IntegerField(blank=True, null=True)
    falla_hepatica = models.IntegerField(blank=True, null=True)
    falla_respiratoria = models.IntegerField(blank=True, null=True)
    falla_coagulacion = models.IntegerField(blank=True, null=True)
    ingreso_uci = models.IntegerField(blank=True, null=True)
    cirugia_adicional = models.IntegerField(blank=True, null=True)
    transfusion = models.IntegerField(blank=True, null=True)
    total_criterios = models.SmallIntegerField(blank=True, null=True)
    dias_estancia_hosp = models.SmallIntegerField(blank=True, null=True)
    dias_estancia_uci = models.SmallIntegerField(blank=True, null=True)
    unidades_transfundidas = models.SmallIntegerField(blank=True, null=True)
    causa_principal_cie10 = models.CharField(max_length=10, blank=True, null=True)
    grupo_causa = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_morbilidad_completa'


class VMortalidadCompleta(models.Model):
    id_caso = models.IntegerField(primary_key=True)
    nombres_apellidos = models.CharField(max_length=200, blank=True, null=True)
    tipo_id = models.CharField(max_length=5, blank=True, null=True)
    numero_id = models.CharField(max_length=30, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    edad = models.IntegerField(blank=True, null=True)
    sitio_defuncion = models.CharField(max_length=60, blank=True, null=True)
    fecha_defuncion = models.DateField(blank=True, null=True)
    convivencia = models.CharField(max_length=30, blank=True, null=True)
    otro_convivencia = models.CharField(max_length=100, blank=True, null=True)
    escolaridad = models.CharField(max_length=30, blank=True, null=True)
    regulacion_fecundidad = models.CharField(max_length=50, blank=True, null=True)
    gestaciones = models.SmallIntegerField(blank=True, null=True)
    partos_vaginales = models.SmallIntegerField(blank=True, null=True)
    cesareas = models.SmallIntegerField(blank=True, null=True)
    nacidos_muertos = models.SmallIntegerField(blank=True, null=True)
    hijos_vivos = models.SmallIntegerField(blank=True, null=True)
    abortos = models.SmallIntegerField(blank=True, null=True)
    sin_antecedentes = models.IntegerField(blank=True, null=True)
    hipertension_cronica = models.IntegerField(blank=True, null=True)
    diabetes = models.IntegerField(blank=True, null=True)
    vih_sida = models.IntegerField(blank=True, null=True)
    tabaquismo = models.IntegerField(blank=True, null=True)
    deficiencias_socioeconomicas = models.IntegerField(blank=True, null=True)
    preeclampsia = models.IntegerField(blank=True, null=True)
    eclampsia = models.IntegerField(blank=True, null=True)
    sindrome_hellp = models.IntegerField(blank=True, null=True)
    sepsis = models.IntegerField(blank=True, null=True)
    hemorragia_3er_trimestre = models.IntegerField(blank=True, null=True)
    embarazo_no_deseado = models.IntegerField(blank=True, null=True)
    violencia_gestante = models.IntegerField(blank=True, null=True)
    num_cpn = models.SmallIntegerField(blank=True, null=True)
    semana_inicio_cpn = models.SmallIntegerField(blank=True, null=True)
    cpn_realizado_por = models.CharField(max_length=30, blank=True, null=True)
    nivel_atencion_cpn = models.CharField(max_length=3, blank=True, null=True)
    remisiones_oportunas = models.CharField(max_length=15, blank=True, null=True)
    compl_feto_rn_cie10 = models.CharField(max_length=10, blank=True, null=True)
    momento_muerte = models.CharField(max_length=30, blank=True, null=True)
    semana_gestacion_muerte = models.SmallIntegerField(blank=True, null=True)
    fecha_parto = models.DateField(blank=True, null=True)
    hora_parto = models.TimeField(blank=True, null=True)
    tipo_parto = models.CharField(max_length=20, blank=True, null=True)
    parto_atendido_por = models.CharField(max_length=30, blank=True, null=True)
    nivel_atencion_parto = models.CharField(max_length=3, blank=True, null=True)
    causa_basica_cie10 = models.CharField(max_length=10, blank=True, null=True)
    fuente_causa_muerte = models.CharField(max_length=30, blank=True, null=True)
    demora_1 = models.IntegerField(blank=True, null=True)
    demora_2 = models.IntegerField(blank=True, null=True)
    demora_3 = models.IntegerField(blank=True, null=True)
    demora_4 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_mortalidad_completa'


__all__ = [
    'AntecedenteMaterno',
    'AntecedentePartoPuerperio',
    'AntecedenteRiesgo',
    'AntecedentesObstetricos',
    'CasoMorbilidad',
    'CasoMortalidad',
    'CatConvivencia',
    'CatEscolaridad',
    'CatFuenteCausaMuerte',
    'CatGrupoCausa',
    'CatMomentoMuerte',
    'CatNivelAtencion',
    'CatPersonalSalud',
    'CatRegulacionFecundidad',
    'CatRemisiones',
    'CatSitioDefuncion',
    'CatTerminacionGestacion',
    'CatTipoId',
    'CatTipoParto',
    'CausaMuerte',
    'CausasMorbilidad',
    'ComplicacionEmbarazo',
    'ControlPrenatal',
    'CriteriosEnfermedad',
    'CriteriosFallaOrganica',
    'CriteriosManejo',
    'ManejoHospitalario',
    'Paciente',
    'Referencia',
    'VMorbilidadCompleta',
    'VMortalidadCompleta',
]