"""Configuración centralizada y lectura de variables de entorno."""

from pathlib import Path
from typing import Any

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """Configuración global de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=Path.cwd() / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Base de datos ---
    db_engine: str = "postgresql"
    db_user: str = "postgres"
    db_password: str = "password"
    db_name: str = "sivigila_maternidad"
    db_host: str = "localhost"
    db_port: int = 5432

    # --- JWT ---
    jwt_secret: str = "cambia-esto-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # --- Aplicación / OpenAPI ---
    app_title: str = "Mortalidad Materna API"
    app_version: str = "1.0.0"
    app_description: str = "Sistema de análisis de mortalidad y morbilidad materna — SIVIGILA"

    # --- CORS ---
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # --- IA generativa ---
    ia_service_url: str = "http://localhost:8001"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: Any) -> list[str]:
        """Permite definir BACKEND_CORS_ORIGINS como cadena separada por comas."""
        resultado: list[str]
        if isinstance(v, str):
            resultado = [o.strip() for o in v.split(",") if o.strip()]
        else:
            resultado = list(v)
        return resultado

    # --- Valores derivados ---
    @computed_field
    @property
    def database_url(self) -> str:
        """URL de conexión completa ensamblada desde los campos de base de datos."""
        resultado: str = (
            f"{self.db_engine}://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return resultado


Config = _Settings()
