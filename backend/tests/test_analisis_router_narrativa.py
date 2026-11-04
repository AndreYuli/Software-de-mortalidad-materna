"""Tests del endpoint GET /api/analisis/{pk}/narrativa/{tipo}/."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import Analisis
from main import app


@pytest.fixture
def client(db_session):
    """Cliente HTTP con la dependencia de BD sobreescrita por la sesión de prueba."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(secretaria_codigo=None)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _crear_analisis(db_session) -> Analisis:
    analisis = Analisis(
        tipo='mortalidad',
        nombre_archivo='test.xlsx',
        archivo_hash='abc123',
        archivo='media/test.xlsx',
        fecha_carga=datetime.now(timezone.utc),
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    db_session.refresh(analisis)
    return analisis


def test_narrativa_devuelve_404_si_analisis_no_existe(client):
    """Un ID de análisis inexistente debe responder 404."""
    response = client.get('/api/analisis/9999/narrativa/resumen_ejecutivo/')
    assert response.status_code == 404


def test_narrativa_devuelve_503_si_ia_service_no_disponible(client, db_session, mocker, tmp_path):
    """Si IA-SERVICE falla, el router debe responder 503."""
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={'estadisticas_basicas': {'total_casos': 5}, 'tipo': 'mortalidad'},
    )
    from services.ia_client import IAServiceUnavailableError

    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        side_effect=IAServiceUnavailableError(
            "IA-SERVICE devolvió status 503: Function id 'x' in account 'cuenta-secreta' no existe"
        ),
    )

    response = client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    assert response.status_code == 503
    # El detalle del proveedor (ids de función y de cuenta) no debe llegar al usuario.
    assert response.json()['detail'] == 'El servicio de IA no está disponible en este momento.'
    assert 'cuenta-secreta' not in response.text


def test_narrativa_devuelve_200_con_narrativa_generada(client, db_session, mocker):
    """Con IA-SERVICE disponible, el router debe devolver la narrativa generada."""
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={'estadisticas_basicas': {'total_casos': 5}, 'tipo': 'mortalidad'},
    )
    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        return_value={
            'narrativa': 'Texto de prueba.',
            'modelo': 'qwen2.5',
            'generado_en': datetime.now(timezone.utc),
            'desde_cache': False,
        },
    )

    response = client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    assert response.status_code == 200
    body = response.json()
    assert body['narrativa'] == 'Texto de prueba.'
    assert body['desde_cache'] is False


def test_narrativa_no_envia_columnas_identificables_a_ia_client(client, db_session, mocker):
    """Verifica que el payload hacia narrativa_service nunca incluye PII."""
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={
            'estadisticas_basicas': {'total_casos': 5},
            'tipo': 'mortalidad',
            'nombre_archivo': 'test.xlsx',
        },
    )
    mock_obtener = mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        return_value={
            'narrativa': 'ok',
            'modelo': 'qwen2.5',
            'generado_en': datetime.now(timezone.utc),
            'desde_cache': False,
        },
    )

    client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    indicadores_enviados = (
        mock_obtener.call_args.kwargs.get('indicadores') or mock_obtener.call_args[0][3]
    )
    campos_prohibidos = {
        'nombres_apellidos',
        'numero_id',
        'nombre_archivo',
        'A. Nombres y Apellidos',
    }
    assert not (campos_prohibidos & set(indicadores_enviados.keys()))


def test_narrativa_de_clustering_pasa_la_sesion_de_bd_al_servicio(client, db_session, mocker):
    """La narrativa de agrupamiento llamaba a ejecutar_clustering sin la sesión de BD.

    Hallado el 3-nov-2026 al generar narrativas contra un servidor real: la ruta respondía 500
    ("ejecutar_clustering() missing 1 required positional argument: 'db'") en todas las llamadas.
    """
    analisis = _crear_analisis(db_session)
    mock_cluster = mocker.patch(
        'api.routers.analisis.analisis_service.ejecutar_clustering',
        return_value={'n_clusters': 2, 'perfiles': []},
    )
    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        return_value={
            'narrativa': 'ok',
            'modelo': 'qwen2.5',
            'generado_en': datetime.now(timezone.utc),
            'desde_cache': False,
        },
    )

    response = client.get(f'/api/analisis/{analisis.id}/narrativa/clustering/')

    assert response.status_code == 200
    assert mock_cluster.call_args.kwargs['db'] is db_session
