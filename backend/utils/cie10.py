"""Mapeo y resolución de nombres de códigos CIE-10."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CIE10_CACHE: dict[str, str] | None = None


def _cargar_cie10() -> dict[str, str]:
    global _CIE10_CACHE
    if _CIE10_CACHE is not None:
        return _CIE10_CACHE

    base_dir = Path(__file__).resolve().parent.parent
    posibles_rutas = [
        base_dir.parent / 'data' / 'referencia' / 'cie10_nombres.json',
        base_dir / 'data' / 'referencia' / 'cie10_nombres.json',
        Path('data/referencia/cie10_nombres.json'),
    ]
    for ruta in posibles_rutas:
        if ruta.is_file():
            try:
                with open(ruta, encoding='utf-8') as f:
                    _CIE10_CACHE = json.load(f)
                    return _CIE10_CACHE
            except Exception as e:
                logger.warning('Error al cargar CIE-10 de %s: %s', ruta, e)

    _CIE10_CACHE = {}
    return _CIE10_CACHE


def obtener_nombre_cie10(codigo: str | None) -> str:
    """Retorna la descripción legible del código CIE-10 o el mismo código si no se encuentra."""
    if not codigo:
        return ''
    data = _cargar_cie10()
    clave = str(codigo).replace('.', '').strip().upper()
    if clave in data:
        return data[clave]
    if len(clave) == 3 and (clave + 'X') in data:
        return data[clave + 'X']
    return str(codigo).strip()
