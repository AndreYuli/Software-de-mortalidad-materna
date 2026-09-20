"""Utilidades para manejo de JSON."""

import math
from typing import Any


def _sanitize_json(obj: Any) -> Any:
    """Reemplaza nan/inf con None para que json.dumps no falle.

    Args:
        obj: Objeto arbitrario (dict, list, float, etc.).

    Returns:
        Objeto con nan/inf reemplazados por None.
    """
    resultado: Any
    if isinstance(obj, dict):
        resultado = {k: _sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        resultado = [_sanitize_json(v) for v in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        resultado = None
    else:
        resultado = obj
    return resultado
