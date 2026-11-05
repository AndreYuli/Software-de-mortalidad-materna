"""Fixtures compartidos de pytest: sesión de base de datos en PostgreSQL (base de pruebas aparte).

Las pruebas NUNCA usan la base de desarrollo: `DB_NAME` se redirige a `TEST_DB_NAME`
(por defecto `maternanalytics_test`) antes de importar la app, y se crea si no existe.
Cada prueba corre dentro de una transacción que se revierte al terminar.
"""

import os

import pytest

# Debe ir ANTES de importar `db.database` / `main`: ellos crean el engine y ejecutan
# create_all + migraciones al importarse, y deben hacerlo sobre la base de pruebas.
TEST_DB_NAME = os.environ.get('TEST_DB_NAME', 'maternanalytics_test')
if 'test' not in TEST_DB_NAME and 'prueba' not in TEST_DB_NAME:
    raise RuntimeError(f"TEST_DB_NAME debe contener 'test' o 'prueba' (recibido: {TEST_DB_NAME!r})")
os.environ['DB_NAME'] = TEST_DB_NAME
os.environ.setdefault('DB_ENGINE', 'postgresql')


def _crear_base_si_no_existe() -> None:
    """Crea la base de pruebas si no existe (se conecta a la base de mantenimiento 'postgres')."""
    import psycopg2

    from core.config import Config

    conexion = psycopg2.connect(
        host=Config.db_host,
        port=Config.db_port,
        user=Config.db_user,
        password=Config.db_password,
        dbname='postgres',
    )
    conexion.autocommit = True
    try:
        cursor = conexion.cursor()
        cursor.execute('SELECT 1 FROM pg_database WHERE datname = %s', (TEST_DB_NAME,))
        if cursor.fetchone() is None:
            cursor.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        conexion.close()


_crear_base_si_no_existe()

from sqlalchemy.orm import Session  # noqa: E402

from db.database import Base, engine  # noqa: E402

assert engine.dialect.name == 'postgresql', engine.dialect.name
assert engine.url.database == TEST_DB_NAME, engine.url.database
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """Sesión de PostgreSQL aislada por prueba.

    La sesión se une a una transacción externa; `commit()` dentro de la prueba solo libera un
    savepoint, y al terminar todo se revierte, así que no queda ningún dato entre pruebas.

    Yields:
        Sesión de SQLAlchemy sobre la base de pruebas.
    """
    conexion = engine.connect()
    transaccion = conexion.begin()
    session = Session(bind=conexion, join_transaction_mode='create_savepoint')
    try:
        yield session
    finally:
        session.close()
        transaccion.rollback()
        conexion.close()
