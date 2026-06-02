import unicodedata
from hashlib import sha256
import json
import re

import pandas as pd

from .models import (
    AntecedenteMaterno,
    AntecedentePartoPuerperio,
    AntecedenteRiesgo,
    AntecedentesObstetricos,
    CasoMorbilidad,
    CasoMortalidad,
    CatConvivencia,
    CatEscolaridad,
    CatFuenteCausaMuerte,
    CatGrupoCausa,
    CatMomentoMuerte,
    CatNivelAtencion,
    CatPersonalSalud,
    CatRegulacionFecundidad,
    CatRemisiones,
    CatSitioDefuncion,
    CatTerminacionGestacion,
    CatTipoId,
    CatTipoParto,
    CausaMuerte,
    CausasMorbilidad,
    ComplicacionEmbarazo,
    ControlPrenatal,
    CriteriosEnfermedad,
    CriteriosFallaOrganica,
    CriteriosManejo,
    ManejoHospitalario,
    Paciente,
    Referencia,
    SivigilaImportacion,
)


TIPO_ID_ALIASES = {
    'p': 'PA',
    'pasaporte': 'PA',
    'passport': 'PA',
    'cc': 'CC',
    'ce': 'CE',
    'ppt': 'PPT',
    'permiso proteccion temporal': 'PPT',
    'permiso por proteccion temporal': 'PPT',
    'ti': 'TI',
    'tarjeta identidad': 'TI',
    'rc': 'RC',
    'registro civil': 'RC',
}


MORTALIDAD_FECHA_DEFUNCION_COLS = [
    '5.2 Fecha de defunción', '5.2 Fecha de defuncion',
    '5.2 Fecha defunción', '5.2 Fecha defuncion',
    '5.2 Fecha de defunción (dd/mm/aaaa)', '5.2 Fecha de defuncion (dd/mm/aaaa)',
    'Fecha de defunción', 'Fecha de defuncion',
]
MORTALIDAD_FUENTE_CAUSA_COLS = ['10.2 Fuente de causa de muerte', '10.2 Fuente causa de muerte', 'Fuente causa muerte']
MORTALIDAD_REMISIONES_COLS = ['8.3 Remisiones', '8.4 Remisiones', 'Remisiones', 'Remisiones oportunas']
MORTALIDAD_MOMENTO_MUERTE_COLS = ['9.1 Momento de la muerte']
MORTALIDAD_FECHA_PARTO_COLS = ['9.3 Fecha parto (dd/mm/aaaa)', '9.3 Fecha parto', 'Fecha parto (dd/mm/aaaa)', 'Fecha parto']
MORTALIDAD_HORA_PARTO_COLS = ['9.3 Hora parto', 'Hora parto']
MORTALIDAD_ATENDIDO_POR_COLS = ['9.5 Atendido por', 'Atendido por']
MORTALIDAD_NIVEL_PARTO_COLS = ['9.6 Nivel atención parto', 'Nivel atención parto']
MORTALIDAD_PERSONAL_CPN_COLS = ['8.3 Personal CPN', 'Personal CPN']
MORTALIDAD_NIVEL_CPN_COLS = ['8.4 Nivel atención CPN', 'Nivel atención CPN']

MORBILIDAD_FECHA_EGRESO_COLS = [
    'Fecha de egreso', 'Fecha egreso',
    'Fecha de egreso (dd/mm/aaaa)', 'Fecha egreso (dd/mm/aaaa)',
    'Fecha de egreso (dd/mm/yyyy)', 'Fecha egreso (dd/mm/yyyy)',
]
MORBILIDAD_TERMINACION_COLS = ['Terminación de la gestación', 'Terminacion de la gestacion']
MORBILIDAD_ESTADO_RN_COLS = ['Estado recién nacido', 'Estado recien nacido']
MORBILIDAD_PESO_RN_COLS = ['Peso RN gramos', 'Peso RN', 'Peso recién nacido']
MORBILIDAD_TRANSFUNDIDAS_COLS = ['Unidades transfundidas']
MORBILIDAD_GRUPO_CAUSA_COLS = ['Grupo causa', 'Grupo de causa']
MORBILIDAD_INSTITUCION_REF_1_COLS = ['Institución referencia 1', 'Institucion referencia 1']
MORBILIDAD_INSTITUCION_REF_2_COLS = ['Institución referencia 2', 'Institucion referencia 2']
MORBILIDAD_TIEMPO_REMISION_COLS = ['Tiempo remisión (h)', 'Tiempo remision (h)', 'Tiempo remisión horas']


def persistir_dataframe_sivigila(df, tipo):
    registros = df.dropna(how='all').copy()
    resumen = {
        'tipo': tipo,
        'registros_procesados': 0,
        'filas_omitidas_duplicadas': 0,
        'pacientes_nuevos': 0,
        'pacientes_existentes': 0,
        'casos_creados': 0,
        'casos_actualizados': 0,
    }

    for index, row in registros.iterrows():
        numero_fila = index + 2
        if tipo == 'morbilidad':
            resultado = _persistir_fila_morbilidad(row, numero_fila)
        else:
            resultado = _persistir_fila_mortalidad(row, numero_fila)

        resumen['registros_procesados'] += 1
        if resultado.get('duplicado_exacto'):
            resumen['filas_omitidas_duplicadas'] += 1
            continue

        if resultado['paciente_creado']:
            resumen['pacientes_nuevos'] += 1
        else:
            resumen['pacientes_existentes'] += 1

        if resultado['caso_creado']:
            resumen['casos_creados'] += 1
        else:
            resumen['casos_actualizados'] += 1

    return resumen


def _persistir_fila_morbilidad(row, numero_fila):
    identificacion = _resolver_identificacion(
        nombres_col='Nombres y apellidos',
        tipo_id_col='Tipo de ID',
        numero_id_col='N° identificación',
        row=row,
        numero_fila=numero_fila,
    )
    fecha_egreso = _parse_date(_get_value(row, MORBILIDAD_FECHA_EGRESO_COLS))
    causa_principal = _require_text(_get_value(row, ['Causa principal CIE-10']), 'Causa principal CIE-10', numero_fila).upper()
    event_hash = _hash_payload({
        'tipo': 'morbilidad',
        'tipo_identificacion': identificacion['tipo_codigo'],
        'numero_id': identificacion['numero_id'],
        'fecha_egreso': _date_key(fecha_egreso),
        'causa_principal_cie10': causa_principal,
        'momento_ocurrencia': _resolve_momento_ocurrencia(_get_value(row, ['Momento ocurrencia'])),
        'edad_gestacional_sem': _parse_int(_get_value(row, ['Edad gestacional ocurrencia (sem)'])),
    })
    row_hash = _row_hash('morbilidad', row)
    if SivigilaImportacion.objects.filter(row_hash=row_hash).exists():
        return _resultado_duplicado()

    paciente, paciente_creado = _upsert_paciente(identificacion)
    caso, caso_creado = _resolver_caso_morbilidad(paciente, event_hash, fecha_egreso, causa_principal)

    regulacion = _resolve_catalog(CatRegulacionFecundidad, _get_value(row, ['Regulación fecundidad', 'Regulacion fecundidad']))
    terminacion = _resolve_catalog(CatTerminacionGestacion, _get_value(row, MORBILIDAD_TERMINACION_COLS), required=False)

    _upsert_single_related(
        AntecedentesObstetricos,
        {'id_caso': caso},
        {
            'num_gestaciones': _parse_int(_get_value(row, ['N° gestaciones'])),
            'partos_vaginales': _parse_int(_get_value(row, ['Partos vaginales'])),
            'cesareas': _parse_int(_get_value(row, ['Cesáreas'])),
            'abortos': _parse_int(_get_value(row, ['Abortos'])),
            'id_regulacion_fecundidad': regulacion,
            'num_controles_prenatales': _parse_int(_get_value(row, ['N° controles prenatales'])),
            'semanas_inicio_cpn': _parse_int(_get_value(row, ['Semanas inicio CPN'])),
            'id_terminacion_gestacion': terminacion,
            'edad_gestacional_sem': _parse_int(_get_value(row, ['Edad gestacional ocurrencia (sem)'])),
            'momento_ocurrencia': _resolve_momento_ocurrencia(_get_value(row, ['Momento ocurrencia'])),
            'estado_recien_nacido': _normalize_estado_rn(_get_value(row, MORBILIDAD_ESTADO_RN_COLS)),
            'peso_rn_gramos': _parse_int(_get_value(row, MORBILIDAD_PESO_RN_COLS)),
        },
    )

    _upsert_single_related(
        CriteriosEnfermedad,
        {'id_caso': caso},
        {
            'eclampsia': _parse_bool(_get_value(row, ['Eclampsia'])),
            'sepsis_sistemica_severa': _parse_bool(_get_value(row, ['Sepsis sistémica severa'])),
            'hemorragia_obstetrica': _parse_bool(_get_value(row, ['Hemorragia obstétrica severa'])),
            'preeclampsia': _parse_bool(_get_value(row, ['Preeclampsia'])),
            'ruptura_uterina': _parse_bool(_get_value(row, ['Ruptura uterina'])),
            'aborto_septico': 0,
            'embarazo_ectopico': 0,
            'autoinmune': 0,
            'hematologica': 0,
            'oncologica': 0,
            'endocrino_metabolicas': 0,
            'renales': 0,
            'gastrointestinales': 0,
            'tromboembolicos': 0,
            'cardiocerebrovasculares': 0,
            'otras_enfermedades': 0,
        },
    )

    _upsert_single_related(
        CriteriosFallaOrganica,
        {'id_caso': caso},
        {
            'falla_cardiaca': 0,
            'falla_vascular': 0,
            'falla_renal': 0,
            'falla_hepatica': 0,
            'falla_metabolica': 0,
            'falla_cerebral': 0,
            'falla_respiratoria': 0,
            'falla_coagulacion': 0,
        },
    )

    _upsert_single_related(
        CriteriosManejo,
        {'id_caso': caso},
        {
            'ingreso_uci': _parse_bool(_get_value(row, ['Ingreso UCI'])),
            'cirugia_adicional': _parse_bool(_get_value(row, ['Cirugía adicional'])),
            'transfusion': _parse_bool(_get_value(row, ['Transfusión'])),
            'total_criterios': _parse_int(_get_value(row, ['Total criterios'])),
            'accidente': 0,
            'intoxicacion_accidental': 0,
            'intento_suicida': 0,
            'victima_violencia': 0,
            'otros_eventos_sp': 0,
            'cual_evento_sp': None,
        },
    )

    _upsert_single_related(
        ManejoHospitalario,
        {'id_caso': caso},
        {
            'dias_estancia_hosp': _parse_int(_get_value(row, ['Días estancia hospitalaria'])),
            'dias_estancia_uci': _parse_int(_get_value(row, ['Días estancia UCI'])),
            'unidades_transfundidas': _parse_int(_get_value(row, MORBILIDAD_TRANSFUNDIDAS_COLS)),
            'cirugia_1': None,
            'cirugia_1_cual': None,
            'cirugia_2': None,
            'cirugia_2_cual': None,
        },
    )

    grupo_causa = _resolve_catalog_optional_text(CatGrupoCausa, _get_value(row, MORBILIDAD_GRUPO_CAUSA_COLS))
    _upsert_single_related(
        CausasMorbilidad,
        {'id_caso': caso},
        {
            'causa_principal_cie10': causa_principal,
            'id_grupo_causa': grupo_causa,
            'causa_asociada_2': None,
            'causa_asociada_3': None,
            'causa_asociada_4': None,
        },
    )

    remitida = _parse_bool(_get_value(row, ['Remitida'])) if _has_any_value(row, ['Remitida']) else 0
    _upsert_single_related(
        Referencia,
        {'id_caso': caso},
        {
            'remitida': remitida,
            'institucion_ref_1': _clean_text(_get_value(row, MORBILIDAD_INSTITUCION_REF_1_COLS)),
            'institucion_ref_2': _clean_text(_get_value(row, MORBILIDAD_INSTITUCION_REF_2_COLS)),
            'tiempo_remision_h': _parse_decimal(_get_value(row, MORBILIDAD_TIEMPO_REMISION_COLS)),
        },
    )

    _registrar_importacion('morbilidad', row_hash, event_hash, caso.id_caso, identificacion)
    return {'paciente_creado': paciente_creado, 'caso_creado': caso_creado, 'duplicado_exacto': False}


def _persistir_fila_mortalidad(row, numero_fila):
    identificacion = _resolver_identificacion(
        nombres_col='A. Nombres y Apellidos',
        tipo_id_col='B. Tipo ID',
        numero_id_col='C. Número ID',
        row=row,
        numero_fila=numero_fila,
    )

    sitio_defuncion = _resolve_catalog(
        CatSitioDefuncion,
        _get_value(row, ['5.1 Sitio de Defunción']),
        numero_fila=numero_fila,
        nombre_campo='5.1 Sitio de Defunción',
    )
    fecha_defuncion = _parse_date(_get_value(row, MORTALIDAD_FECHA_DEFUNCION_COLS))
    causa_basica = _require_text(_get_value(row, ['10.1 Causa básica CIE-10']), '10.1 Causa básica CIE-10', numero_fila).upper()
    event_hash = _hash_payload({
        'tipo': 'mortalidad',
        'tipo_identificacion': identificacion['tipo_codigo'],
        'numero_id': identificacion['numero_id'],
        'fecha_defuncion': _date_key(fecha_defuncion),
        'causa_basica_cie10': causa_basica,
        'sitio_defuncion': sitio_defuncion.id,
        'momento_muerte': _get_value(row, MORTALIDAD_MOMENTO_MUERTE_COLS),
        'semana_gestacion_muerte': _parse_int(_get_value(row, ['9.2 Semana gestación'])),
    })
    row_hash = _row_hash('mortalidad', row)
    if SivigilaImportacion.objects.filter(row_hash=row_hash).exists():
        return _resultado_duplicado()

    paciente, paciente_creado = _upsert_paciente(identificacion)
    caso, caso_creado = _resolver_caso_mortalidad(paciente, event_hash, sitio_defuncion, fecha_defuncion, causa_basica)

    convivencia = _resolve_catalog(
        CatConvivencia,
        _get_value(row, ['6.1 Convivencia']),
        numero_fila=numero_fila,
        nombre_campo='6.1 Convivencia',
    )
    escolaridad = _resolve_catalog(
        CatEscolaridad,
        _get_value(row, ['6.3 Escolaridad']),
        numero_fila=numero_fila,
        nombre_campo='6.3 Escolaridad',
    )
    regulacion = _resolve_catalog(
        CatRegulacionFecundidad,
        _get_value(row, ['6.4 Regulación Fecundidad', '6.4 Regulacion Fecundidad']),
        numero_fila=numero_fila,
        nombre_campo='6.4 Regulación Fecundidad',
    )

    _upsert_single_related(
        AntecedenteMaterno,
        {'id_caso': caso},
        {
            'id_convivencia': convivencia,
            'otro_convivencia': None,
            'id_escolaridad': escolaridad,
            'id_regulacion_fec': regulacion,
            'gestaciones': _parse_int(_get_value(row, ['6.5 Gestaciones'])),
            'partos_vaginales': _parse_int(_get_value(row, ['6.6 Partos Vaginales'])),
            'cesareas': _parse_int(_get_value(row, ['6.7 Cesáreas'])),
            'nacidos_muertos': _parse_int(_get_value(row, ['6.8 Muertos'])),
            'hijos_vivos': _parse_int(_get_value(row, ['6.9 Vivos'])),
            'abortos': _parse_int(_get_value(row, ['6.10 Abortos'])),
        },
    )

    _upsert_single_related(
        AntecedenteRiesgo,
        {'id_caso': caso},
        {
            'sin_antecedentes': 0,
            'hipertension_cronica': 0,
            'cardiopatias': 0,
            'diabetes': 0,
            'mola_hidatiforme': 0,
            'rn_pretermino': 0,
            'rn_bajo_peso': 0,
            'rn_macrosomico': 0,
            'trastorno_mental': 0,
            'obesidad': 0,
            'desnutricion_cronica': 0,
            'intergenesis_menor_2a': 0,
            'its_distintas': 0,
            'vih_sida': 0,
            'otras_infecciones': 0,
            'rh_negativo': 0,
            'tabaquismo': 0,
            'alcoholismo': 0,
            'sustancias_psicoactivas': 0,
            'deficiencias_socioeconomicas': 0,
            'sifilis': 0,
            'hepatitis_b': 0,
            'otros_factores_riesgo': 0,
            'desc_otros_factores': None,
            'gingivitis_periodontitis': 0,
        },
    )

    _upsert_single_related(
        ComplicacionEmbarazo,
        {'id_caso': caso},
        {
            'preeclampsia': 0,
            'eclampsia': 0,
            'sindrome_hellp': 0,
            'diabetes_gestacional': 0,
            'sepsis': 0,
            'hemorragia_1er_trimestre': 0,
            'hemorragia_2do_trimestre': 0,
            'hemorragia_3er_trimestre': 0,
            'desproporcion_cefalo_pelv': 0,
            'retardo_crecimiento_iu': 0,
            'enfermedad_autoinmune': 0,
            'malaria': 0,
            'embarazo_no_deseado': 0,
            'violencia_gestante': 0,
            'otras_complicaciones': 0,
            'desc_otras_complicaciones': None,
            'gestacion_violencia_sexual': 0,
            'feto_incompatible_vida': 0,
            'sintomas_depresivos': 0,
        },
    )

    remisiones = _resolve_catalog_optional_text(CatRemisiones, _get_value(row, MORTALIDAD_REMISIONES_COLS))
    if remisiones is None:
        remisiones = CatRemisiones.objects.filter(pk=3).first() or CatRemisiones.objects.order_by('id').first()

    personal_cpn = _resolve_catalog_optional_text(CatPersonalSalud, _get_value(row, MORTALIDAD_PERSONAL_CPN_COLS))
    nivel_cpn = _resolve_catalog_optional_text(CatNivelAtencion, _get_value(row, MORTALIDAD_NIVEL_CPN_COLS), extra_field='nivel')
    _upsert_single_related(
        ControlPrenatal,
        {'id_caso': caso},
        {
            'num_cpn': _parse_int(_get_value(row, ['8.1 No. CPN'])),
            'semana_inicio_cpn': _parse_int(_get_value(row, ['8.2 Semana inicio CPN'])),
            'id_personal_cpn': personal_cpn,
            'id_nivel_atencion_cpn': nivel_cpn,
            'id_remisiones': remisiones,
            'compl_feto_rn_cie10': None,
        },
    )

    momento_muerte = _resolve_catalog(
        CatMomentoMuerte,
        _get_value(row, MORTALIDAD_MOMENTO_MUERTE_COLS),
        numero_fila=numero_fila,
        nombre_campo='9.1 Momento de la muerte',
    )
    tipo_parto = _resolve_catalog_optional_text(CatTipoParto, _get_value(row, ['9.4 Tipo de parto']))
    atendido_por = _resolve_catalog_optional_text(CatPersonalSalud, _get_value(row, MORTALIDAD_ATENDIDO_POR_COLS))
    nivel_parto = _resolve_catalog_optional_text(CatNivelAtencion, _get_value(row, MORTALIDAD_NIVEL_PARTO_COLS), extra_field='nivel')
    _upsert_single_related(
        AntecedentePartoPuerperio,
        {'id_caso': caso},
        {
            'id_momento_muerte': momento_muerte,
            'semana_gestacion_muerte': _parse_int(_get_value(row, ['9.2 Semana gestación'])),
            'fecha_parto': _parse_date(_get_value(row, MORTALIDAD_FECHA_PARTO_COLS)),
            'hora_parto': _parse_time(_get_value(row, MORTALIDAD_HORA_PARTO_COLS)),
            'id_tipo_parto': tipo_parto,
            'id_atendido_por': atendido_por,
            'otro_atencion_parto': None,
            'id_nivel_atencion_parto': nivel_parto,
        },
    )

    fuente_causa = _resolve_catalog_optional_text(CatFuenteCausaMuerte, _get_value(row, MORTALIDAD_FUENTE_CAUSA_COLS))
    if fuente_causa is None:
        fuente_causa = CatFuenteCausaMuerte.objects.filter(pk=1).first() or CatFuenteCausaMuerte.objects.order_by('id').first()

    _upsert_single_related(
        CausaMuerte,
        {'id_caso': caso},
        {
            'causa_basica_cie10': causa_basica,
            'id_fuente_causa': fuente_causa,
            'demora_1': _parse_bool(_get_value(row, ['10.3.1 Demora 1'])),
            'demora_2': _parse_bool(_get_value(row, ['10.3.2 Demora 2'])),
            'demora_3': _parse_bool(_get_value(row, ['10.3.3 Demora 3'])),
            'demora_4': _parse_bool(_get_value(row, ['10.3.4 Demora 4'])),
        },
    )

    _registrar_importacion('mortalidad', row_hash, event_hash, caso.id_caso, identificacion)
    return {'paciente_creado': paciente_creado, 'caso_creado': caso_creado, 'duplicado_exacto': False}


def _resolver_identificacion(*, nombres_col, tipo_id_col, numero_id_col, row, numero_fila):
    nombres = _require_text(_get_value(row, [nombres_col]), nombres_col, numero_fila)
    tipo_id_valor = _normalizar_tipo_identificacion(_get_value(row, [tipo_id_col]))
    tipo_identificacion = _resolve_catalog(
        CatTipoId,
        tipo_id_valor,
        numero_fila=numero_fila,
        nombre_campo=tipo_id_col,
        code_field='codigo',
    )
    numero_id = _require_text(_get_value(row, [numero_id_col]), numero_id_col, numero_fila)
    fecha_nacimiento = _parse_date(_get_value(row, ['Fecha de Nacimiento', 'Fecha de nacimiento', 'Fecha nacimiento']))

    return {
        'nombres': nombres,
        'tipo_obj': tipo_identificacion,
        'tipo_codigo': tipo_identificacion.codigo,
        'numero_id': numero_id,
        'fecha_nacimiento': fecha_nacimiento,
    }


def _upsert_paciente(identificacion):
    defaults = {
        'nombres_apellidos': identificacion['nombres'],
    }
    if identificacion.get('fecha_nacimiento') is not None:
        defaults['fecha_nacimiento'] = identificacion['fecha_nacimiento']

    paciente, creado = Paciente.objects.update_or_create(
        id_tipo=identificacion['tipo_obj'],
        numero_id=identificacion['numero_id'],
        defaults=defaults,
    )
    return paciente, creado


def _resolver_caso_morbilidad(paciente, event_hash, fecha_egreso, causa_principal):
    importacion = SivigilaImportacion.objects.filter(tipo='morbilidad', event_hash=event_hash).first()
    if importacion is not None:
        caso = CasoMorbilidad.objects.filter(id_caso=importacion.caso_id, id_paciente=paciente).first()
        if caso is not None:
            if fecha_egreso is not None and caso.fecha_egreso != fecha_egreso:
                caso.fecha_egreso = fecha_egreso
                caso.save(update_fields=['fecha_egreso'])
            return caso, False

    causa_existente = CausasMorbilidad.objects.filter(
        id_caso__id_paciente=paciente,
        causa_principal_cie10=causa_principal,
        id_caso__fecha_egreso=fecha_egreso,
    ).select_related('id_caso').first()
    if causa_existente is not None:
        return causa_existente.id_caso, False

    caso = CasoMorbilidad.objects.create(
        id_paciente=paciente,
        fecha_egreso=fecha_egreso,
    )
    return caso, True


def _resolver_caso_mortalidad(paciente, event_hash, sitio_defuncion, fecha_defuncion, causa_basica):
    importacion = SivigilaImportacion.objects.filter(tipo='mortalidad', event_hash=event_hash).first()
    if importacion is not None:
        caso = CasoMortalidad.objects.filter(id_caso=importacion.caso_id, id_paciente=paciente).first()
        if caso is not None:
            _actualizar_caso_mortalidad(caso, sitio_defuncion, fecha_defuncion)
            return caso, False

    causa_existente = CausaMuerte.objects.filter(
        id_caso__id_paciente=paciente,
        causa_basica_cie10=causa_basica,
        id_caso__fecha_defuncion=fecha_defuncion,
    ).select_related('id_caso').first()
    if causa_existente is not None:
        caso = causa_existente.id_caso
        _actualizar_caso_mortalidad(caso, sitio_defuncion, fecha_defuncion)
        return caso, False

    caso = CasoMortalidad.objects.create(
        id_paciente=paciente,
        id_sitio_defuncion=sitio_defuncion,
        fecha_defuncion=fecha_defuncion,
    )
    return caso, True


def _actualizar_caso_mortalidad(caso, sitio_defuncion, fecha_defuncion):
    campos = []
    if caso.id_sitio_defuncion_id != sitio_defuncion.id:
        caso.id_sitio_defuncion = sitio_defuncion
        campos.append('id_sitio_defuncion')
    if fecha_defuncion is not None and caso.fecha_defuncion != fecha_defuncion:
        caso.fecha_defuncion = fecha_defuncion
        campos.append('fecha_defuncion')
    if campos:
        caso.save(update_fields=campos)


def _registrar_importacion(tipo, row_hash, event_hash, caso_id, identificacion):
    SivigilaImportacion.objects.create(
        tipo=tipo,
        row_hash=row_hash,
        event_hash=event_hash,
        caso_id=caso_id,
        numero_id=identificacion['numero_id'],
        tipo_identificacion=identificacion['tipo_codigo'],
    )


def _resultado_duplicado():
    return {
        'paciente_creado': False,
        'caso_creado': False,
        'duplicado_exacto': True,
    }


def _row_hash(tipo, row):
    normalizado = {columna: _normalize_hash_value(row[columna]) for columna in sorted(row.index.tolist())}
    return _hash_payload({'tipo': tipo, 'row': normalizado})


def _hash_payload(payload):
    serializado = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str, separators=(',', ':'))
    return sha256(serializado.encode('utf-8')).hexdigest()


def _normalize_hash_value(value):
    if _is_empty(value):
        return None
    if isinstance(value, (int, float)):
        numero = float(value)
        if numero.is_integer():
            return int(numero)
        return numero
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except TypeError:
            pass
    return _clean_text(value)


def _date_key(value):
    return value.isoformat() if value is not None else None


def _resolve_catalog(model, value, *, numero_fila=None, nombre_campo=None, required=True, code_field=None, extra_field=None):
    if _is_empty(value):
        if required:
            raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
        return None

    texto = _clean_text(value)
    if texto is None:
        if required:
            raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
        return None

    obj = _resolve_catalog_by_id(model, value)
    if obj is None:
        obj = _resolve_catalog_by_fields(model, texto, code_field=code_field, extra_field=extra_field)

    if obj is not None:
        return obj

    if required:
        raise ValueError(f'Fila {numero_fila}: no se encontró catálogo para {nombre_campo}={texto!r}.')
    return None


def _resolve_catalog_optional_text(model, value, extra_field=None):
    return _resolve_catalog(model, value, required=False, extra_field=extra_field)


def _resolve_catalog_by_id(model, value):
    if isinstance(value, (int, float)) and not pd.isna(value):
        return model.objects.filter(pk=int(value)).first()
    return None


def _resolve_catalog_by_fields(model, texto, *, code_field=None, extra_field=None):
    if code_field:
        obj = model.objects.filter(**{f'{code_field}__iexact': texto}).first()
        if obj is not None:
            return obj

    simplificado = _slugify(texto)
    for candidato in model.objects.all():
        if any(_slugify(valor) == simplificado for valor in _catalog_comparables(candidato, code_field, extra_field)):
            return candidato
    return None


def _catalog_comparables(candidato, code_field, extra_field):
    comparables = []
    if hasattr(candidato, 'descripcion'):
        comparables.append(getattr(candidato, 'descripcion'))
    if code_field and hasattr(candidato, code_field):
        comparables.append(getattr(candidato, code_field))
    if extra_field and hasattr(candidato, extra_field):
        comparables.append(getattr(candidato, extra_field))
    return comparables


def _upsert_single_related(model, lookup, defaults):
    instancia = model.objects.filter(**lookup).first()
    if instancia is None:
        return model.objects.create(**lookup, **defaults), True

    for campo, valor in defaults.items():
        setattr(instancia, campo, valor)
    instancia.save(update_fields=list(defaults.keys()))
    return instancia, False


def _get_value(row, columns):
    for column in columns:
        if column in row:
            value = row[column]
            if not _is_empty(value):
                return value
    return None


def _has_any_value(row, columns):
    return _get_value(row, columns) is not None


def _is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == '' or value.strip().lower() in {'nan', 'none', 'null'}
    return pd.isna(value)


def _clean_text(value):
    if _is_empty(value):
        return None
    return str(value).strip()


def _normalizar_tipo_identificacion(value):
    texto = _clean_text(value)
    if texto is None:
        return None

    clave = _slugify(texto)
    alias = TIPO_ID_ALIASES.get(clave)
    return alias or texto


def _slugify(value):
    texto = _clean_text(value)
    if texto is None:
        return None
    sin_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    normalizado = sin_acentos.lower().replace('>', ' gt ').replace('<', ' lt ')
    solo_alfanumerico = re.sub(r'[^a-zA-Z0-9]+', ' ', normalizado)
    return ' '.join(solo_alfanumerico.split())


def _require_text(value, nombre_campo, numero_fila):
    texto = _clean_text(value)
    if texto is None:
        raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
    return texto


def _parse_int(value):
    if _is_empty(value):
        return None
    return int(float(value))


def _parse_decimal(value):
    if _is_empty(value):
        return None
    return round(float(value), 1)


_EXCEL_SERIAL_ORIGIN = pd.Timestamp('1899-12-30')


def _parse_date(value):
    if _is_empty(value):
        return None
    # Intento 1: conversión estándar con dayfirst=True (DD/MM/YYYY colombiano)
    fecha = pd.to_datetime(value, errors='coerce', dayfirst=True)
    if not pd.isna(fecha):
        return fecha.date()
    # Intento 2: serial numérico de Excel
    try:
        n = int(float(value))
        if 1000 < n < 100000:
            return (_EXCEL_SERIAL_ORIGIN + pd.Timedelta(days=n)).date()
    except (ValueError, TypeError):
        pass
    return None


def _parse_time(value):
    if _is_empty(value):
        return None
    hora = pd.to_datetime(value, errors='coerce')
    if pd.isna(hora):
        return None
    return hora.time()


def _parse_bool(value):
    if _is_empty(value):
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if float(value) != 0 else 0
    texto = _slugify(value)
    return 1 if texto in {'1', 'si', 's', 'sí', 'true', 'x', 'yes', 'y'} else 0


def _resolve_momento_ocurrencia(value):
    if _is_empty(value):
        return None
    if isinstance(value, (int, float)):
        codigo = int(value)
        return {
            1: 'Antes',
            2: 'Durante',
            3: 'Despues',
            4: 'Despues',
        }.get(codigo)

    texto = _slugify(value)
    equivalencias = {
        'antes': 'Antes',
        'durante': 'Durante',
        'despues': 'Despues',
        'después': 'Despues',
    }
    return equivalencias.get(texto)


def _normalize_estado_rn(value):
    if _is_empty(value):
        return None
    if isinstance(value, (int, float)):
        return {1: 'Vivo', 2: 'Muerto'}.get(int(value))
    texto = _slugify(value)
    equivalencias = {
        'vivo': 'Vivo',
        'muerto': 'Muerto',
    }
    return equivalencias.get(texto)