"""Escritura de registros relacionados para casos de mortalidad materna."""

from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    AntecedenteMaterno,
    AntecedentePartoPuerperio,
    AntecedenteRiesgo,
    CatConvivencia,
    CatEscolaridad,
    CatEtnia,
    CatFuenteCausaMuerte,
    CatMomentoMuerte,
    CatNivelAtencion,
    CatPersonalSalud,
    CatPoblacionVulnerable,
    CatRegulacionFecundidad,
    CatRemisiones,
    CatTipoAfiliacion,
    CatTipoParto,
    CatZonaResidencia,
    CausaMuerte,
    ComplicacionEmbarazo,
    ControlPrenatal,
    DatosSociodemograficos,
)
from services._sivigila_catalog import _resolve_catalog_optional
from services._sivigila_escritura import (
    _MORTALIDAD_ATENDIDO_POR_COLS,
    _MORTALIDAD_COMPLICACIONES_FETO_COLS,
    _MORTALIDAD_FECHA_PARTO_COLS,
    _MORTALIDAD_FUENTE_CAUSA_COLS,
    _MORTALIDAD_HORA_PARTO_COLS,
    _MORTALIDAD_MOMENTO_MUERTE_COLS,
    _MORTALIDAD_NIVEL_CPN_COLS,
    _MORTALIDAD_NIVEL_PARTO_COLS,
    _MORTALIDAD_PERSONAL_CPN_COLS,
    _MORTALIDAD_REMISIONES_COLS,
    _get_value,
    _upsert_single_related,
)
from services._sivigila_helpers import _DatosPasada1
from utils.date_parsers import _parse_date, _parse_time
from utils.text_utils import clean_text
from utils.type_parsers import _parse_bool, _parse_int


def _escribir_relacionados_mortalidad(
    db: Session,
    row,
    pdata: '_DatosPasada1',
    caso,
    caso_creado: bool,
    related_cache: dict,
    catalog_cache: dict,
):
    """Persiste todos los registros relacionados de un caso de mortalidad.

    Args:
        db: Sesión de base de datos.
        row: Fila del DataFrame.
        pdata: Datos validados de pasada 1 para esta fila.
        caso: Instancia de CasoMortalidad.
        caso_creado: True si el caso fue recién creado.
        related_cache: Cache de IDs existentes por modelo.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.
    """
    kw = {'caso_creado': caso_creado, 'related_cache': related_cache}

    convivencia = _resolve_catalog_optional(
        db,
        CatConvivencia,
        _get_value(row, ['6.1 Convivencia']),
        catalog_cache=catalog_cache,
    )
    escolaridad = _resolve_catalog_optional(
        db,
        CatEscolaridad,
        _get_value(row, ['6.3 Escolaridad']),
        catalog_cache=catalog_cache,
    )
    regulacion = _resolve_catalog_optional(
        db,
        CatRegulacionFecundidad,
        _get_value(row, ['6.4 Regulación Fecundidad', '6.4 Regulacion Fecundidad']),
        catalog_cache=catalog_cache,
    )
    _upsert_single_related(
        db,
        AntecedenteMaterno,
        {'id_caso': caso.id_caso},
        {
            'id_convivencia': convivencia.id if convivencia else None,
            'otro_convivencia': clean_text(
                _get_value(
                    row,
                    ['6.2 Si otro convivencia', '6.2 Si marcó otro ¿Cuál?', 'Si otro convivencia'],
                )
            ),
            'id_escolaridad': escolaridad.id if escolaridad else None,
            'id_regulacion_fec': regulacion.id if regulacion else None,
            'gestaciones': _parse_int(_get_value(row, ['6.5 Gestaciones'])),
            'partos_vaginales': _parse_int(_get_value(row, ['6.6 Partos Vaginales'])),
            'cesareas': _parse_int(_get_value(row, ['6.7 Cesáreas'])),
            'nacidos_muertos': _parse_int(_get_value(row, ['6.8 Muertos'])),
            'hijos_vivos': _parse_int(_get_value(row, ['6.9 Vivos'])),
            'abortos': _parse_int(_get_value(row, ['6.10 Abortos'])),
        },
        **kw,
    )

    mapa_riesgos = {
        'sin_antecedentes': ['7.1.1 Ninguno', '7.1 Ninguno', 'Ninguno'],
        'hipertension_cronica': [
            '7.1.2 Hipertensión crónica',
            '7.1 Hipertensión crónica',
            'Hipertensión crónica',
            'Hipertension cronica',
        ],
        'cardiopatias': ['7.1.3 Cardiopatías', '7.1 Cardiopatías', 'Cardiopatías', 'Cardiopatias'],
        'diabetes': ['7.1.4 Diabetes', '7.1 Diabetes', 'Diabetes'],
        'mola_hidatiforme': ['7.1.5 Mola hidatiforme', '7.1 Mola hidatiforme', 'Mola hidatiforme'],
        'rn_pretermino': [
            '7.1.6 RN pretérmino',
            '7.1 RN pretérmino',
            'RN pretérmino',
            'RN pretermino',
        ],
        'rn_bajo_peso': [
            '7.1.7 RN bajo peso',
            '7.1 RN de bajo peso',
            'RN de bajo peso',
            'RN bajo peso',
        ],
        'rn_macrosomico': [
            '7.1.8 RN macrosómicos',
            '7.1 RN macrosómicos',
            'RN macrosómicos',
            'RN macrosomicos',
        ],
        'trastorno_mental': ['7.1.9 Trastorno mental', '7.1 Trastorno mental', 'Trastorno mental'],
        'obesidad': ['7.1.10 Obesidad', '7.1 Obesidad', 'Obesidad'],
        'desnutricion_cronica': [
            '7.1.11 Desnutrición crónica',
            '7.1 Desnutrición crónica',
            'Desnutrición crónica',
            'Desnutricion cronica',
        ],
        'intergenesis_menor_2a': [
            '7.1.12 Intergénesis <2a',
            '7.1 Intergénesis menor a dos años',
            'Intergénesis menor a dos años',
            'Intergenesis menor a dos años',
        ],
        'its_distintas': [
            '7.1.13 ITS distintas VIH/síf/HB',
            '7.1 ITS distintas a VIH, sífilis y HB',
            'ITS distintas a VIH, sífilis y HB',
            'ITS distintas',
        ],
        'vih_sida': ['7.1.14 VIH-SIDA', '7.1 VIH - SIDA', 'VIH - SIDA', 'VIH SIDA', 'VIH'],
        'otras_infecciones': [
            '7.1.15 Otras infecciones',
            '7.1 Otras infecciones',
            'Otras infecciones',
        ],
        'rh_negativo': ['7.1.16 RH negativo', '7.1 RH negativo', 'RH negativo'],
        'tabaquismo': ['7.1.17 Tabaquismo', '7.1 Tabaquismo', 'Tabaquismo'],
        'alcoholismo': ['7.1.18 Alcoholismo', '7.1 Alcoholismo', 'Alcoholismo'],
        'sustancias_psicoactivas': [
            '7.1.19 Sust.psicoactivas',
            '7.1 Sustancias psicoactivas',
            'Sustancias psicoactivas',
        ],
        'deficiencias_socioeconomicas': [
            '7.1.20 Def.socioeconómicas',
            '7.1 Deficiencias socioeconómicas',
            'Deficiencias socioeconómicas',
            'Deficiencias socioeconomicas',
        ],
        'sifilis': ['7.1.21 Sífilis', '7.1 Sífilis', 'Sífilis', 'Sifilis'],
        'hepatitis_b': ['7.1.22 Hepatitis B', '7.1 Hepatitis B', 'Hepatitis B'],
        'otros_factores_riesgo': [
            '7.1.23 Otros factores riesgo',
            '7.1 Otros factores de riesgo',
            'Otros factores de riesgo',
        ],
        'gingivitis_periodontitis': [
            '7.1.24 Gingivitis/periodontitis',
            '7.1 Gingivitis y/o periodontitis',
            'Gingivitis y/o periodontitis',
            'Gingivitis y periodontitis',
        ],
    }

    riesgos_data = {}
    for campo, columnas in mapa_riesgos.items():
        riesgos_data[campo] = _parse_bool(_get_value(row, columnas))

    if riesgos_data.get('sin_antecedentes') == 1:
        for k in riesgos_data:
            if k != 'sin_antecedentes':
                riesgos_data[k] = 0

    riesgos_data['desc_otros_factores'] = _get_value(
        row,
        [
            '7.1.23 Cuáles otros factores',
            '7.1.1 Si marcó otros factores (7.1 - 23) ¿Cuáles?',
            '7.1 Cuál otro',
            'Cuál otro',
            'Cuál otro factor de riesgo',
        ],
    )

    _upsert_single_related(
        db,
        AntecedenteRiesgo,
        {'id_caso': caso.id_caso},
        riesgos_data,
        **kw,
    )

    mapa_complicaciones = {
        'preeclampsia': ['7.2.1 Preeclampsia', '7.2 Preeclampsia', 'Preeclampsia'],
        'eclampsia': ['7.2.2 Eclampsia', '7.2 Eclampsia', 'Eclampsia'],
        'sindrome_hellp': [
            '7.2.3 Síndrome HELLP',
            '7.2 Síndrome HELLP',
            '7.2 Síndrome de Hellp',
            'Síndrome HELLP',
            'Síndrome de Hellp',
            'Sindrome de Hellp',
            'Sindrome Hellp',
        ],
        'diabetes_gestacional': [
            '7.2.4 Diabetes gestacional',
            '7.2 Diabetes gestacional',
            'Diabetes gestacional',
        ],
        'sepsis': ['7.2.5 Sepsis', '7.2 Sepsis', 'Sepsis'],
        'hemorragia_1er_trimestre': [
            '7.2.6 Hemorragia 1er trim',
            '7.2 Hemorragia 1er trimestre',
            'Hemorragia 1er trimestre',
        ],
        'hemorragia_2do_trimestre': [
            '7.2.7 Hemorragia 2do trim',
            '7.2 Hemorragia 2do trimestre',
            'Hemorragia 2do trimestre',
        ],
        'hemorragia_3er_trimestre': [
            '7.2.8 Hemorragia 3er trim',
            '7.2 Hemorragia 3er trimestre',
            'Hemorragia 3er trimestre',
        ],
        'desproporcion_cefalo_pelv': [
            '7.2.9 Desproporción céfalo-pélvica',
            '7.2 Desproporción céfalo pélvica',
            '7.2 Desproporción céfalo-pélvica',
            'Desproporción céfalo pélvica',
            'Desproporción céfalo-pélvica',
            'Desproporcion cefalo pelvica',
        ],
        'retardo_crecimiento_iu': [
            '7.2.10 Retardo crec.intrauterino',
            '7.2 Retardo crecimiento intrauterino',
            'Retardo crecimiento intrauterino',
        ],
        'enfermedad_autoinmune': [
            '7.2.11 Enf.autoinmune',
            '7.2 Enfermedad autoinmune',
            'Enfermedad autoinmune',
        ],
        'malaria': ['7.2.12 Malaria', '7.2 Malaria', 'Malaria'],
        'embarazo_no_deseado': [
            '7.2.13 Embarazo no deseado',
            '7.2 Embarazo no deseado',
            'Embarazo no deseado',
        ],
        'violencia_gestante': [
            '7.2.14 Violencia contra gestante',
            '7.2 Violencia contra la gestante',
            'Violencia contra la gestante',
            'Violencia gestante',
        ],
        'otras_complicaciones': [
            '7.2.15 Otras complicaciones',
            '7.2 Otras complicaciones',
            'Otras complicaciones',
        ],
        'gestacion_violencia_sexual': [
            '7.2.16 Gest.violencia sexual',
            '7.2 Gestación producto de violencia sexual',
            'Gestación producto de violencia sexual',
            'Gestacion violencia sexual',
        ],
        'feto_incompatible_vida': [
            '7.2.17 Feto incompatible con vida',
            '7.2 Feto incompatible con la vida',
            'Feto incompatible con la vida',
            'Feto incompatible vida',
        ],
        'sintomas_depresivos': [
            '7.2.18 Síntomas depresivos',
            '7.2 Síntomas depresivos',
            'Síntomas depresivos',
            'Sintomas depresivos',
        ],
    }

    complicaciones_data = {}
    for campo, columnas in mapa_complicaciones.items():
        complicaciones_data[campo] = _parse_bool(_get_value(row, columnas))

    complicaciones_data['desc_otras_complicaciones'] = _get_value(
        row,
        [
            '7.2.15 Cuáles otras complicaciones',
            '7.2.1 Si marcó otras complicaciones (7.2 - 15) ¿Cuáles?',
            '7.2.1 Si marcó otros factores (7.1.15), mencione cuáles',
            '7.2 Cuál otra complicación',
            'Cuál otra complicación',
            'Cuál otra',
        ],
    )

    _upsert_single_related(
        db,
        ComplicacionEmbarazo,
        {'id_caso': caso.id_caso},
        complicaciones_data,
        **kw,
    )

    remisiones = _resolve_catalog_optional(
        db,
        CatRemisiones,
        _get_value(row, _MORTALIDAD_REMISIONES_COLS),
        catalog_cache=catalog_cache,
    )
    if remisiones is None:
        remisiones = (
            db.query(CatRemisiones).filter(CatRemisiones.id == 3).first()
            or db.query(CatRemisiones).order_by(CatRemisiones.id).first()
        )

    personal_cpn = _resolve_catalog_optional(
        db,
        CatPersonalSalud,
        _get_value(row, _MORTALIDAD_PERSONAL_CPN_COLS),
        catalog_cache=catalog_cache,
    )
    nivel_cpn = _resolve_catalog_optional(
        db,
        CatNivelAtencion,
        _get_value(row, _MORTALIDAD_NIVEL_CPN_COLS),
        catalog_cache=catalog_cache,
        extra_field='nivel',
    )

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
            'compl_feto_rn_cie10': clean_text(
                _get_value(row, _MORTALIDAD_COMPLICACIONES_FETO_COLS)
            ),
        },
        **kw,
    )

    momento_muerte = _resolve_catalog_optional(
        db,
        CatMomentoMuerte,
        _get_value(row, _MORTALIDAD_MOMENTO_MUERTE_COLS),
        catalog_cache=catalog_cache,
    )
    tipo_parto = _resolve_catalog_optional(
        db,
        CatTipoParto,
        _get_value(row, ['9.4 Tipo de parto']),
        catalog_cache=catalog_cache,
    )
    atendido_por = _resolve_catalog_optional(
        db,
        CatPersonalSalud,
        _get_value(row, _MORTALIDAD_ATENDIDO_POR_COLS),
        catalog_cache=catalog_cache,
    )
    nivel_parto = _resolve_catalog_optional(
        db,
        CatNivelAtencion,
        _get_value(row, _MORTALIDAD_NIVEL_PARTO_COLS),
        catalog_cache=catalog_cache,
        extra_field='nivel',
    )

    fecha_parto_val = _parse_date(_get_value(row, _MORTALIDAD_FECHA_PARTO_COLS))
    hora_parto_val = _parse_time(_get_value(row, _MORTALIDAD_HORA_PARTO_COLS))
    tipo_parto_val = tipo_parto.id if tipo_parto else None
    atendido_por_val = atendido_por.id if atendido_por else None
    nivel_parto_val = nivel_parto.id if nivel_parto else None
    otro_atencion_parto_val = clean_text(
        _get_value(
            row,
            [
                '9.5.1 Otro ¿quién?',
                'Otro ¿quién?',
                '9.5 Otro, Cuál?',
                '9.5 Otro, ¿Cuál?',
                '9.5 Otro',
                'Otro, Cuál?',
                'Otro, Cuál',
                'Otro atendido por',
            ],
        )
    )

    # Regla de negocio: Si 9.5 NO es 7=Otro, se borra cualquier texto en 9.5.1
    if atendido_por_val != 7:
        otro_atencion_parto_val = None

    # Regla de negocio: Si 9.1 Momento de muerte es Gestación (1), se inactivan los datos del parto
    if momento_muerte and momento_muerte.id == 1:
        fecha_parto_val = None
        hora_parto_val = None
        tipo_parto_val = None
        atendido_por_val = None
        nivel_parto_val = None
        otro_atencion_parto_val = None

    _upsert_single_related(
        db,
        AntecedentePartoPuerperio,
        {'id_caso': caso.id_caso},
        {
            'id_momento_muerte': momento_muerte.id if momento_muerte else None,
            'semana_gestacion_muerte': _parse_int(_get_value(row, ['9.2 Semana gestación'])),
            'fecha_parto': fecha_parto_val,
            'hora_parto': hora_parto_val,
            'id_tipo_parto': tipo_parto_val,
            'id_atendido_por': atendido_por_val,
            'otro_atencion_parto': otro_atencion_parto_val,
            'id_nivel_atencion_parto': nivel_parto_val,
        },
        **kw,
    )

    fuente_causa = _resolve_catalog_optional(
        db,
        CatFuenteCausaMuerte,
        _get_value(row, _MORTALIDAD_FUENTE_CAUSA_COLS),
        catalog_cache=catalog_cache,
    )
    if fuente_causa is None:
        fuente_causa = (
            db.query(CatFuenteCausaMuerte).filter(CatFuenteCausaMuerte.id == 1).first()
            or db.query(CatFuenteCausaMuerte).order_by(CatFuenteCausaMuerte.id).first()
        )

    _upsert_single_related(
        db,
        CausaMuerte,
        {'id_caso': caso.id_caso},
        {
            'causa_basica_cie10': pdata.causa,
            'id_fuente_causa': fuente_causa.id if fuente_causa else None,
            'demora_1': _parse_bool(_get_value(row, ['10.3.1 Demora 1'])),
            'demora_2': _parse_bool(_get_value(row, ['10.3.2 Demora 2'])),
            'demora_3': _parse_bool(_get_value(row, ['10.3.3 Demora 3'])),
            'demora_4': _parse_bool(_get_value(row, ['10.3.4 Demora 4'])),
        },
        **kw,
    )

    zona = _resolve_catalog_optional(
        db,
        CatZonaResidencia,
        _get_value(row, ['Zona de residencia', 'Zona residencia', 'Zona']),
        catalog_cache=catalog_cache,
    )
    pob_vuln = _resolve_catalog_optional(
        db,
        CatPoblacionVulnerable,
        _get_value(row, ['Población vulnerable', 'Poblacion vulnerable', 'Población vulnerable']),
        catalog_cache=catalog_cache,
    )
    etnia = _resolve_catalog_optional(
        db,
        CatEtnia,
        _get_value(row, ['Etnia', 'Grupo étnico', 'Grupo etnico']),
        catalog_cache=catalog_cache,
    )
    tipo_afiliacion = _resolve_catalog_optional(
        db,
        CatTipoAfiliacion,
        _get_value(
            row,
            [
                'Tipo de afiliación',
                'Tipo afiliación',
                'Tipo afiliacion',
                'Afiliación',
                'Afiliacion',
                'Régimen de afiliación',
                'Regimen de afiliacion',
            ],
        ),
        catalog_cache=catalog_cache,
    )

    ds = (
        db.query(DatosSociodemograficos)
        .filter(DatosSociodemograficos.caso_mortalidad_id == caso.id_caso)
        .first()
    )
    if ds is None:
        ds = DatosSociodemograficos(
            caso_mortalidad_id=caso.id_caso,
            id_zona_residencia=zona.id if zona else None,
            id_poblacion_vulnerable=pob_vuln.id if pob_vuln else None,
            id_etnia=etnia.id if etnia else None,
            id_tipo_afiliacion=tipo_afiliacion.id if tipo_afiliacion else None,
        )
        db.add(ds)
    else:
        ds.id_zona_residencia = zona.id if zona else None
        ds.id_poblacion_vulnerable = pob_vuln.id if pob_vuln else None
        ds.id_etnia = etnia.id if etnia else None
        ds.id_tipo_afiliacion = tipo_afiliacion.id if tipo_afiliacion else None
