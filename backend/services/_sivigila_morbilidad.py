"""Escritura de registros relacionados para casos de morbilidad materna extrema."""

from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    AntecedentesObstetricos,
    CatEtnia,
    CatGrupoCausa,
    CatPoblacionVulnerable,
    CatRegulacionFecundidad,
    CatTerminacionGestacion,
    CatTipoAfiliacion,
    CatZonaResidencia,
    CausasMorbilidad,
    CriteriosEnfermedad,
    CriteriosFallaOrganica,
    CriteriosManejo,
    DatosSociodemograficos,
    ManejoHospitalario,
    Referencia,
)
from services._sivigila_catalog import _resolve_catalog_optional
from services._sivigila_escritura import (
    _MORBILIDAD_ESTADO_RN_COLS,
    _MORBILIDAD_GRUPO_CAUSA_COLS,
    _MORBILIDAD_INSTITUCION_REF_1_COLS,
    _MORBILIDAD_INSTITUCION_REF_2_COLS,
    _MORBILIDAD_PESO_RN_COLS,
    _MORBILIDAD_TERMINACION_COLS,
    _MORBILIDAD_TIEMPO_REMISION_COLS,
    _MORBILIDAD_TRANSFUNDIDAS_COLS,
    _get_value,
    _has_any_value,
    _normalize_estado_rn,
    _resolve_momento_ocurrencia,
    _upsert_single_related,
)
from services._sivigila_helpers import _DatosPasada1
from utils.date_parsers import _parse_date
from utils.text_utils import clean_text, is_empty, slugify
from utils.type_parsers import _parse_bool, _parse_decimal, _parse_int

_CIRUGIA_CODIGOS = {
    '1': 1,
    'histerectomia': 1,
    '2': 2,
    'laparotomia': 2,
    '3': 3,
    'legrado': 3,
    '4': 4,
    'otra': 4,
}


def _parse_cirugia_codigo(value) -> int | None:
    """Traduce el texto/código de una cirugía adicional a su código 1-4.

    Args:
        value: Valor crudo de la celda ('Histerectomía', '1', 1.0, etc.).

    Returns:
        Código 1-4 según la ficha 549, o None si está vacío/no reconocido.
    """
    if is_empty(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _CIRUGIA_CODIGOS.get(str(int(value)))
    return _CIRUGIA_CODIGOS.get(slugify(value))


def _parse_multiplicidad(value) -> int | None:
    """Traduce 'Único'/'Múltiple' (o 1/2) al código de multiplicidad.

    Args:
        value: Valor crudo de la celda.

    Returns:
        1 si es múltiple, 0 si es único, None si está vacío/no reconocido.
    """
    if is_empty(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        codigo = int(value)
    else:
        slug = slugify(value)
        if slug in {'2', 'multiple'}:
            return 1
        if slug in {'1', 'unico'}:
            return 0
        return None
    if codigo == 2:
        return 1
    if codigo == 1:
        return 0
    return None


def _escribir_relacionados_morbilidad(
    db: Session,
    row,
    pdata: '_DatosPasada1',
    caso,
    caso_creado: bool,
    related_cache: dict,
    catalog_cache: dict,
):
    """Persiste todos los registros relacionados de un caso de morbilidad.

    Args:
        db: Sesión de base de datos.
        row: Fila del DataFrame.
        pdata: Datos validados de pasada 1 para esta fila.
        caso: Instancia de CasoMorbilidad.
        caso_creado: True si el caso fue recién creado.
        related_cache: Cache de IDs existentes por modelo.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.
    """
    kw = {'caso_creado': caso_creado, 'related_cache': related_cache}

    regulacion = _resolve_catalog_optional(
        db,
        CatRegulacionFecundidad,
        _get_value(row, ['Regulación fecundidad', 'Regulacion fecundidad']),
        catalog_cache=catalog_cache,
    )
    terminacion = _resolve_catalog_optional(
        db,
        CatTerminacionGestacion,
        _get_value(row, _MORBILIDAD_TERMINACION_COLS),
        catalog_cache=catalog_cache,
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
            'molas': _parse_int(_get_value(row, ['Molas'])),
            'ectopicos': _parse_int(_get_value(row, ['Ectópicos'])),
            'muertos': _parse_int(_get_value(row, ['Muertos'])),
            'vivos': _parse_int(_get_value(row, ['Vivos'])),
            'fecha_ultima_gestacion': _parse_date(
                _get_value(
                    row,
                    [
                        'Fecha última gestación (dd/mm/aaaa)',
                        'Fecha última gestación',
                        'Fecha ultima gestacion',
                    ],
                )
            ),
            'id_regulacion_fecundidad': regulacion.id if regulacion else None,
            'num_controles_prenatales': _parse_int(_get_value(row, ['N° controles prenatales'])),
            'semanas_inicio_cpn': _parse_int(_get_value(row, ['Semanas inicio CPN'])),
            'id_terminacion_gestacion': terminacion.id if terminacion else None,
            'edad_gestacional_sem': _parse_int(
                _get_value(row, ['Edad gestacional ocurrencia (sem)'])
            ),
            'momento_ocurrencia': _resolve_momento_ocurrencia(
                _get_value(row, ['Momento ocurrencia'])
            ),
            'estado_recien_nacido': _normalize_estado_rn(
                _get_value(row, _MORBILIDAD_ESTADO_RN_COLS)
            ),
            'peso_rn_gramos': _parse_int(_get_value(row, _MORBILIDAD_PESO_RN_COLS)),
            'multiplicidad': _parse_multiplicidad(_get_value(row, ['Multiplicidad'])),
        },
        **kw,
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
            'aborto_septico': _parse_bool(_get_value(row, ['Aborto séptico'])),
            'embarazo_ectopico': _parse_bool(_get_value(row, ['Embarazo ectópico'])),
            'autoinmune': _parse_bool(_get_value(row, ['7.1.8 Autoinmune', 'Autoinmune'])),
            'hematologica': _parse_bool(_get_value(row, ['Hematológica'])),
            'oncologica': _parse_bool(_get_value(row, ['Oncológica'])),
            'endocrino_metabolicas': _parse_bool(_get_value(row, ['Endocrino/metabólicas'])),
            'renales': _parse_bool(_get_value(row, ['Renales'])),
            'gastrointestinales': _parse_bool(_get_value(row, ['Gastrointestinales'])),
            'tromboembolicos': _parse_bool(_get_value(row, ['Eventos tromboembólicos'])),
            'cardiocerebrovasculares': _parse_bool(_get_value(row, ['Cardiocerebrovasculares'])),
            'otras_enfermedades': _parse_bool(_get_value(row, ['Otras'])),
        },
        **kw,
    )

    _upsert_single_related(
        db,
        CriteriosFallaOrganica,
        {'id_caso': caso.id_caso},
        {
            'falla_cardiaca': _parse_bool(_get_value(row, ['Falla cardíaca'])),
            'falla_vascular': _parse_bool(_get_value(row, ['Falla vascular'])),
            'falla_renal': _parse_bool(_get_value(row, ['Falla renal'])),
            'falla_hepatica': _parse_bool(_get_value(row, ['Falla hepática'])),
            'falla_metabolica': _parse_bool(_get_value(row, ['Falla metabólica'])),
            'falla_cerebral': _parse_bool(_get_value(row, ['Falla cerebral'])),
            'falla_respiratoria': _parse_bool(_get_value(row, ['Falla respiratoria'])),
            'falla_coagulacion': _parse_bool(_get_value(row, ['Falla coagulación'])),
        },
        **kw,
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
            'accidente': _parse_bool(_get_value(row, ['Accidente'])),
            'intoxicacion_accidental': _parse_bool(_get_value(row, ['Intoxicación accidental'])),
            'intento_suicida': _parse_bool(_get_value(row, ['Intento suicida'])),
            'victima_violencia': _parse_bool(_get_value(row, ['Víctima de violencia'])),
            'otros_eventos_sp': _parse_bool(_get_value(row, ['Otros eventos salud pública'])),
            'cual_evento_sp': clean_text(_get_value(row, ['¿Cuál evento?'])),
        },
        **kw,
    )

    _upsert_single_related(
        db,
        ManejoHospitalario,
        {'id_caso': caso.id_caso},
        {
            'dias_estancia_hosp': _parse_int(_get_value(row, ['Días estancia hospitalaria'])),
            'dias_estancia_uci': _parse_int(_get_value(row, ['Días estancia UCI'])),
            'unidades_transfundidas': _parse_int(_get_value(row, _MORBILIDAD_TRANSFUNDIDAS_COLS)),
            'cirugia_1': _parse_cirugia_codigo(_get_value(row, ['Cirugía adicional 1'])),
            'cirugia_1_cual': clean_text(_get_value(row, ['¿Cuál otra cirugía 1?'])),
            'cirugia_2': _parse_cirugia_codigo(_get_value(row, ['Cirugía adicional 2'])),
            'cirugia_2_cual': clean_text(_get_value(row, ['¿Cuál otra cirugía 2?'])),
        },
        **kw,
    )

    grupo_causa = _resolve_catalog_optional(
        db,
        CatGrupoCausa,
        _get_value(row, _MORBILIDAD_GRUPO_CAUSA_COLS),
        catalog_cache=catalog_cache,
    )
    _upsert_single_related(
        db,
        CausasMorbilidad,
        {'id_caso': caso.id_caso},
        {
            'causa_principal_cie10': pdata.causa,
            'id_grupo_causa': grupo_causa.id if grupo_causa else None,
            'causa_asociada_2': clean_text(_get_value(row, ['Causa asociada CIE-10'])),
            'causa_asociada_3': clean_text(_get_value(row, ['Causa asociada CIE-10.1'])),
            'causa_asociada_4': clean_text(_get_value(row, ['Causa asociada CIE-10.2'])),
        },
        **kw,
    )

    tiene_remitida = _has_any_value(row, ['Remitida'])
    remitida = _parse_bool(_get_value(row, ['Remitida'])) if tiene_remitida else 0
    _upsert_single_related(
        db,
        Referencia,
        {'id_caso': caso.id_caso},
        {
            'remitida': remitida,
            'institucion_ref_1': clean_text(_get_value(row, _MORBILIDAD_INSTITUCION_REF_1_COLS)),
            'institucion_ref_2': clean_text(_get_value(row, _MORBILIDAD_INSTITUCION_REF_2_COLS)),
            'tiempo_remision_h': _parse_decimal(_get_value(row, _MORBILIDAD_TIEMPO_REMISION_COLS)),
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
        _get_value(row, ['Población vulnerable', 'Poblacion vulnerable']),
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
            ],
        ),
        catalog_cache=catalog_cache,
    )

    ds = (
        db.query(DatosSociodemograficos)
        .filter(DatosSociodemograficos.caso_morbilidad_id == caso.id_caso)
        .first()
    )
    if ds is None:
        ds = DatosSociodemograficos(
            caso_morbilidad_id=caso.id_caso,
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
