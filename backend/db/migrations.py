"""Migraciones menores de arranque (idempotentes).

El proyecto crea tablas con `Base.metadata.create_all` y con el script SQL de
inicialización, pero `create_all` no añade columnas a tablas que ya existen. Estas
sentencias `ALTER ... ADD COLUMN IF NOT EXISTS` cubren la llegada del aislamiento por
secretaría (tenant) sobre bases de datos ya creadas, y son seguras de repetir en cada
arranque.
"""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Engine

from db.database import SessionLocal
from db.database_views import create_database_views

logger = logging.getLogger(__name__)

# Columnas nuevas del aislamiento por secretaría. `secretaria_codigo` es el tenant;
# `departamento`/`secretaria` guardan el nombre visible del usuario.
_ALTERACIONES: tuple[str, ...] = (
    "ALTER TABLE api_usuario ADD COLUMN IF NOT EXISTS departamento VARCHAR(100)",
    "ALTER TABLE api_usuario ADD COLUMN IF NOT EXISTS secretaria VARCHAR(150)",
    "ALTER TABLE api_usuario ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)",
    "ALTER TABLE api_analisis ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)",
    "ALTER TABLE api_sivigilaimportacion ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)",
    "ALTER TABLE caso_morbilidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)",
    "ALTER TABLE caso_mortalidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)",
)

# Índices para las búsquedas por tenant (todas las consultas filtran por secretaria_codigo).
_INDICES: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS ix_api_usuario_secretaria_codigo ON api_usuario (secretaria_codigo)",
    "CREATE INDEX IF NOT EXISTS ix_api_analisis_secretaria_codigo ON api_analisis (secretaria_codigo)",
    "CREATE INDEX IF NOT EXISTS ix_sivigilaimportacion_secretaria_codigo "
    "ON api_sivigilaimportacion (secretaria_codigo)",
    "CREATE INDEX IF NOT EXISTS ix_caso_morbilidad_secretaria_codigo "
    "ON caso_morbilidad (secretaria_codigo)",
    "CREATE INDEX IF NOT EXISTS ix_caso_mortalidad_secretaria_codigo "
    "ON caso_mortalidad (secretaria_codigo)",
)


def run_migrations(engine: Engine) -> None:
    """Aplica las migraciones de arranque y recrea las vistas.

    Nunca lanza excepciones: un fallo (por ejemplo, una base aún sin el esquema SQL)
    se registra y continúa, para no impedir que la aplicación levante.

    Args:
        engine: Motor de SQLAlchemy sobre la base de datos de la aplicación.
    """
    with engine.begin() as conn:
        for sql in _ALTERACIONES + _INDICES:
            try:
                conn.execute(text(sql))
            except Exception:
                logger.warning(
                    'Migración omitida (¿falta la tabla?): %s', sql, exc_info=True)

    # Las vistas se recrean para exponer la nueva columna secretaria_codigo.
    session = SessionLocal()
    try:
        create_database_views(session)
    except Exception:
        logger.warning(
            'No se pudieron recrear las vistas en el arranque.', exc_info=True)
    finally:
        session.close()
