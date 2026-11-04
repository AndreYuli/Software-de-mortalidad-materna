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

from db import models_sqlalchemy  # noqa: F401  (registra los modelos en Base.metadata)
from db.auditoria import aplicar_auditoria_y_maestras
from db.database import Base, SessionLocal
from db.database_views import create_database_views

logger = logging.getLogger(__name__)

# Columnas nuevas del aislamiento por secretaría. `secretaria_codigo` es el tenant;
# `departamento`/`secretaria` guardan el nombre visible del usuario.
_ALTERACIONES: tuple[str, ...] = (
    'ALTER TABLE api_usuario ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE api_analisis ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE api_sivigilaimportacion ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE caso_morbilidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE caso_mortalidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
)

# Índices para las búsquedas por tenant (todas las consultas filtran por secretaria_codigo).
_INDICES: tuple[str, ...] = (
    'CREATE INDEX IF NOT EXISTS ix_api_usuario_secretaria_codigo ON api_usuario (secretaria_codigo)',  # noqa: E501
    'CREATE INDEX IF NOT EXISTS ix_api_analisis_secretaria_codigo ON api_analisis (secretaria_codigo)',  # noqa: E501
    'CREATE INDEX IF NOT EXISTS ix_sivigilaimportacion_secretaria_codigo '
    'ON api_sivigilaimportacion (secretaria_codigo)',
    'CREATE INDEX IF NOT EXISTS ix_caso_morbilidad_secretaria_codigo '
    'ON caso_morbilidad (secretaria_codigo)',
    'CREATE INDEX IF NOT EXISTS ix_caso_mortalidad_secretaria_codigo '
    'ON caso_mortalidad (secretaria_codigo)',
)


# Normalización a 1FN (observación 8 de la asesora): los grupos de columnas repetidas pasan a
# tablas hijas con (padre, orden) único. Cada paso es idempotente: sólo copia y borra si la
# columna antigua todavía existe, y las tablas hijas las crea `create_all` antes de migrar.
# Se copia ANTES de borrar y todo va en una transacción (si algo falla, no se pierde nada).
# La vista v_morbilidad_completa depende de referencia.institucion_ref_1, por eso se elimina
# antes y `create_database_views` la recrea después.
_NORMALIZACION_1FN: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        'causas_morbilidad',
        'causa_asociada_2',
        (
            'INSERT INTO causa_asociada_morbilidad (id_caso, orden, cie10) '
            'SELECT id_caso, 1, causa_asociada_2 FROM causas_morbilidad '
            "WHERE causa_asociada_2 IS NOT NULL AND btrim(causa_asociada_2) <> '' "
            'ON CONFLICT (id_caso, orden) DO NOTHING',
            'INSERT INTO causa_asociada_morbilidad (id_caso, orden, cie10) '
            'SELECT id_caso, 2, causa_asociada_3 FROM causas_morbilidad '
            "WHERE causa_asociada_3 IS NOT NULL AND btrim(causa_asociada_3) <> '' "
            'ON CONFLICT (id_caso, orden) DO NOTHING',
            'INSERT INTO causa_asociada_morbilidad (id_caso, orden, cie10) '
            'SELECT id_caso, 3, causa_asociada_4 FROM causas_morbilidad '
            "WHERE causa_asociada_4 IS NOT NULL AND btrim(causa_asociada_4) <> '' "
            'ON CONFLICT (id_caso, orden) DO NOTHING',
            'ALTER TABLE causas_morbilidad DROP COLUMN causa_asociada_2, '
            'DROP COLUMN causa_asociada_3, DROP COLUMN causa_asociada_4',
        ),
    ),
    (
        'referencia',
        'institucion_ref_1',
        (
            'INSERT INTO referencia_institucion (id_referencia, orden, institucion) '
            'SELECT id_referencia, 1, institucion_ref_1 FROM referencia '
            "WHERE institucion_ref_1 IS NOT NULL AND btrim(institucion_ref_1) <> '' "
            'ON CONFLICT (id_referencia, orden) DO NOTHING',
            'INSERT INTO referencia_institucion (id_referencia, orden, institucion) '
            'SELECT id_referencia, 2, institucion_ref_2 FROM referencia '
            "WHERE institucion_ref_2 IS NOT NULL AND btrim(institucion_ref_2) <> '' "
            'ON CONFLICT (id_referencia, orden) DO NOTHING',
            'DROP VIEW IF EXISTS v_morbilidad_completa',
            'ALTER TABLE referencia DROP COLUMN institucion_ref_1, DROP COLUMN institucion_ref_2',
        ),
    ),
    (
        'manejo_hospitalario',
        'cirugia_1',
        (
            'INSERT INTO cirugia_adicional_morbilidad (id_manejo, orden, id_tipo_cirugia, cual) '
            'SELECT id_manejo, 1, cirugia_1, cirugia_1_cual FROM manejo_hospitalario '
            'WHERE cirugia_1 IS NOT NULL ON CONFLICT (id_manejo, orden) DO NOTHING',
            'INSERT INTO cirugia_adicional_morbilidad (id_manejo, orden, id_tipo_cirugia, cual) '
            'SELECT id_manejo, 2, cirugia_2, cirugia_2_cual FROM manejo_hospitalario '
            'WHERE cirugia_2 IS NOT NULL ON CONFLICT (id_manejo, orden) DO NOTHING',
            'ALTER TABLE manejo_hospitalario DROP COLUMN cirugia_1, DROP COLUMN cirugia_1_cual, '
            'DROP COLUMN cirugia_2, DROP COLUMN cirugia_2_cual',
        ),
    ),
)


# Las plantillas de carga usan '—' para "sin causa asociada"; la primera versión de la tabla hija
# lo guardaba como si fuera un código CIE-10. Se borra en cada arranque (idempotente).
SQL_LIMPIAR_MARCADORES_DE_VACIO = (
    'DELETE FROM causa_asociada_morbilidad '
    "WHERE trim(replace(replace(replace(cie10, '—', ''), '–', ''), '-', '')) = ''"
)


def _limpiar_marcadores_de_vacio(engine: Engine) -> None:
    """Borra de causa_asociada_morbilidad los guiones que no son códigos CIE-10."""
    try:
        with engine.begin() as conn:
            conn.execute(text(SQL_LIMPIAR_MARCADORES_DE_VACIO))
    except Exception:
        logger.warning('No se pudieron limpiar los marcadores de vacío', exc_info=True)


def _normalizar_1fn(engine: Engine) -> None:
    """Copia los grupos repetidos a sus tablas hijas y elimina las columnas antiguas.

    Sólo actúa en PostgreSQL y sólo si la columna antigua existe, así que es seguro repetirlo
    en cada arranque. Cada tabla se migra en su propia transacción: o se copia y se borra, o
    no cambia nada.
    """
    if engine.dialect.name != 'postgresql':
        return
    for tabla, columna_guia, sentencias in _NORMALIZACION_1FN:
        try:
            with engine.begin() as conn:
                existe = conn.execute(
                    text(
                        'SELECT 1 FROM information_schema.columns '
                        'WHERE table_schema = current_schema() AND table_name = :t AND column_name = :c'  # noqa: E501
                    ),
                    {'t': tabla, 'c': columna_guia},
                ).first()
                if not existe:
                    continue
                for sql in sentencias:
                    conn.execute(text(sql))
                logger.info('Normalización 1FN aplicada a %s', tabla)
        except Exception:
            logger.warning('Normalización 1FN omitida en %s', tabla, exc_info=True)


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
                logger.warning('Migración omitida (¿falta la tabla?): %s', sql, exc_info=True)

    Base.metadata.create_all(bind=engine)  # tablas hijas nuevas (no toca las existentes)
    aplicar_auditoria_y_maestras(engine)  # maestras y triggers (solo PostgreSQL)
    _normalizar_1fn(engine)
    _limpiar_marcadores_de_vacio(engine)

    # Las vistas se recrean para exponer la nueva columna secretaria_codigo.
    session = SessionLocal()
    try:
        create_database_views(session)
    except Exception:
        logger.warning('No se pudieron recrear las vistas en el arranque.', exc_info=True)
    finally:
        session.close()
