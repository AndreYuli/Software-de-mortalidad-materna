"""Tests de las plantillas de prompt: no truenan con datos vacíos o parciales."""

import pytest

from prompts import construir_prompt

_TIPOS = ["resumen_ejecutivo", "demoras", "clustering", "tendencias"]


@pytest.mark.parametrize("tipo_narrativa", _TIPOS)
@pytest.mark.parametrize("tipo_analisis", ["mortalidad", "morbilidad"])
def test_construir_prompt_con_indicadores_vacios(tipo_narrativa, tipo_analisis):
    prompt = construir_prompt(tipo_narrativa, {}, tipo_analisis)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_construir_prompt_resumen_ejecutivo_incluye_datos():
    indicadores = {"total_casos": 42, "edad_promedio": 27.5}
    prompt = construir_prompt("resumen_ejecutivo", indicadores, "mortalidad")
    assert "42" in prompt
    assert "27.5" in prompt


def test_construir_prompt_tipo_narrativa_invalido_lanza_keyerror():
    with pytest.raises(KeyError):
        construir_prompt("inexistente", {}, "mortalidad")
