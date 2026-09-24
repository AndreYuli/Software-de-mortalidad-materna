"""Plantilla de prompt para alertas de tendencias mensuales."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que interpreta tendencias temporales de casos obstétricos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de alertas de tendencias a partir de la distribución mensual.

    Args:
        indicadores: Dict `distribucion_mensual` (conteo de casos por mes/año).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = (
        'mortalidad materna'
        if tipo_analisis == 'mortalidad'
        else 'morbilidad materna extrema'
    )
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Distribución mensual de casos de {evento}:\n{indicadores}\n\n'
        'Identifica si hay una tendencia al alza, a la baja, o picos puntuales, '
        'y si el patrón amerita una alerta de vigilancia epidemiológica.'
    )
    return prompt
