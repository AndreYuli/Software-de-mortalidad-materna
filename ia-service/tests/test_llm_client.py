"""Tests del cliente HTTP hacia el proveedor LLM, con httpx mockeado."""

import httpx
import pytest
from core.config import Config
from llm_client import LLMUnavailableError, chatear, generar

URL = 'https://api.ejemplo.com/v1/chat/completions'


@pytest.fixture(autouse=True)
def proveedor_configurado(mocker):
    mocker.patch.object(Config, 'llm_base_url', 'https://api.ejemplo.com/v1/')
    mocker.patch.object(Config, 'llm_api_key', 'clave-de-prueba')


def _respuesta(status, json):
    return httpx.Response(status, json=json, request=httpx.Request('POST', URL))


def test_generar_devuelve_texto_en_exito(mocker):
    mocker.patch(
        'httpx.Client.post',
        return_value=_respuesta(
            200,
            {'choices': [{'message': {'content': 'Texto generado por el modelo.'}}]},
        ),
    )

    assert generar('un prompt de prueba') == 'Texto generado por el modelo.'


def test_generar_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(LLMUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch(
        'httpx.Client.post', side_effect=httpx.ConnectError('connection refused')
    )

    with pytest.raises(LLMUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_status_no_200(mocker):
    mocker.patch(
        'httpx.Client.post', return_value=_respuesta(410, {'detail': 'modelo retirado'})
    )

    with pytest.raises(LLMUnavailableError):
        generar('un prompt de prueba')


def test_chatear_devuelve_texto_en_exito(mocker):
    mocker.patch(
        'httpx.Client.post',
        return_value=_respuesta(
            200, {'choices': [{'message': {'content': 'Respuesta del chat.'}}]}
        ),
    )

    assert chatear([{'role': 'user', 'content': 'hola'}]) == 'Respuesta del chat.'


def test_generar_y_chatear_llaman_a_chat_completions_con_la_clave(mocker):
    post = mocker.patch(
        'httpx.Client.post',
        return_value=_respuesta(
            200, {'choices': [{'message': {'content': 'Hola desde el proveedor.'}}]}
        ),
    )

    assert generar('un prompt') == 'Hola desde el proveedor.'
    assert chatear([{'role': 'user', 'content': 'hola'}]) == 'Hola desde el proveedor.'
    assert post.call_args.args[0] == URL
    assert post.call_args.kwargs['headers']['Authorization'] == 'Bearer clave-de-prueba'
    assert post.call_args.kwargs['json']['model'] == Config.ollama_model


def test_chatear_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(LLMUnavailableError):
        chatear([{'role': 'user', 'content': 'hola'}])


def test_lanza_error_si_no_hay_llm_base_url(mocker):
    mocker.patch.object(Config, 'llm_base_url', '')
    post = mocker.patch('httpx.Client.post')

    with pytest.raises(LLMUnavailableError, match='LLM_BASE_URL'):
        generar('un prompt')
    with pytest.raises(LLMUnavailableError, match='LLM_BASE_URL'):
        chatear([{'role': 'user', 'content': 'hola'}])
    post.assert_not_called()
