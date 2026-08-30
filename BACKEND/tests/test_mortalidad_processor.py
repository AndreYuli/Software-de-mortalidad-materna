"""Tests de regresión sobre MortalidadProcessor (código existente, sin tests previos)."""

from services._mortalidad_processor import MortalidadProcessor
from tests.fixtures_sivigila import df_mortalidad_ejemplo


def test_calcular_estadisticas_basicas_con_datos_sinteticos():
    """Debe calcular total de casos, edad y gestaciones promedio."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    stats = p.calcular_estadisticas_basicas()
    assert stats["total_casos"] == 6
    assert stats["edad_promedio"] == (22 + 31 + 27 + 19 + 35 + 24) / 6
    assert stats["gestaciones_promedio"] == (2 + 3 + 1 + 1 + 4 + 2) / 6


def test_analizar_momento_muerte_distribuye_correctamente():
    """La distribución de momento de muerte debe agrupar por categoría."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_momento_muerte()
    assert resultado["total"] == 6
    assert resultado["distribucion"]["Durante el embarazo"] == 2
    assert resultado["distribucion"]["Durante el parto"] == 2


def test_analizar_demoras_calcula_porcentajes():
    """Las demoras deben reportarse como casos y porcentaje."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_demoras()
    assert resultado["demora_1"]["casos_con_demora"] == 3
    assert resultado["demora_1"]["porcentaje"] == 50.0


def test_analizar_causas_cie10_top_causas():
    """El top de causas CIE-10 debe respetar top_n y los conteos."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_causas_cie10(top_n=5)
    assert resultado["total_causas_unicas"] == 3
    top = {c["codigo"]: c["casos"] for c in resultado["top_causas"]}
    assert top["O14.1"] == 3


def test_clustering_factores_riesgo_no_truena_con_datos_suficientes():
    """El clustering de factores de riesgo debe ejecutarse sin excepciones."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.clustering_factores_riesgo(n_clusters=2)
    assert resultado["n_clusters"] == 2
    assert resultado["n_samples"] > 0
    assert len(resultado["cluster_profiles"]) == 2


def test_analizar_sankey_flujo_genera_nodos_y_enlaces_con_prefijos():
    """El flujo Sankey debe generar nodos categorizados y enlaces válidos."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_sankey_flujo()
    assert "nodos" in resultado
    assert "links" in resultado
    assert len(resultado["nodos"]) > 0
    assert len(resultado["links"]["source"]) > 0
    assert (
        len(resultado["links"]["source"])
        == len(resultado["links"]["target"])
        == len(resultado["links"]["value"])
    )
    assert any(n.startswith("[Parto]") for n in resultado["nodos"])
    assert any(n.startswith("[Nivel]") for n in resultado["nodos"])
    assert any(n.startswith("[Muerte]") for n in resultado["nodos"])


def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 5, 1]
    assert resultado["total"] == 6
