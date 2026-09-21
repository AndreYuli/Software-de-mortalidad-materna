from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from ollama_client import OllamaUnavailableError
from core.config import Config

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
def test_chat_devuelve_503_si_ollama_no_disponible(mock_chatear):
    mock_chatear.side_effect = OllamaUnavailableError('Ollama no responde')

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
    assert response.json()['detail'] == 'Ollama no responde'
