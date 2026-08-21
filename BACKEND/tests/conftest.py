"""Fixtures compartidos de pytest: sesión de base de datos en SQLite en memoria."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base


@pytest.fixture
def db_session():
    """Provee una sesión de BD SQLite en memoria, aislada por test.

    Yields:
        Sesión de SQLAlchemy con todas las tablas creadas.
    """
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
