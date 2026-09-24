"""Plantilla de prompt para el chatbot de datos."""

import json
from typing import Any

from schemas import ChatMensaje


def construir(
    pregunta: str,
    historial: list[ChatMensaje],
    contexto: dict[str, Any],
    tipo_analisis: str,
) -> list[dict[str, str]]:
    """Construye la lista de mensajes para el endpoint de chat de Ollama.

    Args:
        pregunta: Pregunta del usuario.
        historial: Conversación previa.
        contexto: Datos agregados que el LLM puede leer.
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de diccionarios compatibles con /api/chat.
    """
    contexto_str = json.dumps(contexto, ensure_ascii=False, indent=2)

    system_prompt = (
        f'Eres un experto asistente de salud pública especializado en análisis de {tipo_analisis} '
        'materna. Tu tarea es responder preguntas sobre los datos analizados utilizando ÚNICAMENTE '
        'la información proporcionada en el siguiente contexto de datos agregados en formato JSON.\n\n'
        'Reglas estrictas:\n'
        '1. NO inventes cifras ni datos que no estén en el contexto.\n'
        '2. Si el dato necesario para responder no se encuentra en el contexto, indica claramente '
        'que no dispones de esa información.\n'
        '3. NUNCA menciones nombres, identificaciones, ni detalles específicos de pacientes '
        'individuales. Mantén el anonimato.\n'
        '4. Responde de forma clara, concisa y directa a la pregunta formulada.\n\n'
        f'DATOS DE CONTEXTO:\n{contexto_str}'
    )

    messages = [{'role': 'system', 'content': system_prompt}]

    for msg in historial:
        # Mapear 'usuario' -> 'user', 'asistente' -> 'assistant'
        role = 'user' if msg.rol == 'usuario' else 'assistant'
        messages.append({'role': role, 'content': msg.contenido})

    messages.append({'role': 'user', 'content': pregunta})

    return messages
