"""Mapeo y resolución de nombres de códigos CIE-10."""

import json
import logging
import re
from pathlib import Path

from utils.text_utils import clean_text

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


# Letra + 2 dígitos + (dígito o X): el punto se ignora, igual que en la tabla de referencia.
_FORMATO_CIE10 = re.compile(r'[A-Z]\d{2}[0-9X]?')


def es_codigo_cie10_valido(codigo: str | None) -> bool:
    """Indica si el código tiene formato CIE-10 y existe en la tabla de referencia.

    Acepta con o sin punto ('O14.1' y 'O141'), en minúscula y con espacios, y los códigos de
    categoría de 3 caracteres ('O85' se busca como 'O85X', igual que `obtener_nombre_cie10`).
    Si la tabla de referencia no está disponible sólo se comprueba el formato, para no rechazar
    cargas por un archivo de apoyo ausente.
    """
    if not codigo:
        return False
    clave = str(codigo).replace('.', '').strip().upper()
    if not _FORMATO_CIE10.fullmatch(clave):
        return False
    data = _cargar_cie10()
    if not data:
        return True
    return clave in data or (len(clave) == 3 and (clave + 'X') in data)


def normalizar_cie10(codigo: object) -> str:
    """Forma canónica con la que se guarda un código CIE-10: mayúsculas, sin punto ni espacios.

    'o14.1' y 'O141' son el mismo código; guardarlo siempre igual permite la llave foránea
    a la tabla `cie10` y evita que el mismo diagnóstico cuente como dos causas distintas.
    """
    return str(codigo).replace('.', '').strip().upper()


def limpiar_causa_asociada(valor: object) -> str | None:
    """Devuelve la causa asociada como texto, o None si está vacía o es sólo un guion ('—').

    Las plantillas de carga usan '—' para indicar "sin causa asociada"; no es un código.
    """
    texto = clean_text(valor)
    if texto is None or re.fullmatch(r'[-–—\s]+', texto):
        return None
    return texto
