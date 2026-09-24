"""Cliente HTTP hacia la API local de Ollama."""

import httpx

from core.config import Config


class OllamaUnavailableError(Exception):
    """Se lanza cuando Ollama no responde, da timeout o devuelve un error."""


def _chat_openai(messages: list[dict[str, str]], timeout: float) -> str:
    """Llama a /chat/completions de una API compatible con OpenAI (LLM_BASE_URL)."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f'{Config.llm_base_url.rstrip("/")}/chat/completions',
                headers={'Authorization': f'Bearer {Config.llm_api_key}'},
                json={'model': Config.ollama_model, 'messages': messages},
            )
    except httpx.TimeoutException as exc:
        raise OllamaUnavailableError(
            f'Timeout esperando al proveedor LLM: {exc}'
        ) from exc
    except httpx.ConnectError as exc:
        raise OllamaUnavailableError(
            f'No se pudo conectar al proveedor LLM: {exc}'
        ) from exc

    if response.status_code != 200:
        raise OllamaUnavailableError(
            f'El proveedor LLM devolvió status {response.status_code}: {response.text}'
        )

    return response.json()['choices'][0]['message']['content']


def generar(prompt: str) -> str:
    """Envía un prompt a Ollama y devuelve el texto generado.

    Args:
        prompt: Prompt completo ya construido por una plantilla.

    Returns:
        Texto generado por el modelo.

    Raises:
        OllamaUnavailableError: Si Ollama no responde, da timeout, rechaza la
            conexión o devuelve un status distinto de 200.
    """
    if Config.llm_base_url:
        return _chat_openai(
            [{'role': 'user', 'content': prompt}], Config.ollama_timeout_s
        )
    try:
        with httpx.Client(timeout=Config.ollama_timeout_s) as client:
            response = client.post(
                f'{Config.ollama_host}/api/generate',
                json={'model': Config.ollama_model, 'prompt': prompt, 'stream': False},
            )
    except httpx.TimeoutException as exc:
        raise OllamaUnavailableError(
            f'Timeout esperando respuesta de Ollama: {exc}'
        ) from exc
    except httpx.ConnectError as exc:
        raise OllamaUnavailableError(f'No se pudo conectar a Ollama: {exc}') from exc

    if response.status_code != 200:
        raise OllamaUnavailableError(
            f'Ollama devolvió status {response.status_code}: {response.text}'
        )

    return response.json()['response']


def chatear(messages: list[dict[str, str]]) -> str:
    """Envía una lista de mensajes a Ollama (/api/chat) y devuelve la respuesta.

    Args:
        messages: Lista de diccionarios con claves 'role' y 'content'.

    Returns:
        Texto de la respuesta generada por el modelo.

    Raises:
        OllamaUnavailableError: Si Ollama no responde o devuelve error.
    """
    if Config.llm_base_url:
        return _chat_openai(messages, 120.0)
    try:
        # Usamos 120s explícitamente para el chat dado el contexto grande y el tiempo de cold-start
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f'{Config.ollama_host}/api/chat',
                json={
                    'model': Config.ollama_model,
                    'messages': messages,
                    'stream': False,
                },
            )
    except httpx.TimeoutException as exc:
        raise OllamaUnavailableError(
            f'Timeout esperando respuesta de Ollama (chat): {exc}'
        ) from exc
    except httpx.ConnectError as exc:
        raise OllamaUnavailableError(
            f'No se pudo conectar a Ollama (chat): {exc}'
        ) from exc

    if response.status_code != 200:
        raise OllamaUnavailableError(
            f'Ollama devolvió status {response.status_code} en chat: {response.text}'
        )

    return response.json()['message']['content']
