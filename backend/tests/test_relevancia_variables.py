"""Pruebas del índice de relevancia de variables (observaciones 1 y 2 de la asesora)."""

import csv
from math import isclose
from pathlib import Path

import pytest

from services.relevancia_variables import (
    calcular_relevancia,
    intervalo_wilson,
    leer_variables,
)

CSV = (
    Path(__file__).resolve().parents[2]
    / 'docs'
    / 'relevancia_variables'
    / 'variables_literatura.csv'
)


def test_wilson_coincide_con_valor_de_referencia():
    """21 de 30 artículos: IC 95 % de Wilson = (0,5212; 0,8335), fórmula cerrada."""
    bajo, alto = intervalo_wilson(21, 30)
    assert isclose(bajo, 0.5212, abs_tol=5e-4)
    assert isclose(alto, 0.8335, abs_tol=5e-4)


@pytest.mark.parametrize(('k', 'n'), [(0, 30), (30, 30), (1, 30)])
def test_wilson_se_mantiene_en_cero_uno_en_los_extremos(k, n):
    """A diferencia de Wald, nunca sale del intervalo [0, 1] ni colapsa en k=0 o k=n."""
    bajo, alto = intervalo_wilson(k, n)
    assert 0 <= bajo <= k / n + 1e-12
    assert k / n - 1e-12 <= alto <= 1
    assert alto > bajo


def test_wilson_rechaza_entradas_invalidas():
    """Con k fuera de [0, n] o n no positivo se lanza ValueError."""
    with pytest.raises(ValueError):
        intervalo_wilson(31, 30)
    with pytest.raises(ValueError):
        intervalo_wilson(1, 0)


def test_ranking_ordena_por_limite_inferior_y_marca_disponibilidad():
    """Se ordena por el límite inferior de Wilson; la disponibilidad no altera la frecuencia."""
    filas = [
        {'variable': 'A', 'n_articulos': 3, 'disponible_549': 1, 'disponible_550': 0},
        {'variable': 'B', 'n_articulos': 21, 'disponible_549': 1, 'disponible_550': 1},
        {'variable': 'C', 'n_articulos': 7, 'disponible_549': 0, 'disponible_550': 0},
    ]
    res = calcular_relevancia(filas, total_articulos=30)
    assert [r['variable'] for r in res] == ['B', 'C', 'A']
    assert res[0]['posicion'] == 1 and res[0]['frecuencia'] == 0.7
    assert res[0]['disponible_en'] == 'ambos'
    assert res[1]['disponible_en'] == 'ninguno'
    assert res[2]['disponible_en'] == '549'


def test_datos_reales_tabla1_son_trazables():
    """Cada variable de la Tabla 1 lista tantos artículos como indica su conteo (trazabilidad)."""
    filas = leer_variables(CSV)
    assert len(filas) == 20
    for fila in filas:
        assert len(fila['articulos']) == fila['n_articulos'], fila['variable']
        assert len(set(fila['articulos'])) == fila['n_articulos'], fila['variable']


def test_resultado_sobre_datos_reales_de_la_tabla_1():
    """Edad es la más frecuente (21/30) y las variables sin ficha quedan marcadas 'ninguno'."""
    res = calcular_relevancia(leer_variables(CSV), total_articulos=30)
    assert res[0]['variable'].startswith('Edad de la mujer') and res[0]['n_articulos'] == 21
    por_nombre = {r['variable']: r for r in res}
    assert por_nombre['Ingresos del hogar']['disponible_en'] == 'ninguno'
    assert por_nombre['Nivel educativo de la mujer']['disponible_en'] == '550'
    with CSV.open(encoding='utf-8') as fh:
        assert next(csv.reader(fh))[0] == 'factor'
