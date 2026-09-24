"""Punto de entrada de la aplicación FastAPI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import analisis, auth, sivigila
from core.config import Config
from db.database import Base, engine
from db.models_sqlalchemy import Analisis, NarrativaIA, SivigilaImportacion, Usuario  # noqa: F401

# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

app = FastAPI(
    title=Config.app_title,
    description=Config.app_description,
    version=Config.app_version,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ---------------------------------------------------------------------------
# Archivos cargados
# ---------------------------------------------------------------------------
# `media/` contiene los Excel con datos de pacientes: NO se expone como estático.

Path('media').mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Creación de tablas propias de la API (no gestionadas por el script SQL)
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(analisis.router)
app.include_router(sivigila.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get('/health', tags=['health'])
def health() -> dict[str, str]:
    """Verifica que el servidor está en funcionamiento.

    Returns:
        Diccionario con status 'ok'.
    """
    resultado: dict[str, str] = {'status': 'ok'}
    return resultado
