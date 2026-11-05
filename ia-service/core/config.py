"""Configuración centralizada de IA-SERVICE, cargada desde variables de entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """Configuración de conexión al proveedor LLM y del servidor."""

    model_config = SettingsConfigDict(
        env_file=Path.cwd() / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # ponytail: las variables OLLAMA_MODEL y OLLAMA_TIMEOUT_S conservan su nombre histórico porque el .env del
    # servidor las usa; renombrarlas exige actualizar ese .env (hoy OLLAMA_MODEL es el id del modelo del proveedor).
    ollama_model: str = 'openai/gpt-oss-20b'
    ollama_timeout_s: float = 120.0
    # API compatible con OpenAI (producción: https://api.groq.com/openai/v1). Obligatoria.
    llm_base_url: str = ''
    llm_api_key: str = ''


Config = _Settings()
