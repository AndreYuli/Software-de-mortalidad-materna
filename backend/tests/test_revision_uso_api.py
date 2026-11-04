"""Pruebas de las correcciones derivadas de la revisión de uso (partes 1 a 6)."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token
from db.database import get_db
from db.models_sqlalchemy import Analisis, Usuario
from main import app

REGISTRO = {
    'nombre': 'Ana Prueba',
    'email': 'ana@institucion.gov.co',
    'password': 'Clave-segura-2026',
    'departamento_codigo': 'antioquia',
    'secretaria_codigo': 'bello',
}


@pytest.fixture
def client(db_session):
    """Cliente HTTP con la BD de prueba."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _registrar(client, **cambios):
    return client.post('/api/auth/register/', json={**REGISTRO, **cambios})


@pytest.mark.parametrize(
    'clave',
    ['12345', '1234567', '123456', 'aaaaaa', 'password', '12345678', 'abcdefghijklmn', 'x' * 129],
)
def test_registro_rechaza_claves_debiles(client, clave):
    """Mínimo 15 caracteres (14 se rechaza), máximo 128 y sin claves comunes (NIST SP 800-63B-4)."""
    assert _registrar(client, password=clave).status_code == 422


def test_registro_acepta_clave_valida(client):
    """Una clave de 15+ caracteres no común se acepta."""
    assert _registrar(client).status_code == 201


@pytest.mark.parametrize('nombre', ['x' * 121, '<img src=x onerror=alert(1)>'])
def test_registro_valida_nombre(client, nombre):
    """El nombre tiene máximo 120 caracteres y no admite marcado HTML."""
    assert _registrar(client, nombre=nombre).status_code == 422


@pytest.mark.parametrize(
    'query',
    ['year=abc', 'year=99999', 'month=13', 'month=-1', 'month=abc', 'week=99', 'day=32'],
)
@pytest.mark.parametrize('ruta', ['completo', 'narrativa/mortalidad'])
def test_filtros_de_fecha_invalidos_devuelven_422(client, db_session, ruta, query):
    """Un filtro de fecha fuera de rango o no numérico es 422, nunca 500 con texto de Python."""
    if ruta != 'completo' and query.split('=')[0] in ('week', 'day'):
        pytest.skip('narrativa y chat sólo filtran por año y mes')
    usuario = Usuario(
        nombre='T',
        email='t@t.co',
        password_hash='x',
        secretaria_codigo='bello',
        fecha_registro=datetime.now(timezone.utc),
    )
    db_session.add(usuario)
    db_session.flush()
    analisis = Analisis(
        nombre_archivo='a.xlsx',
        tipo='mortalidad',
        secretaria_codigo='bello',
        archivo_hash='h',
        archivo='/media/uploads/a.xlsx',
        fecha_carga=datetime.now(timezone.utc),
        total_registros=1,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    token = create_access_token({'sub': str(usuario.id)})
    r = client.get(
        f'/api/analisis/{analisis.id}/{ruta}/?{query}', headers={'Authorization': f'Bearer {token}'}
    )
    assert r.status_code == 422, r.text
