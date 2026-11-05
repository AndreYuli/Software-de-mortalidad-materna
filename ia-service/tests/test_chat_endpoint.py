from unittest.mock import patch

from core.config import Config
from fastapi.testclient import TestClient
from main import app
from llm_client import LLMUnavailableError

client = TestClient(app)


@patch('main.chatear')
def test_chat_devuelve_200_en_exito(mock_chatear):
    mock_chatear.return_value = 'Hola, esta es la respuesta.'

    response = client.post(
        '/chat',
        json={
            'pregunta': '¿Hola?',
            'historial': [],
            'tipo_analisis': 'mortalidad',
            'contexto': {'estadisticas_basicas': {'total': 10}},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        'respuesta': 'Hola, esta es la respuesta.',
        'modelo': Config.ollama_model,
    }

    # Verifica que se llamó a chatear con una lista de mensajes construidos
    mock_chatear.assert_called_once()
    mensajes = mock_chatear.call_args[0][0]
    assert isinstance(mensajes, list)
    assert len(mensajes) > 0
    assert mensajes[0]['role'] == 'system'


@patch('main.chatear')
def test_chat_devuelve_503_si_el_proveedor_no_disponible(mock_chatear):
    mock_chatear.side_effect = LLMUnavailableError('El proveedor no responde')

    response = client.post(
        '/chat',
        json={
            'pregunta': '¿Hola?',
            'historial': [],
            'tipo_analisis': 'mortalidad',
            'contexto': {},
        },
    )

    assert response.status_code == 503
    assert (
        response.json()['detail']
        == 'El proveedor del modelo de lenguaje no está disponible.'
    )
    assert (
        'El proveedor no responde' not in response.text
    )  # el detalle crudo sólo va al log
