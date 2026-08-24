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
    ollama_timeout_s: float = 30.0


Config = _Settings()
