"""Cliente HTTP hacia el proveedor LLM (API compatible con OpenAI; en producción, Groq)."""

import httpx
from core.config import Config


class LLMUnavailableError(Exception):
    """Se lanza cuando el proveedor LLM no está configurado, no responde, da timeout o devuelve un error."""


def _chat(messages: list[dict[str, str]], timeout: float) -> str:
    """Llama a /chat/completions de la API compatible con OpenAI definida en LLM_BASE_URL."""
    if not Config.llm_base_url:
        raise LLMUnavailableError(
            'LLM_BASE_URL no está configurada: define el proveedor LLM en ia-service/.env.'
        )
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f'{Config.llm_base_url.rstrip("/")}/chat/completions',
                headers={'Authorization': f'Bearer {Config.llm_api_key}'},
                json={'model': Config.ollama_model, 'messages': messages},
            )
    except httpx.TimeoutException as exc:
        raise LLMUnavailableError(f'Timeout esperando al proveedor LLM: {exc}') from exc
    except httpx.ConnectError as exc:
        raise LLMUnavailableError(
            f'No se pudo conectar al proveedor LLM: {exc}'
        ) from exc

    if response.status_code != 200:
        raise LLMUnavailableError(
            f'El proveedor LLM devolvió status {response.status_code}: {response.text}'
        )

    return response.json()['choices'][0]['message']['content']


def generar(prompt: str) -> str:
    """Envía un prompt al proveedor LLM y devuelve el texto generado.

    Args:
        prompt: Prompt completo ya construido por una plantilla.

    Returns:
        Texto generado por el modelo.

    Raises:
        LLMUnavailableError: Si el proveedor no está configurado, no responde, da
            timeout o devuelve un status distinto de 200.
    """
    return _chat([{'role': 'user', 'content': prompt}], Config.ollama_timeout_s)


def chatear(messages: list[dict[str, str]]) -> str:
    """Envía una lista de mensajes al proveedor LLM y devuelve la respuesta.

    Args:
        messages: Lista de diccionarios con claves 'role' y 'content'.

    Returns:
        Texto de la respuesta generada por el modelo.

    Raises:
        LLMUnavailableError: Si el proveedor no está configurado, no responde o devuelve error.
    """
    # 120 s fijos para el chat por el contexto grande y el posible cold-start
    return _chat(messages, 120.0)
