"""Configuración y conexión a la base de datos."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from core.config import Config

engine = create_engine(Config.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Clase base para los modelos ORM."""


def get_db():
    """Provee una sesión de base de datos y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
