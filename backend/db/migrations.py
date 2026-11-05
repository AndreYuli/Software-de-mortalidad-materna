"""Ajustes de arranque idempotentes y protección contra la estructura anterior.

El arranque crea las tablas que falten con `Base.metadata.create_all` y repite las tablas
maestras, los triggers y las vistas. `create_all` no añade columnas a tablas que ya existen:
las sentencias `ALTER ... ADD COLUMN IF NOT EXISTS` de este módulo cubren esas columnas y son
seguras de repetir en cada arranque.

**El arranque NO migra datos.** Una base con la estructura anterior (la de `main`, con
`antecedentes_obstetricos`, `antecedente_materno` y las columnas `causa_asociada_2/3/4`) se
pasa a la estructura nueva con `scripts/migrar_estructura_anterior.py`, que copia los datos a
una base NUEVA sin modificar la original (ver docs/MIGRACION_BD.md). Si el backend detecta la
estructura anterior, se niega a arrancar: crear las tablas nuevas vacías al lado de las viejas
dejaría los antecedentes históricos fuera de las vistas del dashboard.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from db import models_sqlalchemy  # noqa: F401  (registra los modelos en Base.metadata)
from db.auditoria import aplicar_auditoria_y_maestras
from db.database import Base
from db.database_views import create_database_views

logger = logging.getLogger(__name__)

# Columnas añadidas a tablas existentes. `secretaria_codigo` es el tenant; `evento`/`id_caso`
# de la bitácora identifican el caso de cada cambio (la función fn_auditar los escribe, así
# que deben existir antes de recrear los triggers).
_ALTERACIONES: tuple[str, ...] = (
    'ALTER TABLE api_usuario ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE api_analisis ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE api_sivigilaimportacion ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE caso_morbilidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE caso_mortalidad ADD COLUMN IF NOT EXISTS secretaria_codigo VARCHAR(60)',
    'ALTER TABLE auditoria_cambio ADD COLUMN IF NOT EXISTS evento VARCHAR(20)',
    'ALTER TABLE auditoria_cambio ADD COLUMN IF NOT EXISTS id_caso INTEGER',
)

# Índices para las búsquedas por tenant (todas las consultas filtran por secretaria_codigo).
_INDICES: tuple[str, ...] = (
    'CREATE INDEX IF NOT EXISTS ix_api_usuario_secretaria_codigo ON api_usuario (secretaria_codigo)',  # noqa: E501
    'CREATE INDEX IF NOT EXISTS ix_api_analisis_secretaria_codigo ON api_analisis (secretaria_codigo)',  # noqa: E501
    'CREATE INDEX IF NOT EXISTS ix_api_sivigilaimportacion_secretaria_codigo '
    'ON api_sivigilaimportacion (secretaria_codigo)',
    'CREATE INDEX IF NOT EXISTS ix_caso_morbilidad_secretaria_codigo '
    'ON caso_morbilidad (secretaria_codigo)',
    'CREATE INDEX IF NOT EXISTS ix_caso_mortalidad_secretaria_codigo '
    'ON caso_mortalidad (secretaria_codigo)',
    'CREATE INDEX IF NOT EXISTS ix_auditoria_evento_caso ON auditoria_cambio (evento, id_caso)',
)

# Señales de la estructura anterior: (tabla, columna o None si basta con que exista la tabla).
SENALES_ESTRUCTURA_ANTERIOR: tuple[tuple[str, str | None], ...] = (
    ('antecedentes_obstetricos', None),
    ('antecedente_materno', None),
    ('causas_morbilidad', 'causa_asociada_2'),
    ('referencia', 'institucion_ref_1'),
    ('manejo_hospitalario', 'cirugia_1'),
    ('control_prenatal', 'num_cpn'),
)


class EstructuraAnteriorError(RuntimeError):
    """La base tiene la estructura anterior y debe migrarse antes de arrancar."""


def detectar_estructura_anterior(engine: Engine) -> list[str]:
    """Devuelve las señales de la estructura anterior presentes en la base (vacía si no hay)."""
    inspector = inspect(engine)
    tablas = set(inspector.get_table_names())
    encontradas: list[str] = []
    for tabla, columna in SENALES_ESTRUCTURA_ANTERIOR:
        if tabla not in tablas:
            continue
        if columna is None:
            encontradas.append(tabla)
        elif columna in {c['name'] for c in inspector.get_columns(tabla)}:
            encontradas.append(f'{tabla}.{columna}')
    return encontradas


def verificar_estructura_compatible(engine: Engine) -> None:
    """Impide arrancar sobre una base con la estructura anterior.

    Raises:
        EstructuraAnteriorError: Si encuentra tablas o columnas de la estructura anterior.
    """
    senales = detectar_estructura_anterior(engine)
    if senales:
        raise EstructuraAnteriorError(
            'La base de datos tiene la estructura anterior (' + ', '.join(senales) + '). '
            'No se arranca para no dejar los datos históricos fuera de las vistas: migre los '
            'datos a una base nueva con scripts/migrar_estructura_anterior.py '
            '(ver docs/MIGRACION_BD.md).'
        )


def run_migrations(engine: Engine) -> None:
    """Aplica los ajustes de arranque y recrea las vistas.

    No lanza excepciones por un ajuste fallido (se registra y continúa), para no impedir que la
    aplicación levante. La estructura anterior se verifica antes, en
    `verificar_estructura_compatible`.

    Args:
        engine: Motor de SQLAlchemy sobre la base de datos de la aplicación.
    """
    Base.metadata.create_all(bind=engine)  # tablas que falten (no toca las existentes)

    if engine.dialect.name == 'postgresql':
        with engine.begin() as conn:
            for sql in _ALTERACIONES + _INDICES:
                try:
                    with conn.begin_nested():
                        conn.execute(text(sql))
                except Exception:
                    logger.warning('Ajuste omitido: %s', sql, exc_info=True)

    aplicar_auditoria_y_maestras(engine)  # maestras, catálogos vacíos y triggers (PostgreSQL)

    # Sesión sobre el MISMO motor recibido (no la base del .env): así las vistas se crean
    # donde corresponde también cuando se llama con otra base (pruebas, migración).
    session = Session(bind=engine)
    try:
        create_database_views(session)
    except Exception:
        logger.warning('No se pudieron recrear las vistas en el arranque.', exc_info=True)
    finally:
        session.close()
