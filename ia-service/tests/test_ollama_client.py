"""Tests del cliente HTTP hacia Ollama, con httpx mockeado."""

import httpx
import pytest

from ollama_client import OllamaUnavailableError, generar


def test_generar_devuelve_texto_en_exito(mocker):
    respuesta_mock = httpx.Response(
        200,
        json={'response': 'Texto generado por el modelo.'},
        request=httpx.Request('POST', 'http://localhost:11434/api/generate'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    texto = generar('un prompt de prueba')

    assert texto == 'Texto generado por el modelo.'


def test_generar_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch(
        'httpx.Client.post', side_effect=httpx.ConnectError('connection refused')
    )

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_status_no_200(mocker):
    respuesta_mock = httpx.Response(
        500,
        json={'error': 'modelo no encontrado'},
        request=httpx.Request('POST', 'http://localhost:11434/api/generate'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')


def test_chatear_devuelve_texto_en_exito(mocker):
    from ollama_client import chatear

    respuesta_mock = httpx.Response(
        200,
        json={'message': {'content': 'Respuesta del chat.'}},
        request=httpx.Request('POST', 'http://localhost:11434/api/chat'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    texto = chatear([{'role': 'user', 'content': 'hola'}])

    assert texto == 'Respuesta del chat.'


def test_generar_y_chatear_usan_api_openai_si_hay_llm_base_url(mocker):
    from core.config import Config
    from ollama_client import chatear

    mocker.patch.object(Config, 'llm_base_url', 'https://api.ejemplo.com/v1/')
    mocker.patch.object(Config, 'llm_api_key', 'clave-de-prueba')
    post = mocker.patch(
        'httpx.Client.post',
        return_value=httpx.Response(
            200,
            json={'choices': [{'message': {'content': 'Hola desde el proveedor.'}}]},
            request=httpx.Request(
                'POST', 'https://api.ejemplo.com/v1/chat/completions'
            ),
        ),
    )

    assert generar('un prompt') == 'Hola desde el proveedor.'
    assert chatear([{'role': 'user', 'content': 'hola'}]) == 'Hola desde el proveedor.'
    url = post.call_args.args[0]
    assert url == 'https://api.ejemplo.com/v1/chat/completions'
    assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer clave-de-prueba'


def test_generar_openai_lanza_error_en_status_no_200(mocker):
    from core.config import Config

    mocker.patch.object(Config, 'llm_base_url', 'https://api.ejemplo.com/v1')
    mocker.patch(
        'httpx.Client.post',
        return_value=httpx.Response(
            410,
            json={'detail': 'modelo retirado'},
            request=httpx.Request(
                'POST', 'https://api.ejemplo.com/v1/chat/completions'
            ),
        ),
    )

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt')


def test_chatear_lanza_error_en_timeout(mocker):
    from ollama_client import chatear

    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(OllamaUnavailableError):
        chatear([{'role': 'user', 'content': 'hola'}])
