"""Escritura de registros relacionados para casos de morbilidad materna extrema."""

from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    AntecedentesObstetricos,
    CatGrupoCausa,
    CatRegulacionFecundidad,
    CatTerminacionGestacion,
    CausasMorbilidad,
    CriteriosEnfermedad,
    CriteriosFallaOrganica,
    CriteriosManejo,
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
from utils.text_utils import clean_text
from utils.type_parsers import _parse_bool, _parse_decimal, _parse_int


def _escribir_relacionados_morbilidad(
    db: Session,
    row,
    pdata: "_DatosPasada1",
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
    kw = {"caso_creado": caso_creado, "related_cache": related_cache}

    regulacion = _resolve_catalog_optional(
        db,
        CatRegulacionFecundidad,
        _get_value(row, ["Regulación fecundidad", "Regulacion fecundidad"]),
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
        {"id_caso": caso.id_caso},
        {
            "num_gestaciones": _parse_int(_get_value(row, ["N° gestaciones"])),
            "partos_vaginales": _parse_int(_get_value(row, ["Partos vaginales"])),
            "cesareas": _parse_int(_get_value(row, ["Cesáreas"])),
            "abortos": _parse_int(_get_value(row, ["Abortos"])),
            "id_regulacion_fecundidad": regulacion.id if regulacion else None,
            "num_controles_prenatales": _parse_int(_get_value(row, ["N° controles prenatales"])),
            "semanas_inicio_cpn": _parse_int(_get_value(row, ["Semanas inicio CPN"])),
            "id_terminacion_gestacion": terminacion.id if terminacion else None,
            "edad_gestacional_sem": _parse_int(
                _get_value(row, ["Edad gestacional ocurrencia (sem)"])
            ),
            "momento_ocurrencia": _resolve_momento_ocurrencia(
                _get_value(row, ["Momento ocurrencia"])
            ),
            "estado_recien_nacido": _normalize_estado_rn(
                _get_value(row, _MORBILIDAD_ESTADO_RN_COLS)
            ),
            "peso_rn_gramos": _parse_int(_get_value(row, _MORBILIDAD_PESO_RN_COLS)),
        },
        **kw,
    )

    _upsert_single_related(
        db,
        CriteriosEnfermedad,
        {"id_caso": caso.id_caso},
        {
            "eclampsia": _parse_bool(_get_value(row, ["Eclampsia"])),
            "sepsis_sistemica_severa": _parse_bool(_get_value(row, ["Sepsis sistémica severa"])),
            "hemorragia_obstetrica": _parse_bool(_get_value(row, ["Hemorragia obstétrica severa"])),
            "preeclampsia": _parse_bool(_get_value(row, ["Preeclampsia"])),
            "ruptura_uterina": _parse_bool(_get_value(row, ["Ruptura uterina"])),
            "aborto_septico": 0,
            "embarazo_ectopico": 0,
            "autoinmune": 0,
            "hematologica": 0,
            "oncologica": 0,
            "endocrino_metabolicas": 0,
            "renales": 0,
            "gastrointestinales": 0,
            "tromboembolicos": 0,
            "cardiocerebrovasculares": 0,
            "otras_enfermedades": 0,
        },
        **kw,
    )

    _upsert_single_related(
        db,
        CriteriosFallaOrganica,
        {"id_caso": caso.id_caso},
        {
            "falla_cardiaca": 0,
            "falla_vascular": 0,
            "falla_renal": 0,
            "falla_hepatica": 0,
            "falla_metabolica": 0,
            "falla_cerebral": 0,
            "falla_respiratoria": 0,
            "falla_coagulacion": 0,
        },
        **kw,
    )

    _upsert_single_related(
        db,
        CriteriosManejo,
        {"id_caso": caso.id_caso},
        {
            "ingreso_uci": _parse_bool(_get_value(row, ["Ingreso UCI"])),
            "cirugia_adicional": _parse_bool(_get_value(row, ["Cirugía adicional"])),
            "transfusion": _parse_bool(_get_value(row, ["Transfusión"])),
            "total_criterios": _parse_int(_get_value(row, ["Total criterios"])),
            "accidente": 0,
            "intoxicacion_accidental": 0,
            "intento_suicida": 0,
            "victima_violencia": 0,
            "otros_eventos_sp": 0,
            "cual_evento_sp": None,
        },
        **kw,
    )

    _upsert_single_related(
        db,
        ManejoHospitalario,
        {"id_caso": caso.id_caso},
        {
            "dias_estancia_hosp": _parse_int(_get_value(row, ["Días estancia hospitalaria"])),
            "dias_estancia_uci": _parse_int(_get_value(row, ["Días estancia UCI"])),
            "unidades_transfundidas": _parse_int(_get_value(row, _MORBILIDAD_TRANSFUNDIDAS_COLS)),
            "cirugia_1": None,
            "cirugia_1_cual": None,
            "cirugia_2": None,
            "cirugia_2_cual": None,
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
        {"id_caso": caso.id_caso},
        {
            "causa_principal_cie10": pdata.causa,
            "id_grupo_causa": grupo_causa.id if grupo_causa else None,
            "causa_asociada_2": None,
            "causa_asociada_3": None,
            "causa_asociada_4": None,
        },
        **kw,
    )

    tiene_remitida = _has_any_value(row, ["Remitida"])
    remitida = _parse_bool(_get_value(row, ["Remitida"])) if tiene_remitida else 0
    _upsert_single_related(
        db,
        Referencia,
        {"id_caso": caso.id_caso},
        {
            "remitida": remitida,
            "institucion_ref_1": clean_text(_get_value(row, _MORBILIDAD_INSTITUCION_REF_1_COLS)),
            "institucion_ref_2": clean_text(_get_value(row, _MORBILIDAD_INSTITUCION_REF_2_COLS)),
            "tiempo_remision_h": _parse_decimal(_get_value(row, _MORBILIDAD_TIEMPO_REMISION_COLS)),
        },
        **kw,
    )
