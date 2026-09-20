"""Utilidades para manejo y limpieza de texto."""

import math
import re
import unicodedata
from typing import Any

import pandas as pd


def is_empty(value: Any) -> bool:
    """Devuelve True si el valor es None, vacío, NaN o cadenas centinela."""
    resultado: bool
    if value is None:
        resultado = True
    elif isinstance(value, str):
        resultado = value.strip() == '' or value.strip().lower() in {'nan', 'none', 'null'}
    elif isinstance(value, float):
        resultado = math.isnan(value)
    else:
        try:
            resultado = bool(pd.isna(value))
        except (TypeError, ValueError):
            resultado = False
    return resultado


def clean_text(value: Any) -> str | None:
    """Devuelve el valor como str limpio o None si está vacío."""
    resultado: str | None
    if is_empty(value):
        resultado = None
    else:
        resultado = str(value).strip()
    return resultado


def slugify(value: Any) -> str | None:
    """Normaliza texto: minúsculas, sin tildes ni caracteres especiales.

    Args:
        value: Valor de celda o encabezado a normalizar.

    Returns:
        Cadena normalizada o None si el valor está vacío.
    """
    texto = clean_text(value)
    resultado: str | None
    if texto is None:
        resultado = None
    else:
        sin_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        normalizado = sin_acentos.lower().replace('>', ' gt ').replace('<', ' lt ')
        resultado = ' '.join(re.sub(r'[^a-zA-Z0-9]+', ' ', normalizado).split())
    return resultado
