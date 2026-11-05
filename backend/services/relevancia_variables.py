"""Índice cuantitativo de relevancia bibliográfica de las variables (observaciones 1 y 2).

La selección de variables de la plataforma se apoyaba en tres criterios cualitativos. Este módulo
cuantifica el primero (frecuencia en la literatura revisada) de forma reproducible:

    f_v = k_v / N          k_v = artículos que reportan la variable v, N = artículos revisados
    IC 95 % de Wilson para f_v (Wilson, 1927; Brown, Cai y DasGupta, 2001)
    puntaje_v = límite inferior del IC de Wilson, que penaliza las frecuencias estimadas con poca
                evidencia (ordenar por la proporción cruda trata igual 1/3 que 10/30)

Además se registra en cuáles fichas (549, 550) existe la variable, para separar «relevante en la
literatura» de «disponible para analizar».

Alcance y límite: mide con qué frecuencia la literatura reporta la variable. NO mide su asociación
estadística con la morbilidad o la mortalidad materna (eso exige datos reales de casos y un modelo
analítico, fuera del alcance descriptivo del proyecto).
"""

import csv
from math import sqrt
from pathlib import Path
from typing import Any

Z_95 = 1.959963984540054  # cuantil 0,975 de la normal estándar


def intervalo_wilson(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de confianza de Wilson para una proporción k/n.

    Args:
        k: Éxitos (artículos que reportan la variable).
        n: Ensayos (artículos revisados); debe ser mayor que cero.
        z: Cuantil de la normal (1,96 para 95 %).

    Returns:
        Tupla (límite inferior, límite superior), siempre dentro de [0, 1].

    Raises:
        ValueError: Si n no es positivo o k está fuera de [0, n].
    """
    if n <= 0 or not 0 <= k <= n:
        raise ValueError('Se requiere n > 0 y 0 <= k <= n.')
    p = k / n
    z2 = z * z
    centro = (p + z2 / (2 * n)) / (1 + z2 / n)
    mitad = z * sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return max(0.0, centro - mitad), min(1.0, centro + mitad)


def leer_variables(ruta: Path) -> list[dict[str, Any]]:
    """Lee el CSV variable→artículos (Tabla 1 del artículo) y separa la lista de artículos."""
    with Path(ruta).open(encoding='utf-8', newline='') as fh:
        filas = list(csv.DictReader(fh))
    for fila in filas:
        fila['n_articulos'] = int(fila['n_articulos'])
        fila['disponible_549'] = int(fila['disponible_549'])
        fila['disponible_550'] = int(fila['disponible_550'])
        fila['articulos'] = [a.strip() for a in fila['articulos'].split(';')]
    return filas


def calcular_relevancia(filas: list[dict[str, Any]], total_articulos: int) -> list[dict[str, Any]]:
    """Calcula frecuencia, IC de Wilson y posición de cada variable.

    Args:
        filas: Variables con `variable`, `n_articulos`, `disponible_549` y `disponible_550`.
        total_articulos: N, artículos revisados (30 en el estudio).

    Returns:
        Las mismas filas con `frecuencia`, `ic_bajo`, `ic_alto`, `disponible_en` y `posicion`,
        ordenadas de mayor a menor límite inferior de Wilson.
    """
    resultado = []
    for fila in filas:
        k = fila['n_articulos']
        bajo, alto = intervalo_wilson(k, total_articulos)
        if fila['disponible_549'] and fila['disponible_550']:
            donde = 'ambos'
        elif fila['disponible_549']:
            donde = '549'
        elif fila['disponible_550']:
            donde = '550'
        else:
            donde = 'ninguno'
        resultado.append(
            {
                **fila,
                'frecuencia': round(k / total_articulos, 4),
                'ic_bajo': round(bajo, 4),
                'ic_alto': round(alto, 4),
                'disponible_en': donde,
            }
        )
    resultado.sort(key=lambda r: (-r['ic_bajo'], -r['n_articulos'], r['variable']))
    for i, fila in enumerate(resultado, start=1):
        fila['posicion'] = i
    return resultado
