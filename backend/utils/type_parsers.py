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


def _parse_bool(value: Any) -> int:
    """Interpreta un valor de celda SIVIGILA como 0 o 1.

    En el estándar SIVIGILA: 1 = Sí, 2 = No, 0 = Sin dato.

    Args:
        value: Valor de celda (bool, numérico, o cadena como 'Sí'/'X'/'1').

    Returns:
        1 si el valor representa afirmativo; 0 en caso contrario.
    """
    if is_empty(value):
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        try:
            return 1 if int(value) == 1 else 0
        except (ValueError, OverflowError):
            return 0
    val_slug = slugify(value)
    return 1 if val_slug in {"1", "10", "si", "s", "true", "x", "yes", "y"} else 0


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
    return val_str in {"1", "1.0", "si", "sí", "s", "true", "x", "yes", "y"}
