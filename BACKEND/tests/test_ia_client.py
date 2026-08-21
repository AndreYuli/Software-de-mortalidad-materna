"""Tests del cliente hacia IA-SERVICE, con httpx mockeado."""

import httpx
import pytest

from services.ia_client import IAServiceUnavailableError, generar_narrativa


def test_generar_narrativa_devuelve_narrativa_y_modelo_en_exito(mocker):
    respuesta_mock = httpx.Response(
        200, json={'narrativa': 'Texto generado.', 'modelo': 'qwen2.5'},
        request=httpx.Request('POST', 'http://localhost:8001/generar-narrativa'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    resultado = generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})

    assert resultado == {'narrativa': 'Texto generado.', 'modelo': 'qwen2.5'}


def test_generar_narrativa_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})


def test_generar_narrativa_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.ConnectError('connection refused'))

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})


def test_generar_narrativa_lanza_error_en_503_de_ia_service(mocker):
    respuesta_mock = httpx.Response(
        503, json={'detail': 'Ollama no disponible'},
        request=httpx.Request('POST', 'http://localhost:8001/generar-narrativa'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})
