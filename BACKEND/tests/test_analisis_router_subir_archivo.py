"""Test de regresión: POST /api/analisis/ debe traducir ValueError a 422, no 500."""

import io

import pytest
from fastapi.testclient import TestClient

from db.database import get_db
from main import app


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_subir_archivo_devuelve_422_si_faltan_columnas(client, mocker):
    mocker.patch(
        'api.routers.analisis.analisis_service.procesar_subida',
        side_effect=ValueError('Faltan columnas requeridas: [...]'),
    )

    response = client.post(
        '/api/analisis/',
        data={'tipo': 'mortalidad'},
        files={'archivo': ('test.xlsx', io.BytesIO(b'contenido'), 'application/vnd.ms-excel')},
    )

    assert response.status_code == 422
    assert 'Faltan columnas' in response.json()['detail']
