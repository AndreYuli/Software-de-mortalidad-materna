"""Configuración centralizada de IA-SERVICE, cargada desde variables de entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """Configuración de conexión a Ollama y del servidor."""

    model_config = SettingsConfigDict(
        env_file=Path.cwd() / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    ollama_host: str = 'http://localhost:11434'
    ollama_model: str = 'qwen2.5'
    ollama_timeout_s: float = 120.0
    # Si llm_base_url está definido se usa una API compatible con OpenAI
    # (p. ej. https://integrate.api.nvidia.com/v1) en vez de Ollama;
    # entonces ollama_model es el id del modelo de ese proveedor.
    llm_base_url: str = ''
    llm_api_key: str = ''


Config = _Settings()
