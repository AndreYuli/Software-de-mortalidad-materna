"""Resolución de registros de catálogo SIVIGILA contra la base de datos.

Nota de tipado: model y value usan Any porque estas funciones resuelven
dinámicamente cualquier modelo de catálogo SQLAlchemy en tiempo de ejecución.
El caché se recibe como parámetro (catalog_cache: dict) para que su ciclo de
vida quede acotado a la petición HTTP que lo origina.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from utils.text_utils import clean_text, is_empty, slugify

logger = logging.getLogger(__name__)


def _catalog_comparables(obj: Any, code_field: str | None, extra_field: str | None) -> list[Any]:
    """Reúne los valores comparables de un objeto de catálogo para búsqueda por texto.

    Args:
        obj: Instancia del modelo de catálogo.
        code_field: Nombre del campo de código alternativo, o None.
        extra_field: Nombre del campo extra a comparar, o None.

    Returns:
        Lista de valores de texto presentes en el objeto.
    """
    comparables: list[Any] = []
    if hasattr(obj, 'descripcion'):
        comparables.append(getattr(obj, 'descripcion'))
    if code_field and hasattr(obj, code_field):
        comparables.append(getattr(obj, code_field))
    if extra_field and hasattr(obj, extra_field):
        comparables.append(getattr(obj, extra_field))
    return comparables


def _resolve_catalog_by_id(db: Session, model: Any, value: Any, catalog_cache: dict) -> Any | None:
    """Busca un registro de catálogo por su ID numérico.

    Args:
        db: Sesión de base de datos.
        model: Modelo SQLAlchemy del catálogo.
        value: Valor a convertir a ID entero.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.

    Returns:
        Instancia del catálogo o None si no se encontró o no era numérico.
    """
    resultado: Any | None = None
    val_id: int | None = None
    try:
        if not isinstance(value, bool):
            val_id = int(float(value))
    except (ValueError, TypeError) as exc:
        logger.debug('No se pudo convertir a ID numérico el valor %r: %s', value, exc)
    if val_id is not None:
        cache_key = ('by_id', model)
        if cache_key not in catalog_cache:
            catalog_cache[cache_key] = {
                getattr(obj, 'id_catalogo', getattr(obj, 'id', None)): obj
                for obj in db.query(model).all()
            }
        resultado = catalog_cache[cache_key].get(val_id)
    return resultado


def _resolve_catalog_by_fields(
    db: Session,
    model: Any,
    texto: str,
    *,
    catalog_cache: dict,
    code_field: str | None = None,
    extra_field: str | None = None,
) -> Any | None:
    """Busca un registro de catálogo por coincidencia de texto normalizado.

    Args:
        db: Sesión de base de datos.
        model: Modelo SQLAlchemy del catálogo.
        texto: Texto a comparar contra los campos del catálogo.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.
        code_field: Campo de código alternativo a comparar exacto.
        extra_field: Campo extra a incluir en la comparación slugificada.

    Returns:
        Instancia del catálogo o None si no se encontró coincidencia.
    """
    resultado: Any | None = None
    cache_key = ('by_fields', model)
    if cache_key not in catalog_cache:
        catalog_cache[cache_key] = db.query(model).all()
    if code_field:
        for obj in catalog_cache[cache_key]:
            code_val = getattr(obj, code_field, None)
            if code_val and str(code_val).strip().lower() == texto.lower():
                resultado = obj
                break
    if resultado is None:
        slug = slugify(texto)
        if slug:
            slug_norm = slug.replace(' de ', ' ')
            for obj in catalog_cache[cache_key]:
                for v in _catalog_comparables(obj, code_field, extra_field):
                    v_slug = slugify(v)
                    if v_slug and (v_slug == slug or v_slug.replace(' de ', ' ') == slug_norm):
                        resultado = obj
                        break
                if resultado:
                    break
    return resultado


def _resolve_catalog(
    db: Session,
    model: Any,
    value: Any,
    *,
    catalog_cache: dict,
    numero_fila: int | None = None,
    nombre_campo: str | None = None,
    required: bool = True,
    code_field: str | None = None,
    extra_field: str | None = None,
) -> Any | None:
    """Busca un registro de catálogo por ID o por texto normalizado.

    Args:
        db: Sesión de base de datos.
        model: Modelo SQLAlchemy del catálogo.
        value: Valor de la celda (ID numérico o texto).
        catalog_cache: Caché local de la petición para evitar consultas repetidas.
        numero_fila: Número de fila Excel para mensajes de error.
        nombre_campo: Nombre del campo para mensajes de error.
        required: Si True lanza ValueError cuando no se encuentra.
        code_field: Campo alternativo de código a comparar.
        extra_field: Campo extra a comparar.

    Returns:
        Instancia del catálogo o None si no es requerido.

    Raises:
        ValueError: Si required=True y no se encuentra el valor.
    """
    resultado: Any | None = None
    vacio = is_empty(value)
    texto = None if vacio else clean_text(value)
    if vacio or texto is None:
        if required:
            raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
    else:
        obj = _resolve_catalog_by_id(db, model, value, catalog_cache)
        if obj is None:
            obj = _resolve_catalog_by_fields(
                db,
                model,
                texto,
                catalog_cache=catalog_cache,
                code_field=code_field,
                extra_field=extra_field,
            )
        resultado = obj
        if resultado is None and required:
            raise ValueError(
                f'Fila {numero_fila}: no se encontró catálogo para {nombre_campo}={texto!r}.'
            )
    return resultado


def _resolve_catalog_optional(
    db: Session,
    model: Any,
    value: Any,
    *,
    catalog_cache: dict,
    extra_field: str | None = None,
) -> Any | None:
    """Atajo para resolver un catálogo sin lanzar error si no se encuentra.

    Args:
        db: Sesión de base de datos.
        model: Modelo SQLAlchemy del catálogo.
        value: Valor de la celda.
        catalog_cache: Caché local de la petición para evitar consultas repetidas.
        extra_field: Campo extra a comparar.

    Returns:
        Instancia del catálogo o None.
    """
    resultado: Any | None = _resolve_catalog(
        db,
        model,
        value,
        catalog_cache=catalog_cache,
        required=False,
        extra_field=extra_field,
    )
    return resultado
