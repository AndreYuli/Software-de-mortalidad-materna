"""Validadores estructurales y de columnas."""

import re
import unicodedata
from typing import Any

from utils.text_utils import clean_text


def _normalizar_encabezado(valor: str) -> str:
    """Normaliza un encabezado de columna Excel para comparación tolerante.

    Quita tildes, convierte a minúsculas, reemplaza variantes de 'N°/No.'
    y elimina caracteres no alfanuméricos.

    Args:
        valor: Texto del encabezado.

    Returns:
        Cadena normalizada apta para comparación fuzzy.
    """
    texto = str(valor or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = texto.replace('n°', 'n ').replace('nº', 'n ').replace('no.', 'n ').replace('no ', 'n ')
    texto = re.sub(r'[^a-z0-9]+', ' ', texto)
    resultado: str = ' '.join(texto.split())
    return resultado


def _require_text(value: Any, nombre_campo: str, numero_fila: int) -> str:
    """Extrae texto obligatorio o lanza ValueError si está vacío.

    Args:
        value: Valor de celda.
        nombre_campo: Nombre del campo para el mensaje de error.
        numero_fila: Número de fila Excel para el mensaje de error.

    Returns:
        Texto limpio.

    Raises:
        ValueError: Si el valor está vacío o es None.
    """
    resultado = clean_text(value)
    if resultado is None:
        raise ValueError(f'Fila {numero_fila}: el campo {nombre_campo} es obligatorio.')
    return resultado


def verificar_columnas_faltantes(requeridas: list[str], disponibles: list[str]) -> list[str]:
    """Devuelve las columnas requeridas que no están en la lista disponible.

    Args:
        requeridas: Columnas que deben existir.
        disponibles: Columnas presentes en el archivo.

    Returns:
        Lista de columnas ausentes; vacía si no falta ninguna.
    """
    disponibles_set = set(disponibles)
    resultado: list[str] = [col for col in requeridas if col not in disponibles_set]
    return resultado
