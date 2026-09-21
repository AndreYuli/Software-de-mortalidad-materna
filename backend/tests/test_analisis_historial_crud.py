"""Tests de edición y eliminación de cargas del historial."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import Analisis, NarrativaIA
from main import app


@pytest.fixture
def client(db_session):
    """Client."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: object()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def carga(db_session):
    """Carga."""
    a = Analisis(
        tipo='mortalidad',
        nombre_archivo='agosto.xlsx',
        archivo_hash='h',
        archivo='',
        fecha_carga=datetime(2025, 8, 18, 15, 0),
        total_registros=3,
        resumen={},
    )
    db_session.add(a)
    db_session.commit()
    return a


def test_patch_corrige_nombre_y_fecha(client, carga):
    """Patch corrige nombre y fecha."""
    r = client.patch(
        f'/api/analisis/{carga.id}/',
        json={
            'nombre_archivo': ' septiembre.xlsx ',
            'fecha_carga': '2025-09-02T10:00:00',
        },
    )
    assert r.status_code == 200
    assert r.json()['nombre_archivo'] == 'septiembre.xlsx'
    h = client.get('/api/analisis/historial/?month=9&year=2025').json()
    assert [i['id'] for i in h['items']] == [carga.id]


def test_patch_rechaza_nombre_vacio_y_peticion_sin_cambios(client, carga):
    """Patch rechaza nombre vacio y peticion sin cambios."""
    assert (
        client.patch(f'/api/analisis/{carga.id}/', json={'nombre_archivo': '  '}).status_code == 422
    )
    assert client.patch(f'/api/analisis/{carga.id}/', json={}).status_code == 422


def test_patch_y_delete_404_si_no_existe(client):
    """Patch y delete 404 si no existe."""
    assert client.patch('/api/analisis/999/', json={'nombre_archivo': 'x'}).status_code == 404
    assert client.delete('/api/analisis/999/').status_code == 404


def test_delete_elimina_carga_y_sus_narrativas(client, db_session, carga):
    """Delete elimina carga y sus narrativas."""
    db_session.add(
        NarrativaIA(
            analisis_id=carga.id,
            tipo_narrativa='resumen_ejecutivo',
            filtros_hash='x',
            contenido='t',
            modelo='m',
            generado_en=datetime(2025, 8, 19),
        )
    )
    db_session.commit()
    assert client.delete(f'/api/analisis/{carga.id}/').status_code == 204
    assert db_session.query(Analisis).count() == 0
    assert db_session.query(NarrativaIA).count() == 0
