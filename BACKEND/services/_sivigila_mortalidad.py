"""Escritura de registros relacionados para casos de mortalidad materna."""

from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    AntecedenteMaterno,
    AntecedentePartoPuerperio,
    AntecedenteRiesgo,
    CatConvivencia,
    CatEscolaridad,
    CatFuenteCausaMuerte,
    CatMomentoMuerte,
    CatNivelAtencion,
    CatPersonalSalud,
    CatRegulacionFecundidad,
    CatRemisiones,
    CatTipoParto,
    CausaMuerte,
    ComplicacionEmbarazo,
    ControlPrenatal,
)
from services._sivigila_catalog import _resolve_catalog_optional
from services._sivigila_escritura import (
    _MORTALIDAD_ATENDIDO_POR_COLS,
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
from utils.type_parsers import _parse_bool, _parse_int

_CAMPOS_ANTECEDENTE_RIESGO = [
    "sin_antecedentes",
    "hipertension_cronica",
    "cardiopatias",
    "diabetes",
    "mola_hidatiforme",
    "rn_pretermino",
    "rn_bajo_peso",
    "rn_macrosomico",
    "trastorno_mental",
    "obesidad",
    "desnutricion_cronica",
    "intergenesis_menor_2a",
    "its_distintas",
    "vih_sida",
    "otras_infecciones",
    "rh_negativo",
    "tabaquismo",
    "alcoholismo",
    "sustancias_psicoactivas",
    "deficiencias_socioeconomicas",
    "sifilis",
    "hepatitis_b",
    "otros_factores_riesgo",
    "gingivitis_periodontitis",
]

_CAMPOS_COMPLICACION_EMBARAZO = [
    "preeclampsia",
    "eclampsia",
    "sindrome_hellp",
    "diabetes_gestacional",
    "sepsis",
    "hemorragia_1er_trimestre",
    "hemorragia_2do_trimestre",
    "hemorragia_3er_trimestre",
    "desproporcion_cefalo_pelv",
    "retardo_crecimiento_iu",
    "enfermedad_autoinmune",
    "malaria",
    "embarazo_no_deseado",
    "violencia_gestante",
    "otras_complicaciones",
    "gestacion_violencia_sexual",
    "feto_incompatible_vida",
    "sintomas_depresivos",
]


def _escribir_relacionados_mortalidad(
    db: Session,
    row,
    pdata: "_DatosPasada1",
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
    kw = {"caso_creado": caso_creado, "related_cache": related_cache}

    convivencia = _resolve_catalog_optional(
        db,
        CatConvivencia,
        _get_value(row, ["6.1 Convivencia"]),
        catalog_cache=catalog_cache,
    )
    escolaridad = _resolve_catalog_optional(
        db,
        CatEscolaridad,
        _get_value(row, ["6.3 Escolaridad"]),
        catalog_cache=catalog_cache,
    )
    regulacion = _resolve_catalog_optional(
        db,
        CatRegulacionFecundidad,
        _get_value(row, ["6.4 Regulación Fecundidad", "6.4 Regulacion Fecundidad"]),
        catalog_cache=catalog_cache,
    )
    _upsert_single_related(
        db,
        AntecedenteMaterno,
        {"id_caso": caso.id_caso},
        {
            "id_convivencia": convivencia.id if convivencia else None,
            "otro_convivencia": None,
            "id_escolaridad": escolaridad.id if escolaridad else None,
            "id_regulacion_fec": regulacion.id if regulacion else None,
            "gestaciones": _parse_int(_get_value(row, ["6.5 Gestaciones"])),
            "partos_vaginales": _parse_int(_get_value(row, ["6.6 Partos Vaginales"])),
            "cesareas": _parse_int(_get_value(row, ["6.7 Cesáreas"])),
            "nacidos_muertos": _parse_int(_get_value(row, ["6.8 Muertos"])),
            "hijos_vivos": _parse_int(_get_value(row, ["6.9 Vivos"])),
            "abortos": _parse_int(_get_value(row, ["6.10 Abortos"])),
        },
        **kw,
    )

    _upsert_single_related(
        db,
        AntecedenteRiesgo,
        {"id_caso": caso.id_caso},
        {k: 0 for k in _CAMPOS_ANTECEDENTE_RIESGO} | {"desc_otros_factores": None},
        **kw,
    )

    _upsert_single_related(
        db,
        ComplicacionEmbarazo,
        {"id_caso": caso.id_caso},
        {k: 0 for k in _CAMPOS_COMPLICACION_EMBARAZO} | {"desc_otras_complicaciones": None},
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
        extra_field="nivel",
    )
    _upsert_single_related(
        db,
        ControlPrenatal,
        {"id_caso": caso.id_caso},
        {
            "num_cpn": _parse_int(_get_value(row, ["8.1 No. CPN"])),
            "semana_inicio_cpn": _parse_int(_get_value(row, ["8.2 Semana inicio CPN"])),
            "id_personal_cpn": personal_cpn.id if personal_cpn else None,
            "id_nivel_atencion_cpn": nivel_cpn.id if nivel_cpn else None,
            "id_remisiones": remisiones.id if remisiones else None,
            "compl_feto_rn_cie10": None,
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
        _get_value(row, ["9.4 Tipo de parto"]),
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
        extra_field="nivel",
    )
    _upsert_single_related(
        db,
        AntecedentePartoPuerperio,
        {"id_caso": caso.id_caso},
        {
            "id_momento_muerte": momento_muerte.id if momento_muerte else None,
            "semana_gestacion_muerte": _parse_int(_get_value(row, ["9.2 Semana gestación"])),
            "fecha_parto": _parse_date(_get_value(row, _MORTALIDAD_FECHA_PARTO_COLS)),
            "hora_parto": _parse_time(_get_value(row, _MORTALIDAD_HORA_PARTO_COLS)),
            "id_tipo_parto": tipo_parto.id if tipo_parto else None,
            "id_atendido_por": atendido_por.id if atendido_por else None,
            "otro_atencion_parto": None,
            "id_nivel_atencion_parto": nivel_parto.id if nivel_parto else None,
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
        {"id_caso": caso.id_caso},
        {
            "causa_basica_cie10": pdata.causa,
            "id_fuente_causa": fuente_causa.id if fuente_causa else None,
            "demora_1": _parse_bool(_get_value(row, ["10.3.1 Demora 1"])),
            "demora_2": _parse_bool(_get_value(row, ["10.3.2 Demora 2"])),
            "demora_3": _parse_bool(_get_value(row, ["10.3.3 Demora 3"])),
            "demora_4": _parse_bool(_get_value(row, ["10.3.4 Demora 4"])),
        },
        **kw,
    )
