"""Tests del cliente HTTP hacia Ollama, con httpx mockeado."""

import httpx
import pytest

from ollama_client import OllamaUnavailableError, generar


def test_generar_devuelve_texto_en_exito(mocker):
    respuesta_mock = httpx.Response(
        200,
        json={"response": "Texto generado por el modelo."},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )
    mocker.patch("httpx.Client.post", return_value=respuesta_mock)

    texto = generar("un prompt de prueba")

    assert texto == "Texto generado por el modelo."


def test_generar_lanza_error_en_timeout(mocker):
    mocker.patch("httpx.Client.post", side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(OllamaUnavailableError):
        generar("un prompt de prueba")


def test_generar_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch(
        "httpx.Client.post", side_effect=httpx.ConnectError("connection refused")
    )

    with pytest.raises(OllamaUnavailableError):
        generar("un prompt de prueba")


def test_generar_lanza_error_en_status_no_200(mocker):
    respuesta_mock = httpx.Response(
        500,
        json={"error": "modelo no encontrado"},
        request=httpx.Request("POST", "http://localhost:11434/api/generate"),
    )
    mocker.patch("httpx.Client.post", return_value=respuesta_mock)

    with pytest.raises(OllamaUnavailableError):
        generar("un prompt de prueba")
