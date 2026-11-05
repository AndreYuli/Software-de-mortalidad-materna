"""Tests del endpoint de health check."""

from fastapi.testclient import TestClient
from core.config import Config
from main import app

client = TestClient(app)


def test_health_devuelve_ok():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_generar_narrativa_devuelve_200_en_exito(mocker):
    mocker.patch('main.generar', return_value='Narrativa generada de prueba.')

    response = client.post(
        '/generar-narrativa',
        json={
            'tipo_narrativa': 'resumen_ejecutivo',
            'tipo_analisis': 'mortalidad',
            'indicadores': {'total_casos': 10},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body['narrativa'] == 'Narrativa generada de prueba.'
    assert body['modelo'] == Config.ollama_model


def test_generar_narrativa_devuelve_422_con_tipo_invalido():
    response = client.post(
        '/generar-narrativa',
        json={
            'tipo_narrativa': 'no_existe',
            'tipo_analisis': 'mortalidad',
            'indicadores': {},
        },
    )
    assert response.status_code == 422


def test_generar_narrativa_devuelve_503_si_el_proveedor_no_disponible(mocker):
    from llm_client import LLMUnavailableError

    mocker.patch(
        'main.generar',
        side_effect=LLMUnavailableError(
            "Function id 'x' in account 'cuenta-secreta' is not found"
        ),
    )

    response = client.post(
        '/generar-narrativa',
        json={
            'tipo_narrativa': 'resumen_ejecutivo',
            'tipo_analisis': 'mortalidad',
            'indicadores': {'total_casos': 10},
        },
    )

    assert response.status_code == 503
    # El detalle del proveedor (ids de función y de cuenta) no debe salir del microservicio.
    assert 'cuenta-secreta' not in response.text
