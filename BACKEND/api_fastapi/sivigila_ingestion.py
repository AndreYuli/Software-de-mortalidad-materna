import unicodedata
from hashlib import sha256
import json
import re
import datetime

import pandas as pd

from .models_sqlalchemy import (
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


_CATALOG_BY_ID = {}
_CATALOG_BY_FIELDS = {}
_PACIENTE_CACHE = {}
_EXISTING_HASHES = set()
_RELATED_EXISTS_CACHE = {}


def persistir_dataframe_sivigila(db, df, tipo):
    global _CATALOG_BY_ID, _CATALOG_BY_FIELDS, _PACIENTE_CACHE, _EXISTING_HASHES, _RELATED_EXISTS_CACHE
    _CATALOG_BY_ID = {}
    _CATALOG_BY_FIELDS = {}
    _PACIENTE_CACHE = {}
    _RELATED_EXISTS_CACHE = {}
    
    registros = df.dropna(how='all').copy()
    
    # Pre-cargar hashes existentes en bloque para evitar consultas en bucle
    try:
        df_hashes = registros.apply(lambda r: _row_hash(tipo, r), axis=1)
        _EXISTING_HASHES = set(
            row[0] for row in db.query(SivigilaImportacion.row_hash)
            .filter(SivigilaImportacion.row_hash.in_(df_hashes.tolist())).all()
        )
    except Exception:
        _EXISTING_HASHES = set()
        df_hashes = pd.Series([_row_hash(tipo, r) for _, r in registros.iterrows()], index=registros.index)

    resumen = {
        'tipo': tipo,
        'registros_procesados': 0,
        'filas_omitidas_duplicadas': 0,
        'pacientes_nuevos': 0,
        'pacientes_existentes': 0,
        'casos_creados': 0,
        'casos_actualizados': 0,
    }

    # Pass 1: Pre-resolve and validate identification / key columns
    pass1_data = {}
    non_duplicate_indices = []
    numeros_id = set()
    event_hashes_list = []
    
    for index, row in registros.iterrows():
        numero_fila = index + 2
        row_hash = df_hashes.loc[index]
        
        resumen['registros_procesados'] += 1
        if row_hash in _EXISTING_HASHES:
            resumen['filas_omitidas_duplicadas'] += 1
            continue
            
        non_duplicate_indices.append(index)
        
        if tipo == 'morbilidad':
            identificacion = _resolver_identificacion(
                db=db,
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
            pass1_data[index] = {
                'identificacion': identificacion,
                'fecha_egreso': fecha_egreso,
                'causa_principal': causa_principal,
                'event_hash': event_hash,
                'row_hash': row_hash,
            }
        else:
            identificacion = _resolver_identificacion(
                db=db,
                nombres_col='A. Nombres y Apellidos',
                tipo_id_col='B. Tipo ID',
                numero_id_col='C. Número ID',
                row=row,
                numero_fila=numero_fila,
            )
            sitio_defuncion = _resolve_catalog(
                db,
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
            pass1_data[index] = {
                'identificacion': identificacion,
                'sitio_defuncion': sitio_defuncion,
                'fecha_defuncion': fecha_defuncion,
                'causa_basica': causa_basica,
                'event_hash': event_hash,
                'row_hash': row_hash,
            }
            
        numeros_id.add(identificacion['numero_id'])
        event_hashes_list.append(event_hash)

    if not non_duplicate_indices:
        return resumen

    # --- Preload Caches in Bulk ---
    
    # A. Preload Pacientes
    if numeros_id:
        list_nums = list(numeros_id)
        for i in range(0, len(list_nums), 1000):
            chunk = list_nums[i:i+1000]
            existing_pacientes = db.query(Paciente).filter(Paciente.numero_id.in_(chunk)).all()
            for p in existing_pacientes:
                _PACIENTE_CACHE[(p.id_tipo_id, p.numero_id)] = p

    # B. Preload SivigilaImportacion
    _IMPORT_CACHE = {}
    if event_hashes_list:
        unique_events = list(set(event_hashes_list))
        for i in range(0, len(unique_events), 1000):
            chunk = unique_events[i:i+1000]
            existing_imports = db.query(SivigilaImportacion).filter(
                SivigilaImportacion.tipo == tipo,
                SivigilaImportacion.event_hash.in_(chunk)
            ).all()
            for imp in existing_imports:
                _IMPORT_CACHE[imp.event_hash] = imp

    # C. Preload Cases and Causa
    existing_caso_ids = [imp.caso_id for imp in _IMPORT_CACHE.values()]
    patient_ids = [p.id_paciente for p in _PACIENTE_CACHE.values()]
    
    _CASO_BY_ID = {}
    _CASO_BY_PACIENTE_FECHA = {}
    _CAUSA_CACHE = {}
    
    if tipo == 'morbilidad':
        if patient_ids:
            for i in range(0, len(patient_ids), 1000):
                chunk = patient_ids[i:i+1000]
                cases = db.query(CasoMorbilidad).filter(CasoMorbilidad.id_paciente.in_(chunk)).all()
                for c in cases:
                    _CASO_BY_ID[c.id_caso] = c
                    _CASO_BY_PACIENTE_FECHA[(c.id_paciente, c.fecha_egreso)] = c
                    if c.id_caso not in existing_caso_ids:
                        existing_caso_ids.append(c.id_caso)
        if existing_caso_ids:
            for i in range(0, len(existing_caso_ids), 1000):
                chunk = existing_caso_ids[i:i+1000]
                causas = db.query(CausasMorbilidad).filter(CausasMorbilidad.id_caso.in_(chunk)).all()
                for cau in causas:
                    _CAUSA_CACHE[cau.id_caso] = cau
    else:
        if patient_ids:
            for i in range(0, len(patient_ids), 1000):
                chunk = patient_ids[i:i+1000]
                cases = db.query(CasoMortalidad).filter(CasoMortalidad.id_paciente.in_(chunk)).all()
                for c in cases:
                    _CASO_BY_ID[c.id_caso] = c
                    _CASO_BY_PACIENTE_FECHA[(c.id_paciente, c.fecha_defuncion)] = c
                    if c.id_caso not in existing_caso_ids:
                        existing_caso_ids.append(c.id_caso)
        if existing_caso_ids:
            for i in range(0, len(existing_caso_ids), 1000):
                chunk = existing_caso_ids[i:i+1000]
                causas = db.query(CausaMuerte).filter(CausaMuerte.id_caso.in_(chunk)).all()
                for cau in causas:
                    _CAUSA_CACHE[cau.id_caso] = cau

    # D. Preload Related Records Existence
    related_models_morbilidad = [
        AntecedentesObstetricos, CriteriosEnfermedad, CriteriosFallaOrganica,
        CriteriosManejo, ManejoHospitalario, CausasMorbilidad, Referencia
    ]
    related_models_mortalidad = [
        AntecedenteMaterno, AntecedenteRiesgo, ComplicacionEmbarazo,
        ControlPrenatal, AntecedentePartoPuerperio, CausaMuerte
    ]
    models_to_preload = related_models_morbilidad if tipo == 'morbilidad' else related_models_mortalidad
    for model in models_to_preload:
        _RELATED_EXISTS_CACHE[model] = set()
        if existing_caso_ids:
            for i in range(0, len(existing_caso_ids), 1000):
                chunk = existing_caso_ids[i:i+1000]
                existing_ids = db.query(model.id_caso).filter(model.id_caso.in_(chunk)).all()
                for row in existing_ids:
                    _RELATED_EXISTS_CACHE[model].add(row[0])

    # --- Pass 2: Upsert Patients ---
    for index in non_duplicate_indices:
        identificacion = pass1_data[index]['identificacion']
        cache_key = (identificacion['tipo_obj'].id, identificacion['numero_id'])
        if cache_key not in _PACIENTE_CACHE:
            paciente = Paciente(
                id_tipo_id=identificacion['tipo_obj'].id,
                numero_id=identificacion['numero_id'],
                nombres_apellidos=identificacion['nombres'],
                fecha_nacimiento=identificacion.get('fecha_nacimiento'),
                creado_en=datetime.datetime.utcnow()
            )
            db.add(paciente)
            _PACIENTE_CACHE[cache_key] = paciente
            resumen['pacientes_nuevos'] += 1
        else:
            paciente = _PACIENTE_CACHE[cache_key]
            if paciente.nombres_apellidos != identificacion['nombres']:
                paciente.nombres_apellidos = identificacion['nombres']
            if identificacion.get('fecha_nacimiento') is not None and paciente.fecha_nacimiento != identificacion['fecha_nacimiento']:
                paciente.fecha_nacimiento = identificacion['fecha_nacimiento']
            resumen['pacientes_existentes'] += 1

    # Flush once to get all new Patient IDs!
    db.flush()

    # --- Pass 3: Upsert Cases ---
    row_cases = {} # index -> (caso, caso_creado)
    for index in non_duplicate_indices:
        row = registros.loc[index]
        pdata = pass1_data[index]
        identificacion = pdata['identificacion']
        cache_key = (identificacion['tipo_obj'].id, identificacion['numero_id'])
        paciente = _PACIENTE_CACHE[cache_key]
        event_hash = pdata['event_hash']

        if tipo == 'morbilidad':
            fecha_egreso = pdata['fecha_egreso']
            causa_principal = pdata['causa_principal']
            
            importacion = _IMPORT_CACHE.get(event_hash)
            caso = None
            if importacion is not None:
                caso = _CASO_BY_ID.get(importacion.caso_id)
            if caso is None:
                caso_potencial = _CASO_BY_PACIENTE_FECHA.get((paciente.id_paciente, fecha_egreso))
                if caso_potencial is not None:
                    causa_existente = _CAUSA_CACHE.get(caso_potencial.id_caso)
                    if causa_existente is not None and causa_existente.causa_principal_cie10 == causa_principal:
                        caso = caso_potencial
            
            caso_creado = False
            if caso is None:
                caso = CasoMorbilidad(
                    id_paciente=paciente.id_paciente,
                    fecha_egreso=fecha_egreso,
                    creado_en=datetime.datetime.utcnow()
                )
                db.add(caso)
                _CASO_BY_PACIENTE_FECHA[(paciente.id_paciente, fecha_egreso)] = caso
                caso_creado = True
                resumen['casos_creados'] += 1
            else:
                if fecha_egreso is not None and caso.fecha_egreso != fecha_egreso:
                    caso.fecha_egreso = fecha_egreso
                resumen['casos_actualizados'] += 1
                
            row_cases[index] = (caso, caso_creado)
        else:
            sitio_defuncion = pdata['sitio_defuncion']
            fecha_defuncion = pdata['fecha_defuncion']
            causa_basica = pdata['causa_basica']
            
            importacion = _IMPORT_CACHE.get(event_hash)
            caso = None
            if importacion is not None:
                caso = _CASO_BY_ID.get(importacion.caso_id)
            if caso is None:
                caso_potencial = _CASO_BY_PACIENTE_FECHA.get((paciente.id_paciente, fecha_defuncion))
                if caso_potencial is not None:
                    causa_existente = _CAUSA_CACHE.get(caso_potencial.id_caso)
                    if causa_existente is not None and causa_existente.causa_basica_cie10 == causa_basica:
                        caso = caso_potencial
            
            caso_creado = False
            if caso is None:
                caso = CasoMortalidad(
                    id_paciente=paciente.id_paciente,
                    id_sitio_defuncion=sitio_defuncion.id,
                    fecha_defuncion=fecha_defuncion,
                    creado_en=datetime.datetime.utcnow()
                )
                db.add(caso)
                _CASO_BY_PACIENTE_FECHA[(paciente.id_paciente, fecha_defuncion)] = caso
                caso_creado = True
                resumen['casos_creados'] += 1
            else:
                _actualizar_caso_mortalidad(db, caso, sitio_defuncion, fecha_defuncion)
                resumen['casos_actualizados'] += 1
                
            row_cases[index] = (caso, caso_creado)

    # Flush once to get all new Case IDs!
    db.flush()

    # --- Pass 4: Upsert Related Records ---
    for index in non_duplicate_indices:
        row = registros.loc[index]
        pdata = pass1_data[index]
        identificacion = pdata['identificacion']
        event_hash = pdata['event_hash']
        row_hash = pdata['row_hash']
        caso, caso_creado = row_cases[index]

        if tipo == 'morbilidad':
            fecha_egreso = pdata['fecha_egreso']
            causa_principal = pdata['causa_principal']
            
            regulacion = _resolve_catalog(
                db,
                CatRegulacionFecundidad,
                _get_value(row, ['Regulación fecundidad', 'Regulacion fecundidad']),
                numero_fila=numero_fila,
                nombre_campo='Regulación fecundidad'
            )
            terminacion = _resolve_catalog(
                db,
                CatTerminacionGestacion,
                _get_value(row, MORBILIDAD_TERMINACION_COLS),
                required=False,
                numero_fila=numero_fila,
                nombre_campo='Terminación de la gestación'
            )

            _upsert_single_related(
                db,
                AntecedentesObstetricos,
                {'id_caso': caso.id_caso},
                {
                    'num_gestaciones': _parse_int(_get_value(row, ['N° gestaciones'])),
                    'partos_vaginales': _parse_int(_get_value(row, ['Partos vaginales'])),
                    'cesareas': _parse_int(_get_value(row, ['Cesáreas'])),
                    'abortos': _parse_int(_get_value(row, ['Abortos'])),
                    'id_regulacion_fecundidad': regulacion.id if regulacion else None,
                    'num_controles_prenatales': _parse_int(_get_value(row, ['N° controles prenatales'])),
                    'semanas_inicio_cpn': _parse_int(_get_value(row, ['Semanas inicio CPN'])),
                    'id_terminacion_gestacion': terminacion.id if terminacion else None,
                    'edad_gestacional_sem': _parse_int(_get_value(row, ['Edad gestacional ocurrencia (sem)'])),
                    'momento_ocurrencia': _resolve_momento_ocurrencia(_get_value(row, ['Momento ocurrencia'])),
                    'estado_recien_nacido': _normalize_estado_rn(_get_value(row, MORBILIDAD_ESTADO_RN_COLS)),
                    'peso_rn_gramos': _parse_int(_get_value(row, MORBILIDAD_PESO_RN_COLS)),
                },
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                CriteriosEnfermedad,
                {'id_caso': caso.id_caso},
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
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                CriteriosFallaOrganica,
                {'id_caso': caso.id_caso},
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
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                CriteriosManejo,
                {'id_caso': caso.id_caso},
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
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                ManejoHospitalario,
                {'id_caso': caso.id_caso},
                {
                    'dias_estancia_hosp': _parse_int(_get_value(row, ['Días estancia hospitalaria'])),
                    'dias_estancia_uci': _parse_int(_get_value(row, ['Días estancia UCI'])),
                    'unidades_transfundidas': _parse_int(_get_value(row, MORBILIDAD_TRANSFUNDIDAS_COLS)),
                    'cirugia_1': None,
                    'cirugia_1_cual': None,
                    'cirugia_2': None,
                    'cirugia_2_cual': None,
                },
                caso_creado=caso_creado
            )

            grupo_causa = _resolve_catalog_optional_text(db, CatGrupoCausa, _get_value(row, MORBILIDAD_GRUPO_CAUSA_COLS))
            _upsert_single_related(
                db,
                CausasMorbilidad,
                {'id_caso': caso.id_caso},
                {
                    'causa_principal_cie10': causa_principal,
                    'id_grupo_causa': grupo_causa.id if grupo_causa else None,
                    'causa_asociada_2': None,
                    'causa_asociada_3': None,
                    'causa_asociada_4': None,
                },
                caso_creado=caso_creado
            )

            remitida = _parse_bool(_get_value(row, ['Remitida'])) if _has_any_value(row, ['Remitida']) else 0
            _upsert_single_related(
                db,
                Referencia,
                {'id_caso': caso.id_caso},
                {
                    'remitida': remitida,
                    'institucion_ref_1': _clean_text(_get_value(row, MORBILIDAD_INSTITUCION_REF_1_COLS)),
                    'institucion_ref_2': _clean_text(_get_value(row, MORBILIDAD_INSTITUCION_REF_2_COLS)),
                    'tiempo_remision_h': _parse_decimal(_get_value(row, MORBILIDAD_TIEMPO_REMISION_COLS)),
                },
                caso_creado=caso_creado
            )
        else:
            sitio_defuncion = pdata['sitio_defuncion']
            fecha_defuncion = pdata['fecha_defuncion']
            causa_basica = pdata['causa_basica']

            convivencia = _resolve_catalog(db, CatConvivencia, _get_value(row, ['6.1 Convivencia']), numero_fila=numero_fila, nombre_campo='6.1 Convivencia')
            escolaridad = _resolve_catalog(db, CatEscolaridad, _get_value(row, ['6.3 Escolaridad']), numero_fila=numero_fila, nombre_campo='6.3 Escolaridad')
            regulacion = _resolve_catalog(db, CatRegulacionFecundidad, _get_value(row, ['6.4 Regulación Fecundidad', '6.4 Regulacion Fecundidad']), numero_fila=numero_fila, nombre_campo='6.4 Regulación Fecundidad')

            _upsert_single_related(
                db,
                AntecedenteMaterno,
                {'id_caso': caso.id_caso},
                {
                    'id_convivencia': convivencia.id if convivencia else None,
                    'otro_convivencia': None,
                    'id_escolaridad': escolaridad.id if escolaridad else None,
                    'id_regulacion_fec': regulacion.id if regulacion else None,
                    'gestaciones': _parse_int(_get_value(row, ['6.5 Gestaciones'])),
                    'partos_vaginales': _parse_int(_get_value(row, ['6.6 Partos Vaginales'])),
                    'cesareas': _parse_int(_get_value(row, ['6.7 Cesáreas'])),
                    'nacidos_muertos': _parse_int(_get_value(row, ['6.8 Muertos'])),
                    'hijos_vivos': _parse_int(_get_value(row, ['6.9 Vivos'])),
                    'abortos': _parse_int(_get_value(row, ['6.10 Abortos'])),
                },
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                AntecedenteRiesgo,
                {'id_caso': caso.id_caso},
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
                caso_creado=caso_creado
            )

            _upsert_single_related(
                db,
                ComplicacionEmbarazo,
                {'id_caso': caso.id_caso},
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
                caso_creado=caso_creado
            )

            remisiones = _resolve_catalog_optional_text(db, CatRemisiones, _get_value(row, MORTALIDAD_REMISIONES_COLS))
            if remisiones is None:
                remisiones = db.query(CatRemisiones).filter(CatRemisiones.id == 3).first() or db.query(CatRemisiones).order_by(CatRemisiones.id).first()

            personal_cpn = _resolve_catalog_optional_text(db, CatPersonalSalud, _get_value(row, MORTALIDAD_PERSONAL_CPN_COLS))
            nivel_cpn = _resolve_catalog_optional_text(db, CatNivelAtencion, _get_value(row, MORTALIDAD_NIVEL_CPN_COLS), extra_field='nivel')
            _upsert_single_related(
                db,
                ControlPrenatal,
                {'id_caso': caso.id_caso},
                {
                    'num_cpn': _parse_int(_get_value(row, ['8.1 No. CPN'])),
                    'semana_inicio_cpn': _parse_int(_get_value(row, ['8.2 Semana inicio CPN'])),
                    'id_personal_cpn': personal_cpn.id if personal_cpn else None,
                    'id_nivel_atencion_cpn': nivel_cpn.id if nivel_cpn else None,
                    'id_remisiones': remisiones.id if remisiones else None,
                    'compl_feto_rn_cie10': None,
                },
                caso_creado=caso_creado
            )

            momento_muerte = _resolve_catalog(db, CatMomentoMuerte, _get_value(row, MORTALIDAD_MOMENTO_MUERTE_COLS), numero_fila=numero_fila, nombre_campo='9.1 Momento de la muerte')
            tipo_parto = _resolve_catalog_optional_text(db, CatTipoParto, _get_value(row, ['9.4 Tipo de parto']))
            atendido_por = _resolve_catalog_optional_text(db, CatPersonalSalud, _get_value(row, MORTALIDAD_ATENDIDO_POR_COLS))
            nivel_parto = _resolve_catalog_optional_text(db, CatNivelAtencion, _get_value(row, MORTALIDAD_NIVEL_PARTO_COLS), extra_field='nivel')
            _upsert_single_related(
                db,
                AntecedentePartoPuerperio,
                {'id_caso': caso.id_caso},
                {
                    'id_momento_muerte': momento_muerte.id if momento_muerte else None,
                    'semana_gestacion_muerte': _parse_int(_get_value(row, ['9.2 Semana gestación'])),
                    'fecha_parto': _parse_date(_get_value(row, MORTALIDAD_FECHA_PARTO_COLS)),
                    'hora_parto': _parse_time(_get_value(row, MORTALIDAD_HORA_PARTO_COLS)),
                    'id_tipo_parto': tipo_parto.id if tipo_parto else None,
                    'id_atendido_por': atendido_por.id if atendido_por else None,
                    'otro_atencion_parto': None,
                    'id_nivel_atencion_parto': nivel_parto.id if nivel_parto else None,
                },
                caso_creado=caso_creado
            )

            fuente_causa = _resolve_catalog_optional_text(db, CatFuenteCausaMuerte, _get_value(row, MORTALIDAD_FUENTE_CAUSA_COLS))
            if fuente_causa is None:
                fuente_causa = db.query(CatFuenteCausaMuerte).filter(CatFuenteCausaMuerte.id == 1).first() or db.query(CatFuenteCausaMuerte).order_by(CatFuenteCausaMuerte.id).first()

            _upsert_single_related(
                db,
                CausaMuerte,
                {'id_caso': caso.id_caso},
                {
                    'causa_basica_cie10': causa_basica,
                    'id_fuente_causa': fuente_causa.id if fuente_causa else None,
                    'demora_1': _parse_bool(_get_value(row, ['10.3.1 Demora 1'])),
                    'demora_2': _parse_bool(_get_value(row, ['10.3.2 Demora 2'])),
                    'demora_3': _parse_bool(_get_value(row, ['10.3.3 Demora 3'])),
                    'demora_4': _parse_bool(_get_value(row, ['10.3.4 Demora 4'])),
                },
                caso_creado=caso_creado
            )

        _registrar_importacion(db, tipo, row_hash, event_hash, caso.id_caso, identificacion)

    return resumen



def _resolver_identificacion(*, db, nombres_col, tipo_id_col, numero_id_col, row, numero_fila):
    nombres = _require_text(_get_value(row, [nombres_col]), nombres_col, numero_fila)
    tipo_id_valor = _normalizar_tipo_identificacion(_get_value(row, [tipo_id_col]))
    tipo_identificacion = _resolve_catalog(
        db,
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


def _upsert_paciente(db, identificacion):
    global _PACIENTE_CACHE
    cache_key = (identificacion['tipo_obj'].id, identificacion['numero_id'])
    if cache_key in _PACIENTE_CACHE:
        return _PACIENTE_CACHE[cache_key], False

    paciente = db.query(Paciente).filter(
        Paciente.id_tipo_id == identificacion['tipo_obj'].id,
        Paciente.numero_id == identificacion['numero_id']
    ).first()

    creado = False
    if paciente is None:
        paciente = Paciente(
            id_tipo_id=identificacion['tipo_obj'].id,
            numero_id=identificacion['numero_id'],
            nombres_apellidos=identificacion['nombres'],
            fecha_nacimiento=identificacion.get('fecha_nacimiento'),
            creado_en=datetime.datetime.utcnow()
        )
        db.add(paciente)
        db.flush()
        creado = True
    else:
        needs_flush = False
        if paciente.nombres_apellidos != identificacion['nombres']:
            paciente.nombres_apellidos = identificacion['nombres']
            needs_flush = True
        if identificacion.get('fecha_nacimiento') is not None and paciente.fecha_nacimiento != identificacion['fecha_nacimiento']:
            paciente.fecha_nacimiento = identificacion['fecha_nacimiento']
            needs_flush = True
        if needs_flush:
            db.flush()

    _PACIENTE_CACHE[cache_key] = paciente
    return paciente, creado

    return paciente, creado


def _resolver_caso_morbilidad(db, paciente, event_hash, fecha_egreso, causa_principal):
    importacion = db.query(SivigilaImportacion).filter(
        SivigilaImportacion.tipo == 'morbilidad',
        SivigilaImportacion.event_hash == event_hash
    ).first()

    if importacion is not None:
        caso = db.query(CasoMorbilidad).filter(
            CasoMorbilidad.id_caso == importacion.caso_id,
            CasoMorbilidad.id_paciente == paciente.id_paciente
        ).first()
        if caso is not None:
            if fecha_egreso is not None and caso.fecha_egreso != fecha_egreso:
                caso.fecha_egreso = fecha_egreso
                db.flush()
            return caso, False

    causa_existente = db.query(CausasMorbilidad).join(
        CasoMorbilidad, CausasMorbilidad.id_caso == CasoMorbilidad.id_caso
    ).filter(
        CasoMorbilidad.id_paciente == paciente.id_paciente,
        CausasMorbilidad.causa_principal_cie10 == causa_principal,
        CasoMorbilidad.fecha_egreso == fecha_egreso
    ).first()

    if causa_existente is not None:
        caso = db.query(CasoMorbilidad).filter(CasoMorbilidad.id_caso == causa_existente.id_caso).first()
        return caso, False

    caso = CasoMorbilidad(
        id_paciente=paciente.id_paciente,
        fecha_egreso=fecha_egreso
    )
    db.add(caso)
    db.flush()
    return caso, True


def _resolver_caso_mortalidad(db, paciente, event_hash, sitio_defuncion, fecha_defuncion, causa_basica):
    importacion = db.query(SivigilaImportacion).filter(
        SivigilaImportacion.tipo == 'mortalidad',
        SivigilaImportacion.event_hash == event_hash
    ).first()

    if importacion is not None:
        caso = db.query(CasoMortalidad).filter(
            CasoMortalidad.id_caso == importacion.caso_id,
            CasoMortalidad.id_paciente == paciente.id_paciente
        ).first()
        if caso is not None:
            _actualizar_caso_mortalidad(db, caso, sitio_defuncion, fecha_defuncion)
            return caso, False

    causa_existente = db.query(CausaMuerte).join(
        CasoMortalidad, CausaMuerte.id_caso == CasoMortalidad.id_caso
    ).filter(
        CasoMortalidad.id_paciente == paciente.id_paciente,
        CausaMuerte.causa_basica_cie10 == causa_basica,
        CasoMortalidad.fecha_defuncion == fecha_defuncion
    ).first()

    if causa_existente is not None:
        caso = db.query(CasoMortalidad).filter(CasoMortalidad.id_caso == causa_existente.id_caso).first()
        _actualizar_caso_mortalidad(db, caso, sitio_defuncion, fecha_defuncion)
        return caso, False

    caso = CasoMortalidad(
        id_paciente=paciente.id_paciente,
        id_sitio_defuncion=sitio_defuncion.id,
        fecha_defuncion=fecha_defuncion
    )
    db.add(caso)
    db.flush()
    return caso, True


def _actualizar_caso_mortalidad(db, caso, sitio_defuncion, fecha_defuncion):
    changed = False
    if caso.id_sitio_defuncion != sitio_defuncion.id:
        caso.id_sitio_defuncion = sitio_defuncion.id
        changed = True
    if fecha_defuncion is not None and caso.fecha_defuncion != fecha_defuncion:
        caso.fecha_defuncion = fecha_defuncion
        changed = True
    if changed:
        db.flush()


def _registrar_importacion(db, tipo, row_hash, event_hash, caso_id, identificacion):
    imp = SivigilaImportacion(
        tipo=tipo,
        row_hash=row_hash,
        event_hash=event_hash,
        caso_id=caso_id,
        numero_id=identificacion['numero_id'],
        tipo_identificacion=identificacion['tipo_codigo'],
        creado_en=datetime.datetime.utcnow()
    )
    db.add(imp)



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


def _resolve_catalog(db, model, value, *, numero_fila=None, nombre_campo=None, required=True, code_field=None, extra_field=None):
    if _is_empty(value):
        if required:
            raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
        return None

    texto = _clean_text(value)
    if texto is None:
        if required:
            raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
        return None

    obj = _resolve_catalog_by_id(db, model, value)
    if obj is None:
        obj = _resolve_catalog_by_fields(db, model, texto, code_field=code_field, extra_field=extra_field)

    if obj is not None:
        return obj

    if required:
        raise ValueError(f'Fila {numero_fila}: no se encontró catálogo para {nombre_campo}={texto!r}.')
    return None


def _resolve_catalog_optional_text(db, model, value, extra_field=None):
    return _resolve_catalog(db, model, value, required=False, extra_field=extra_field)


def _resolve_catalog_by_id(db, model, value):
    global _CATALOG_BY_ID
    val_id = None
    try:
        if not isinstance(value, bool):
            val_id = int(float(value))
    except (ValueError, TypeError):
        pass
            
    if val_id is not None:
        if model not in _CATALOG_BY_ID:
            all_objs = db.query(model).all()
            _CATALOG_BY_ID[model] = {getattr(obj, 'id_catalogo', getattr(obj, 'id', None)): obj for obj in all_objs}
        return _CATALOG_BY_ID[model].get(val_id)
    return None


def _resolve_catalog_by_fields(db, model, texto, *, code_field=None, extra_field=None):
    global _CATALOG_BY_FIELDS
    if model not in _CATALOG_BY_FIELDS:
        _CATALOG_BY_FIELDS[model] = db.query(model).all()

    if code_field:
        for obj in _CATALOG_BY_FIELDS[model]:
            code_val = getattr(obj, code_field, None)
            if code_val and str(code_val).strip().lower() == texto.lower():
                return obj

    simplificado = _slugify(texto)
    for candidato in _CATALOG_BY_FIELDS[model]:
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


def _upsert_single_related(db, model, lookup, defaults, caso_creado=False):
    global _RELATED_EXISTS_CACHE
    # Map model instance lookups to their primary keys
    processed_lookup = {}
    for k, v in lookup.items():
        if hasattr(v, '__table__'):
            from sqlalchemy import inspect
            pk_val = inspect(v).identity[0]
            processed_lookup[k] = pk_val
        else:
            processed_lookup[k] = v

    caso_id = processed_lookup.get('id_caso')
    exists_in_cache = False
    if model in _RELATED_EXISTS_CACHE:
        exists_in_cache = caso_id in _RELATED_EXISTS_CACHE[model]

    if caso_creado or not exists_in_cache:
        instancia = model(**processed_lookup, **defaults)
        db.add(instancia)
        if model in _RELATED_EXISTS_CACHE:
            _RELATED_EXISTS_CACHE[model].add(caso_id)
        return instancia, True
    else:
        instancia = db.query(model).filter_by(**processed_lookup).first()
        if instancia is not None:
            for campo, valor in defaults.items():
                setattr(instancia, campo, valor)
        else:
            instancia = model(**processed_lookup, **defaults)
            db.add(instancia)
            if model in _RELATED_EXISTS_CACHE:
                _RELATED_EXISTS_CACHE[model].add(caso_id)
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
    val_str = str(value).strip()
    if not ('/' in val_str or '-' in val_str or len(val_str) > 8):
        try:
            n = int(float(value))
            if 1000 < n < 100000:
                return (_EXCEL_SERIAL_ORIGIN + pd.Timedelta(days=n)).date()
        except (ValueError, TypeError):
            pass

    fecha = pd.to_datetime(value, errors='coerce', dayfirst=True)
    if not pd.isna(fecha):
        if fecha.year == 1970 and not ('1970' in val_str or '70' in val_str):
            try:
                n = int(float(value))
                if 1000 < n < 100000:
                    return (_EXCEL_SERIAL_ORIGIN + pd.Timedelta(days=n)).date()
            except (ValueError, TypeError):
                pass
        return fecha.date()
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
