"""Dispatcher de plantillas de prompt por tipo de narrativa."""

from typing import Any, Callable

from prompts import clustering, demoras, resumen_ejecutivo, tendencias

_CONSTRUCTORES: dict[str, Callable[[dict[str, Any], str], str]] = {
    'resumen_ejecutivo': resumen_ejecutivo.construir,
    'demoras': demoras.construir,
    'clustering': clustering.construir,
    'tendencias': tendencias.construir,
}


def construir_prompt(tipo_narrativa: str, indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Selecciona la plantilla según `tipo_narrativa` y arma el prompt.

    Args:
        tipo_narrativa: Uno de 'resumen_ejecutivo', 'demoras', 'clustering', 'tendencias'.
        indicadores: Datos agregados relevantes para esa narrativa.
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.

    Raises:
        KeyError: Si `tipo_narrativa` no tiene plantilla registrada.
    """
    constructor = _CONSTRUCTORES[tipo_narrativa]
    return constructor(indicadores, tipo_analisis)
