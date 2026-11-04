"""Configuración y conexión a la base de datos."""

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import Config

engine = create_engine(Config.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Nombres predecibles para llaves, únicos e índices (el script SQL y la base real coinciden).
# Los CHECK siempre llevan nombre explícito en el modelo.
_CONVENCION_NOMBRES = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': '%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}


class Base(DeclarativeBase):
    """Clase base para los modelos ORM."""

    metadata = MetaData(naming_convention=_CONVENCION_NOMBRES)


class VistaBase(DeclarativeBase):
    """Clase base para las VISTAS de solo lectura (`v_*`).

    Tienen su propio `MetaData`, separado del de `Base`: así `Base.metadata.create_all` nunca
    las crea como tablas físicas vacías. Las vistas las crea únicamente
    `db.database_views.create_database_views` (y el script SQL de reconstrucción).
    """

    metadata = MetaData()


def get_db():
    """Provee una sesión de base de datos y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
