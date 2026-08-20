"""Tests de regresión sobre MortalidadProcessor (código existente, sin tests previos)."""

from services._mortalidad_processor import MortalidadProcessor
from tests.fixtures_sivigila import df_mortalidad_ejemplo


def test_calcular_estadisticas_basicas_con_datos_sinteticos():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    stats = p.calcular_estadisticas_basicas()
    assert stats['total_casos'] == 6
    assert stats['edad_promedio'] == (22 + 31 + 27 + 19 + 35 + 24) / 6
    assert stats['gestaciones_promedio'] == (2 + 3 + 1 + 1 + 4 + 2) / 6


def test_analizar_momento_muerte_distribuye_correctamente():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_momento_muerte()
    assert resultado['total'] == 6
    assert resultado['distribucion']['Durante el embarazo'] == 2
    assert resultado['distribucion']['Durante el parto'] == 2


def test_analizar_demoras_calcula_porcentajes():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_demoras()
    assert resultado['demora_1']['casos_con_demora'] == 3
    assert resultado['demora_1']['porcentaje'] == 50.0


def test_analizar_causas_cie10_top_causas():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_causas_cie10(top_n=5)
    assert resultado['total_causas_unicas'] == 3
    top = {c['codigo']: c['casos'] for c in resultado['top_causas']}
    assert top['O14.1'] == 3


def test_clustering_factores_riesgo_no_truena_con_datos_suficientes():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.clustering_factores_riesgo(n_clusters=2)
    assert resultado['n_clusters'] == 2
    assert resultado['n_samples'] > 0
    assert len(resultado['cluster_profiles']) == 2
