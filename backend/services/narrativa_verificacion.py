"""Verificación automática, reproducible, de las narrativas generadas por IA.

Cubre los dos primeros niveles de validación de la Tabla 5 del artículo, que son los que se
pueden comprobar sin criterio humano:

1. Correspondencia numérica: cada cifra del texto debe ser igual a algún valor de los
   indicadores de origen, redondeada a los decimales con que aparece en el texto.
2. Coherencia textual mínima: reglas deterministas (lenguaje prescriptivo, lenguaje causal,
   códigos CIE-10 ausentes de los datos, identificadores de personas, texto vacío).

No sustituye la validez clínica ni epidemiológica, que requiere profesionales de salud.
El criterio de coincidencia y la exclusión de códigos son los de la «Validación 2» del proyecto.
"""

import re
from collections.abc import Iterator
from typing import Any

_NUM = re.compile(r'(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)')
# Lo que no es un dato: códigos CIE-10, «CIE-10», «demora N», numeración «(1)» / «1.»
_NO_DATO = re.compile(
    r'\bO\d{2}(?:\.\d)?\b|\bCIE-?10\b|[Dd]emoras?\s+\d(?:\s*(?:,|y|e)\s*\d)*|\(\d\)|^\s*\d\.\s',
    re.MULTILINE,
)
_CODIGO_CIE10 = re.compile(r'\bO\d{2}(?:\.\d)?\b')
_PRESCRIPTIVO = re.compile(
    r'\b(?:se recomienda|recomendamos|se sugiere (?:iniciar|administrar|tratar)|debe(?:n)? '
    r'(?:administrarse|tratarse|iniciarse)|iniciar tratamiento|tratamiento con|prescrib\w*)\b',
    re.IGNORECASE,
)
_CAUSAL = re.compile(
    r'\b(?:caus[óo] (?:la|el|las|los)|provoc[óo]|ocasion[óo]|se debe a|debido a)\b',
    re.IGNORECASE,
)
_IDENTIFICADOR = re.compile(r'(?<!\d)\d{7,}(?!\d)')
_MINIMO_CARACTERES = 40


def numeros_de(obj: Any) -> Iterator[float]:
    """Recorre un valor anidado (dicts, listas) y entrega todos sus números."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from numeros_de(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from numeros_de(v)


def _codigos_de(obj: Any) -> set[str]:
    """Códigos CIE-10 presentes en cualquier cadena de los indicadores."""
    if isinstance(obj, str):
        return set(_CODIGO_CIE10.findall(obj.upper()))
    if isinstance(obj, dict):
        encontrados: set[str] = set()
        for k, v in obj.items():
            encontrados |= _codigos_de(k) | _codigos_de(v)
        return encontrados
    if isinstance(obj, (list, tuple)):
        encontrados = set()
        for v in obj:
            encontrados |= _codigos_de(v)
        return encontrados
    return set()


def cifras_del_texto(texto: str) -> Iterator[tuple[str, float, int]]:
    """Cifras del texto que son datos: (texto crudo, valor, decimales)."""
    limpio = _NO_DATO.sub(' ', texto)
    for m in _NUM.finditer(limpio):
        crudo = m.group(1)
        if re.fullmatch(r'\d{1,3}(?:\.\d{3})+(?:,\d+)?', crudo):  # 2.000 / 2.000,5
            valor = float(crudo.replace('.', '').replace(',', '.'))
            dec = len(crudo.split(',')[1]) if ',' in crudo else 0
        else:
            valor = float(crudo.replace(',', '.'))
            dec = len(re.split(r'[.,]', crudo)[1]) if re.search(r'[.,]', crudo) else 0
        yield crudo, valor, dec


def _coincide(crudo: str, valor: float, dec: int, fuente: list[float]) -> bool:
    """«2,000» puede ser dos mil (coma de miles) o 2,000 (coma decimal): vale cualquiera."""
    candidatos = [(valor, dec)]
    if re.fullmatch(r'\d{1,3},\d{3}', crudo):
        candidatos.append((float(crudo.replace(',', '')), 0))
    return any(abs(s - v) <= 0.5 * 10**-d + 1e-9 for v, d in candidatos for s in fuente)


def verificar_narrativa(texto: str, indicadores: dict[str, Any]) -> dict[str, Any]:
    """Verifica una narrativa contra los indicadores de los que se generó.

    Args:
        texto: Narrativa generada por el modelo.
        indicadores: Indicadores agregados enviados al modelo.

    Returns:
        Dict con `cifras_total`, `cifras_respaldadas`, `cifras_sin_respaldo` (texto crudo de
        cada cifra no respaldada) y `alertas_coherencia` (lista de mensajes en español).
    """
    fuente = list(numeros_de(indicadores))
    todas = list(cifras_del_texto(texto))
    sin_respaldo = [c for c, v, d in todas if not _coincide(c, v, d, fuente)]

    alertas: list[str] = []
    if len(texto.strip()) < _MINIMO_CARACTERES:
        alertas.append('Texto demasiado corto para ser una narrativa utilizable.')
    if _PRESCRIPTIVO.search(texto):
        alertas.append(
            'Lenguaje prescriptivo: la narrativa es descriptiva y no debe recomendar tratamientos.'
        )
    if _CAUSAL.search(texto):
        alertas.append(
            'Lenguaje causal: un análisis descriptivo no permite afirmar relaciones de causa.'
        )
    if _IDENTIFICADOR.search(texto):
        alertas.append('Posible identificador de persona (número de 7 o más dígitos).')
    permitidos = _codigos_de(indicadores)
    for codigo in sorted(set(_CODIGO_CIE10.findall(texto.upper())) - permitidos):
        alertas.append(f'El código CIE-10 {codigo} no figura en los indicadores de origen.')

    return {
        'cifras_total': len(todas),
        'cifras_respaldadas': len(todas) - len(sin_respaldo),
        'cifras_sin_respaldo': sin_respaldo,
        'alertas_coherencia': alertas,
    }
