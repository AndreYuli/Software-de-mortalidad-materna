"""Bases de datos PostgreSQL DESECHABLES para las pruebas (nunca la base de la aplicación).

Las pruebas de PostgreSQL solo corren si se define, de forma explícita, la variable
`VM_PG_PRUEBAS` con una cadena de conexión libpq a un servidor de DESARROLLO, por ejemplo:

    VM_PG_PRUEBAS="host=127.0.0.1 port=55432 user=vm_prueba password=..."

Cada prueba crea bases `vm_prueba_<aleatorio>_<sufijo>` y las borra al terminar. El ayudante se
niega a operar sobre una base cuyo nombre no empiece por `vm_prueba_` o que sea la base
configurada para la aplicación (`DB_NAME`), para que una prueba nunca toque datos reales.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
import psycopg2.extensions
import pytest

PREFIJO = 'vm_prueba_'


def parametros() -> dict[str, str]:
    """Parámetros de conexión de `VM_PG_PRUEBAS`, u omite la prueba si no está definida."""
    dsn = os.environ.get('VM_PG_PRUEBAS')
    if not dsn:
        pytest.skip('requiere VM_PG_PRUEBAS (PostgreSQL de desarrollo para bases desechables)')
    return psycopg2.extensions.parse_dsn(dsn)


def _comprobar_nombre(nombre: str) -> None:
    if not nombre.startswith(PREFIJO):
        raise RuntimeError(f'Base no desechable rechazada: {nombre}')
    if nombre == os.environ.get('DB_NAME', 'sivigila_maternidad'):
        raise RuntimeError(f'La base {nombre} es la de la aplicación: no se usa en pruebas')


def conectar(nombre: str):
    """Conexión a una base desechable (con autocommit)."""
    _comprobar_nombre(nombre)
    conexion = psycopg2.connect(**{**parametros(), 'dbname': nombre})
    conexion.autocommit = True
    return conexion


@contextmanager
def bases_desechables(*sufijos: str) -> Iterator[dict[str, str]]:
    """Crea una base vacía por sufijo y las borra al salir. Devuelve {sufijo: nombre}."""
    params = parametros()
    try:
        admin = psycopg2.connect(**{**params, 'dbname': 'postgres'})
    except psycopg2.OperationalError:
        pytest.skip('PostgreSQL de VM_PG_PRUEBAS no accesible')
    admin.autocommit = True
    raiz = f'{PREFIJO}{uuid.uuid4().hex[:8]}'
    nombres = {s: f'{raiz}_{s}' for s in sufijos}
    cur = admin.cursor()
    try:
        for nombre in nombres.values():
            _comprobar_nombre(nombre)
            cur.execute(f'CREATE DATABASE {nombre}')
        yield nombres
    finally:
        for nombre in nombres.values():
            _comprobar_nombre(nombre)
            cur.execute(f'DROP DATABASE IF EXISTS {nombre} WITH (FORCE)')
        admin.close()
