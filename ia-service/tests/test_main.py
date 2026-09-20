"""Tests del endpoint de health check."""

from fastapi.testclient import TestClient

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
    assert body['modelo'] == 'qwen2.5'


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


def test_generar_narrativa_devuelve_503_si_ollama_no_disponible(mocker):
    from ollama_client import OllamaUnavailableError

    mocker.patch('main.generar', side_effect=OllamaUnavailableError('no disponible'))

    response = client.post(
        '/generar-narrativa',
        json={
            'tipo_narrativa': 'resumen_ejecutivo',
            'tipo_analisis': 'mortalidad',
            'indicadores': {'total_casos': 10},
        },
    )

    assert response.status_code == 503
