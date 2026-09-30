"""Parseadores de tipos numéricos y booleanos."""

from typing import Any

from utils.text_utils import is_empty, slugify


def _parse_int(value: Any) -> int | None:
    """Convierte un valor a entero o None si está vacío."""
    resultado: int | None
    if is_empty(value):
        resultado = None
    else:
        resultado = int(float(value))
    return resultado


def _parse_decimal(value: Any) -> float | None:
    """Convierte un valor a float con un decimal o None si está vacío."""
    resultado: float | None
    if is_empty(value):
        resultado = None
    else:
        resultado = round(float(value), 1)
    return resultado


def _parse_bool(value: Any) -> bool:
    """Interpreta un valor de celda SIVIGILA como booleano (True o False).

    En el estándar SIVIGILA: 1 = Sí, 2 = No, 0 = Sin dato.

    Args:
        value: Valor de celda (bool, numérico, o cadena como 'Sí'/'X'/'1').

    Returns:
        True si el valor representa afirmativo; False en caso contrario.
    """
    if is_empty(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        try:
            return int(value) == 1
        except (ValueError, OverflowError):
            return False
    val_slug = slugify(value)
    return val_slug in {'1', '10', 'si', 's', 'true', 'x', 'yes', 'y'}


def es_valor_positivo(valor: Any) -> bool:
    """Determina si un valor de celda SIVIGILA representa afirmativo.

    En el estándar SIVIGILA: 1 = Sí, 2 = No, 0 = Sin dato.

    Args:
        valor: Valor de celda (cualquier tipo).

    Returns:
        True si el valor representa afirmativo (1 o 'Sí').
    """
    if is_empty(valor):
        return False
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        try:
            return int(valor) == 1
        except (ValueError, OverflowError):
            return False
    val_str = str(valor).strip().lower()
    return val_str in {'1', '1.0', 'si', 'sí', 's', 'true', 'x', 'yes', 'y'}
