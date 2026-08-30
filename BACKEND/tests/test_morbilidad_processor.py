"""Tests de regresión sobre MorbilidadProcessor (código existente, sin tests previos)."""

from services._morbilidad_processor import MorbilidadProcessor
from tests.fixtures_sivigila import df_morbilidad_ejemplo


def test_calcular_estadisticas_basicas_con_datos_sinteticos():
    """Debe contar el total de casos del DataFrame sintético."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    stats = p.calcular_estadisticas_basicas()
    assert stats["total_casos"] == 6


def test_analizar_tiempo_remision_calcula_boxplot():
    """Debe calcular min/max y total del tiempo de remisión."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_tiempo_remision()
    assert resultado["total"] == 6
    assert resultado["min"] == 0.5
    assert resultado["max"] == 6.0


def test_clustering_perfiles_morbilidad_no_truena_con_datos_suficientes():
    """El clustering debe ejecutarse con 2 clusters sobre datos suficientes."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.clustering_perfiles_morbilidad(n_clusters=2)
    assert resultado["n_clusters"] == 2
    assert len(resultado["cluster_profiles"]) == 2


def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 6, 0]
    assert resultado["total"] == 6
