"""Plantilla de prompt para perfiles de clustering."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que interpreta resultados de clustering (K-means o jerárquico) '
    'sobre casos obstétricos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de interpretación de clusters a partir de perfiles agregados.

    Args:
        indicadores: Dict con `n_clusters`, `n_samples`, `features_used`,
            `cluster_sizes` y `cluster_profiles` (promedios de features por cluster).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = 'mortalidad materna' if tipo_analisis == 'mortalidad' else 'morbilidad materna extrema'
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Se agruparon casos de {evento} en clusters según similitud de características clínicas. '
        f'Perfiles obtenidos:\n{indicadores}\n\n'
        'Describe qué caracteriza a cada cluster (usa los promedios de features de cada uno) '
        'y qué perfil de paciente representa el grupo de mayor tamaño.'
    )
    return prompt
