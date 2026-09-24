"""Plantilla de prompt para el resumen ejecutivo."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que redacta resúmenes epidemiológicos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de resumen ejecutivo a partir de indicadores agregados.

    Args:
        indicadores: Subconjunto agregado con estadísticas básicas y causas/criterios principales.
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = (
        'Mortalidad Materna'
        if tipo_analisis == 'mortalidad'
        else 'Morbilidad Materna Extrema'
    )
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Escribe un resumen ejecutivo del análisis de {evento} con los siguientes datos agregados:\n'
        f'{indicadores}\n\n'
        'Estructura el resumen en: (1) panorama general con las cifras clave, '
        '(2) el hallazgo más relevante, (3) una recomendación de salud pública derivada de los datos.'
    )
    return prompt
