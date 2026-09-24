"""Tests del endpoint de chat sobre los datos de un análisis."""

from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from db.database import get_db
from main import app
from services.ia_client import IAServiceUnavailableError


@pytest.fixture
def client(db_session):
    """Client."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: object()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_analisis_service():
    """Mock analisis service."""
    with patch('api.routers.analisis.analisis_service') as mock:
        yield mock


@pytest.fixture
def mock_chatear_ia():
    """Mock chatear ia."""
    with patch('api.routers.analisis.chatear_ia') as mock:
        yield mock


def test_chat_analisis_devuelve_404_si_analisis_no_existe(client):
    """Chat analisis devuelve 404 si analisis no existe."""
    response = client.post('/api/analisis/999/chat/', json={'pregunta': '¿Hola?', 'historial': []})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_chat_analisis_devuelve_200_con_respuesta(
    client, db_session, mock_analisis_service, mock_chatear_ia
):
    # Setup
    """Chat analisis devuelve 200 con respuesta."""
    from datetime import datetime, timezone

    from db.models_sqlalchemy import Analisis

    analisis = Analisis(
        tipo='mortalidad',
        fecha_carga=datetime.now(timezone.utc),
        nombre_archivo='test.xlsx',
        archivo_hash='abc1234',
        archivo='media/test.xlsx',
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    db_session.refresh(analisis)

    mock_analisis_service.calcular_completo.return_value = {
        'estadisticas_basicas': {'total': 10},
        'distribucion_mensual': {'1': 10},
        'otra_cosa': 'secreto',
    }

    mock_chatear_ia.return_value = {'respuesta': 'Hubo 10 casos en enero.', 'modelo': 'qwen2.5'}

    # Execute
    response = client.post(
        f'/api/analisis/{analisis.id}/chat/',
        json={
            'pregunta': '¿Cuántos casos hubo?',
            'historial': [
                {'rol': 'usuario', 'contenido': 'hola'},
                {'rol': 'asistente', 'contenido': 'hola'},
            ],
        },
    )

    # Verify
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'respuesta': 'Hubo 10 casos en enero.', 'modelo': 'qwen2.5'}

    # Verify context extraction
    mock_chatear_ia.assert_called_once()
    args, kwargs = mock_chatear_ia.call_args
    assert args[0] == '¿Cuántos casos hubo?'
    assert args[1] == [
        {'rol': 'usuario', 'contenido': 'hola'},
        {'rol': 'asistente', 'contenido': 'hola'},
    ]
    assert args[2] == 'mortalidad'
    # Ensure 'otra_cosa' is NOT in the context sent to the LLM
    contexto = args[3]
    assert 'estadisticas_basicas' in contexto
    assert 'distribucion_mensual' in contexto
    assert 'otra_cosa' not in contexto


def test_chat_analisis_devuelve_503_si_ia_service_no_disponible(
    client, db_session, mock_analisis_service, mock_chatear_ia
):
    # Setup
    """Chat analisis devuelve 503 si ia service no disponible."""
    from datetime import datetime, timezone

    from db.models_sqlalchemy import Analisis

    analisis = Analisis(
        tipo='mortalidad',
        fecha_carga=datetime.now(timezone.utc),
        nombre_archivo='test.xlsx',
        archivo_hash='abc1234',
        archivo='media/test.xlsx',
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    db_session.refresh(analisis)

    mock_analisis_service.calcular_completo.return_value = {}
    mock_chatear_ia.side_effect = IAServiceUnavailableError('IA caída')

    # Execute
    response = client.post(
        f'/api/analisis/{analisis.id}/chat/', json={'pregunta': '¿Hola?', 'historial': []}
    )

    # Verify
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()['detail'] == 'IA caída'
