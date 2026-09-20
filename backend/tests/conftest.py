"""Fixtures compartidos de pytest: sesión de base de datos en SQLite en memoria."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.database import Base


@pytest.fixture
def db_session():
    """Provee una sesión de BD SQLite en memoria, aislada por test.

    Usa ``StaticPool`` para que todas las conexiones (incluida la del hilo
    worker donde FastAPI ejecuta los endpoints síncronos vía TestClient)
    compartan la misma conexión SQLite ``:memory:``. Sin esto, cada hilo
    obtendría su propia base de datos en memoria vacía (comportamiento por
    defecto de SQLite con ``:memory:``), causando errores intermitentes de
    "no such table" en tests de endpoints reales.

    Yields:
        Sesión de SQLAlchemy con todas las tablas creadas.
    """
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    fabrica_sesiones = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = fabrica_sesiones()
    try:
        yield session
    finally:
        session.close()
