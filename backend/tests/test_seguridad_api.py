"""Pruebas de seguridad: los endpoints de datos exigen JWT válido; /media no es público."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token
from db.database import get_db
from db.models_sqlalchemy import Usuario
from main import app

RUTAS_PROTEGIDAS = [
    '/api/analisis/',
    '/api/analisis/historial/',
    '/api/analisis/1/',
    '/api/sivigila/resumen/',
    '/api/sivigila/pacientes/',
    '/api/sivigila/morbilidad/',
    '/api/sivigila/mortalidad/',
]


@pytest.fixture
def client(db_session):
    """Cliente HTTP sin sobreescribir la autenticación (solo la BD)."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.parametrize('ruta', RUTAS_PROTEGIDAS)
def test_sin_token_devuelve_401(client, ruta):
    """Sin header Authorization cada ruta protegida responde 401."""
    respuesta = client.get(ruta)
    assert respuesta.status_code == 401


@pytest.mark.parametrize('ruta', RUTAS_PROTEGIDAS)
def test_token_invalido_devuelve_401(client, ruta):
    """Un token que no es un JWT válido responde 401."""
    respuesta = client.get(ruta, headers={'Authorization': 'Bearer no-es-un-jwt'})
    assert respuesta.status_code == 401


def test_subida_sin_token_devuelve_401(client):
    """La subida de archivos exige autenticación."""
    respuesta = client.post('/api/analisis/', data={'tipo': 'mortalidad'})
    assert respuesta.status_code == 401


def test_token_valido_permite_acceso(client, db_session):
    """Con un JWT válido de un usuario existente se accede a los datos."""
    usuario = Usuario(
        nombre='Test', email='t@t.co', password_hash='x', fecha_registro=datetime.now(timezone.utc)
    )
    db_session.add(usuario)
    db_session.commit()
    token = create_access_token({'sub': str(usuario.id)})
    respuesta = client.get('/api/analisis/', headers={'Authorization': f'Bearer {token}'})
    assert respuesta.status_code == 200


def test_endpoints_publicos_siguen_abiertos(client):
    """Health y login siguen accesibles sin token."""
    assert client.get('/health').status_code == 200
    # credenciales inexistentes: rechazo por credenciales, no por falta de token
    r = client.post('/api/auth/login/', json={'email': 'x@x.co', 'password': '12345678'})
    assert r.status_code == 401
    assert 'incorrectos' in r.json()['detail']


def test_media_no_se_sirve_publicamente(client):
    """Los archivos cargados ya no se exponen como estáticos."""
    assert client.get('/media/uploads/2026/08/dummy_morbilidad.xlsx').status_code == 404
