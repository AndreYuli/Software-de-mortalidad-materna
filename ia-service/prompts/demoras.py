"""Plantilla de prompt para demoras (mortalidad) / tiempo de remisión (morbilidad)."""

from typing import Any

_INSTRUCCIONES = (
    "Eres un asistente de salud pública que interpreta demoras en la atención obstétrica. "
    "Responde en español, en un tono profesional dirigido a personal de salud pública. "
    "Usa entre 150 y 250 palabras. "
    "No inventes cifras que no estén en los datos proporcionados. "
    "No menciones nombres propios ni identificadores de personas."
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de demoras/tiempo de remisión a partir de indicadores agregados.

    Args:
        indicadores: Para mortalidad, el dict de `analizar_demoras()` (4 demoras obstétricas).
            Para morbilidad, el dict de `analizar_tiempo_remision()` (boxplot de horas).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    if tipo_analisis == "mortalidad":
        contexto = (
            "Los datos describen la proporción de casos con presencia de cada una de las "
            "cuatro demoras del modelo de las tres demoras obstétricas ampliado a cuatro: "
            "reconocimiento del problema, decisión de buscar atención, acceso al centro de salud "
            "y calidad de la atención recibida."
        )
    else:
        contexto = (
            "Los datos describen la distribución estadística (mínimo, cuartiles, mediana, máximo) "
            "del tiempo de remisión entre instituciones, en horas."
        )
    prompt = (
        f"{_INSTRUCCIONES}\n\n"
        f"{contexto}\n\n"
        f"Datos agregados:\n{indicadores}\n\n"
        "Interpreta cuál es la demora o el rango de tiempo más crítico y sugiere una "
        "acción concreta de salud pública para mitigarlo."
    )
    return prompt
