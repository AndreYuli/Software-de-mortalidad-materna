"""Constantes de columnas y helpers compartidos para escritura SIVIGILA.

Nota de tipado: row, model, caso y value usan Any porque operan sobre filas
pandas.Series y modelos SQLAlchemy que se resuelven dinámicamente en tiempo
de ejecución. catalog_cache y related_cache usan dict[Any, Any] porque sus
claves son clases de modelo SQLAlchemy, no cadenas.
"""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.models_sqlalchemy import CatTipoId, SivigilaImportacion
from services._sivigila_catalog import _resolve_catalog
from utils.column_validators import _require_text
from utils.date_parsers import _parse_date
from utils.text_utils import clean_text, is_empty, slugify

# ---------------------------------------------------------------------------
# Constantes de alias de columnas
# ---------------------------------------------------------------------------

_TIPO_ID_ALIASES = {
    "p": "PA",
    "pasaporte": "PA",
    "passport": "PA",
    "cc": "CC",
    "ce": "CE",
    "ppt": "PPT",
    "permiso proteccion temporal": "PPT",
    "permiso por proteccion temporal": "PPT",
    "ti": "TI",
    "tarjeta identidad": "TI",
    "rc": "RC",
    "registro civil": "RC",
}

_MORTALIDAD_FECHA_DEFUNCION_COLS = [
    "5.2 Fecha de defunción",
    "5.2 Fecha de defuncion",
    "5.2 Fecha defunción",
    "5.2 Fecha defuncion",
    "5.2 Fecha de defunción (dd/mm/aaaa)",
    "5.2 Fecha de defuncion (dd/mm/aaaa)",
    "Fecha de defunción",
    "Fecha de defuncion",
]
_MORTALIDAD_FUENTE_CAUSA_COLS = [
    "10.2 Fuente de causa de muerte",
    "10.2 Fuente causa de muerte",
    "Fuente causa muerte",
]
_MORTALIDAD_REMISIONES_COLS = [
    "8.3 Remisiones",
    "8.4 Remisiones",
    "Remisiones",
    "Remisiones oportunas",
]
_MORTALIDAD_MOMENTO_MUERTE_COLS = ["9.1 Momento de la muerte"]
_MORTALIDAD_FECHA_PARTO_COLS = [
    "9.3 Fecha parto (dd/mm/aaaa)",
    "9.3 Fecha parto",
    "Fecha parto (dd/mm/aaaa)",
    "Fecha parto",
]
_MORTALIDAD_HORA_PARTO_COLS = ["9.3 Hora parto", "Hora parto"]
_MORTALIDAD_ATENDIDO_POR_COLS = ["9.5 Atendido por", "Atendido por"]
_MORTALIDAD_NIVEL_PARTO_COLS = ["9.6 Nivel atención parto", "Nivel atención parto"]
_MORTALIDAD_PERSONAL_CPN_COLS = ["8.3 Personal CPN", "Personal CPN"]
_MORTALIDAD_NIVEL_CPN_COLS = ["8.4 Nivel atención CPN", "Nivel atención CPN"]

_MORBILIDAD_FECHA_EGRESO_COLS = [
    "Fecha de egreso",
    "Fecha egreso",
    "Fecha de egreso (dd/mm/aaaa)",
    "Fecha egreso (dd/mm/aaaa)",
]
_MORBILIDAD_TERMINACION_COLS = ["Terminación de la gestación", "Terminacion de la gestacion"]
_MORBILIDAD_ESTADO_RN_COLS = ["Estado recién nacido", "Estado recien nacido"]
_MORBILIDAD_PESO_RN_COLS = ["Peso RN gramos", "Peso RN", "Peso recién nacido"]
_MORBILIDAD_TRANSFUNDIDAS_COLS = ["Unidades transfundidas"]
_MORBILIDAD_GRUPO_CAUSA_COLS = ["Grupo causa", "Grupo de causa"]
_MORBILIDAD_INSTITUCION_REF_1_COLS = ["Institución referencia 1", "Institucion referencia 1"]
_MORBILIDAD_INSTITUCION_REF_2_COLS = ["Institución referencia 2", "Institucion referencia 2"]
_MORBILIDAD_TIEMPO_REMISION_COLS = [
    "Tiempo remisión (h)",
    "Tiempo remision (h)",
    "Tiempo remisión horas",
]

# ---------------------------------------------------------------------------
# Helpers de fila y dominio
# ---------------------------------------------------------------------------


def _get_value(row: Any, columns: list[str]) -> Any:
    """Devuelve el primer valor no vacío de la fila para la lista de columnas.

    Args:
        row: Fila del DataFrame (pandas.Series).
        columns: Lista de nombres de columna a buscar en orden.

    Returns:
        El primer valor no vacío encontrado, o None si no existe ninguno.
    """
    valor_encontrado: Any = None
    for col in columns:
        if col in row:
            val = row[col]
            if not is_empty(val):
                valor_encontrado = val
                break
    return valor_encontrado


def _has_any_value(row: Any, columns: list[str]) -> bool:
    """Comprueba si alguna de las columnas dadas tiene un valor no vacío.

    Args:
        row: Fila del DataFrame (pandas.Series).
        columns: Lista de nombres de columna a comprobar.

    Returns:
        True si al menos una columna tiene valor, False en caso contrario.
    """
    tiene_valor: bool = _get_value(row, columns) is not None
    return tiene_valor


def _normalizar_tipo_identificacion(value: Any) -> str | None:
    """Normaliza un valor de tipo de identificación a su código canónico.

    Args:
        value: Valor crudo de la celda de tipo de identificación.

    Returns:
        Código normalizado (ej. 'CC', 'PA') o None si el valor está vacío.
    """
    texto = clean_text(value)
    if texto is None:
        resultado: str | None = None
    else:
        resultado = _TIPO_ID_ALIASES.get(slugify(texto), texto)
    return resultado


def _resolve_momento_ocurrencia(value: Any) -> str | None:
    """Traduce un valor de momento de ocurrencia a su representación canónica.

    Args:
        value: Valor crudo: entero (1–4) o texto ('Antes', 'Durante', etc.).

    Returns:
        'Antes', 'Durante' o 'Despues', o None si el valor está vacío.
    """
    resultado: str | None = None
    if not is_empty(value):
        if isinstance(value, (int, float)):
            resultado = {1: "Antes", 2: "Durante", 3: "Despues", 4: "Despues"}.get(int(value))
        else:
            mapa_momento = {"antes": "Antes", "durante": "Durante", "despues": "Despues"}
            resultado = mapa_momento.get(slugify(value))
    return resultado


def _normalize_estado_rn(value: Any) -> str | None:
    """Normaliza el estado del recién nacido a 'Vivo' o 'Muerto'.

    Args:
        value: Valor crudo: entero (1=Vivo, 2=Muerto) o texto equivalente.

    Returns:
        'Vivo' o 'Muerto', o None si el valor está vacío o no reconocido.
    """
    resultado: str | None = None
    if not is_empty(value):
        if isinstance(value, (int, float)):
            resultado = {1: "Vivo", 2: "Muerto"}.get(int(value))
        else:
            resultado = {"vivo": "Vivo", "muerto": "Muerto"}.get(slugify(value))
    return resultado


# ---------------------------------------------------------------------------
# Upsert genérico y registro de importación
# ---------------------------------------------------------------------------


def _upsert_single_related(
    db: Session,
    model: Any,
    lookup: dict[str, Any],
    defaults: dict[str, Any],
    *,
    caso_creado: bool,
    related_cache: dict[Any, Any],
) -> Any:
    """Crea o actualiza un registro relacionado a un caso.

    Args:
        db: Sesión de base de datos.
        model: Modelo SQLAlchemy del registro relacionado.
        lookup: Campos de búsqueda (clave primaria del lado FK).
        defaults: Campos a crear o actualizar.
        caso_creado: Si True, el caso es nuevo y no existe el registro relacionado.
        related_cache: Cache de IDs ya existentes por modelo.

    Returns:
        Instancia creada o actualizada del modelo relacionado.
    """
    caso_id = lookup.get("id_caso")
    exists = caso_id in related_cache.get(model, set())

    if caso_creado or not exists:
        instancia: Any = model(**lookup, **defaults)
        db.add(instancia)
        related_cache.setdefault(model, set()).add(caso_id)
    else:
        instancia = db.query(model).filter_by(**lookup).first()
        if instancia is not None:
            for campo, valor in defaults.items():
                setattr(instancia, campo, valor)
        else:
            instancia = model(**lookup, **defaults)
            db.add(instancia)
            related_cache.setdefault(model, set()).add(caso_id)
    return instancia


def _registrar_importacion(
    db: Session,
    tipo: str,
    row_hash: str,
    event_hash: str,
    caso_id: int,
    identificacion: dict[str, Any],
) -> None:
    """Registra una fila de importación SIVIGILA para control de duplicados.

    Args:
        db: Sesión de base de datos.
        tipo: 'mortalidad' o 'morbilidad'.
        row_hash: Hash de contenido de la fila Excel.
        event_hash: Hash de identidad clínica del evento.
        caso_id: ID del caso mortalidad o morbilidad asociado.
        identificacion: Dict con numero_id y tipo_codigo del paciente.
    """
    db.add(
        SivigilaImportacion(
            tipo=tipo,
            row_hash=row_hash,
            event_hash=event_hash,
            caso_id=caso_id,
            numero_id=identificacion["numero_id"],
            tipo_identificacion=identificacion["tipo_codigo"],
            creado_en=datetime.now(timezone.utc),
        )
    )


def _actualizar_caso_mortalidad(
    db: Session, caso: Any, sitio_defuncion: Any, fecha_defuncion: date | None
) -> None:
    """Actualiza los campos de un caso de mortalidad si han cambiado.

    Args:
        db: Sesión de base de datos.
        caso: Instancia de CasoMortalidad a actualizar.
        sitio_defuncion: Instancia de CatSitioDefuncion con el nuevo sitio.
        fecha_defuncion: Nueva fecha de defunción, o None si no aplica.
    """
    changed = False
    if caso.id_sitio_defuncion != sitio_defuncion.id:
        caso.id_sitio_defuncion = sitio_defuncion.id
        changed = True
    if fecha_defuncion is not None and caso.fecha_defuncion != fecha_defuncion:
        caso.fecha_defuncion = fecha_defuncion
        changed = True
    if changed:
        db.flush()


# ---------------------------------------------------------------------------
# Resolución de identificación del paciente
# ---------------------------------------------------------------------------


def _resolver_identificacion(
    *,
    db: Session,
    nombres_col: str,
    tipo_id_col: str,
    numero_id_col: str,
    row: Any,
    numero_fila: int,
    catalog_cache: dict[Any, Any],
) -> dict[str, Any]:
    """Extrae y valida los datos de identificación de una fila Excel.

    Args:
        db: Sesión de base de datos.
        nombres_col: Nombre de la columna de nombres en el DataFrame.
        tipo_id_col: Nombre de la columna de tipo de identificación.
        numero_id_col: Nombre de la columna de número de identificación.
        row: Fila del DataFrame (pandas.Series).
        numero_fila: Número de fila para mensajes de error.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.

    Returns:
        Dict con nombres, tipo_obj, tipo_codigo, numero_id y fecha_nacimiento.
    """
    nombres = _require_text(_get_value(row, [nombres_col]), nombres_col, numero_fila)
    tipo_id_valor = _normalizar_tipo_identificacion(_get_value(row, [tipo_id_col]))
    tipo_obj = _resolve_catalog(
        db,
        CatTipoId,
        tipo_id_valor,
        catalog_cache=catalog_cache,
        numero_fila=numero_fila,
        nombre_campo=tipo_id_col,
        code_field="codigo",
    )
    numero_id = _require_text(_get_value(row, [numero_id_col]), numero_id_col, numero_fila)
    fecha_nacimiento = _parse_date(
        _get_value(
            row,
            [
                "Fecha de Nacimiento",
                "Fecha de nacimiento",
                "Fecha nacimiento",
            ],
        )
    )
    resultado_identificacion: dict[str, Any] = {
        "nombres": nombres,
        "tipo_obj": tipo_obj,
        "tipo_codigo": tipo_obj.codigo,
        "numero_id": numero_id,
        "fecha_nacimiento": fecha_nacimiento,
    }
    return resultado_identificacion
