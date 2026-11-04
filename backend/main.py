"""Punto de entrada de la aplicación FastAPI."""

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import analisis, auth, sivigila
from core.config import Config
from db.database import Base, engine
from db.migrations import run_migrations
from db.models_sqlalchemy import Analisis, NarrativaIA, SivigilaImportacion, Usuario  # noqa: F401

# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

app = FastAPI(
    title=Config.app_title,
    description=Config.app_description,
    version=Config.app_version,
)

MENSAJE_EMAIL_INVALIDO = (
    'El correo electrónico no es válido. Usa un correo institucional válido, '
    'por ejemplo tu.correo@institucion.gov.co.'
)


@app.exception_handler(RequestValidationError)
async def traducir_error_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Devuelve en español el error de email (p. ej. dominios .test) en login/registro.

    FastAPI/Pydantic generan el mensaje en inglés ("value is not a valid email
    address...") antes de llegar al router. Solo se intercepta ese caso; el resto
    de errores 422 conservan su formato original.
    """
    for error in exc.errors():
        loc = error.get('loc', ())
        msg = str(error.get('msg', ''))
        if 'email' in loc and ('valid email' in msg or 'email address' in msg):
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={'detail': MENSAJE_EMAIL_INVALIDO},
            )
    # Cualquier otro 422 se delega al manejador estándar de FastAPI, que sabe serializar los
    # errores de los validadores propios (ctx con excepciones).
    return await request_validation_exception_handler(request, exc)


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
# Migraciones de arranque: columnas del aislamiento por secretaría y vistas
# ---------------------------------------------------------------------------

run_migrations(engine)

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
