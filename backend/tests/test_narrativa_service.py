"""Tests de narrativa_service: cache hit/miss, regenerar, filtros_hash."""

from datetime import datetime, timezone

from db.models_sqlalchemy import Analisis, NarrativaIA
from services.narrativa_service import (
    calcular_filtros_hash,
    extraer_indicadores_para_narrativa,
    obtener_narrativa,
)


def _crear_analisis(db_session) -> Analisis:
    analisis = Analisis(
        tipo="mortalidad",
        nombre_archivo="test.xlsx",
        archivo_hash="abc123",
        archivo="media/test.xlsx",
        fecha_carga=datetime.now(timezone.utc),
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    return analisis


def test_calcular_filtros_hash_distingue_filtros_distintos():
    """Filtros distintos deben producir hashes distintos."""
    hash1 = calcular_filtros_hash({"year": "2026", "month": None})
    hash2 = calcular_filtros_hash({"year": "2025", "month": None})
    assert hash1 != hash2


def test_calcular_filtros_hash_es_estable_para_mismos_filtros():
    """Los mismos filtros deben producir siempre el mismo hash."""
    hash1 = calcular_filtros_hash({"year": "2026", "month": "05"})
    hash2 = calcular_filtros_hash({"year": "2026", "month": "05"})
    assert hash1 == hash2


def test_obtener_narrativa_usa_cache_si_existe(db_session, mocker):
    """Si hay registro cacheado, no debe llamarse a IA-SERVICE."""
    analisis = _crear_analisis(db_session)
    filtros_hash = calcular_filtros_hash({"year": None, "month": None})
    db_session.add(
        NarrativaIA(
            analisis_id=analisis.id,
            tipo_narrativa="resumen_ejecutivo",
            filtros_hash=filtros_hash,
            contenido="Narrativa cacheada.",
            modelo="qwen2.5",
            generado_en=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    mock_ia_client = mocker.patch("services.narrativa_service.ia_client.generar_narrativa")

    resultado = obtener_narrativa(
        db_session,
        analisis,
        "resumen_ejecutivo",
        indicadores={"total_casos": 99},
        filtros={"year": None, "month": None},
        regenerar=False,
    )

    assert resultado["narrativa"] == "Narrativa cacheada."
    assert resultado["desde_cache"] is True
    mock_ia_client.assert_not_called()


def test_obtener_narrativa_llama_ia_client_si_no_hay_cache(db_session, mocker):
    """Sin cache, debe delegar en ia_client y devolver el texto nuevo."""
    analisis = _crear_analisis(db_session)
    mock_ia_client = mocker.patch(
        "services.narrativa_service.ia_client.generar_narrativa",
        return_value={"narrativa": "Narrativa nueva.", "modelo": "qwen2.5"},
    )

    resultado = obtener_narrativa(
        db_session,
        analisis,
        "resumen_ejecutivo",
        indicadores={"total_casos": 10},
        filtros={"year": None, "month": None},
        regenerar=False,
    )

    assert resultado["narrativa"] == "Narrativa nueva."
    assert resultado["modelo"] == "qwen2.5"
    assert resultado["desde_cache"] is False
    mock_ia_client.assert_called_once_with("resumen_ejecutivo", "mortalidad", {"total_casos": 10})


def test_obtener_narrativa_regenerar_llama_ia_client_aunque_haya_cache(db_session, mocker):
    """regenerar=True debe forzar la llamada a IA-SERVICE ignorando la cache."""
    analisis = _crear_analisis(db_session)
    filtros_hash = calcular_filtros_hash({"year": None, "month": None})
    db_session.add(
        NarrativaIA(
            analisis_id=analisis.id,
            tipo_narrativa="resumen_ejecutivo",
            filtros_hash=filtros_hash,
            contenido="Narrativa vieja.",
            modelo="qwen2.5",
            generado_en=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    mock_ia_client = mocker.patch(
        "services.narrativa_service.ia_client.generar_narrativa",
        return_value={"narrativa": "Narrativa regenerada.", "modelo": "qwen2.5"},
    )

    resultado = obtener_narrativa(
        db_session,
        analisis,
        "resumen_ejecutivo",
        indicadores={"total_casos": 10},
        filtros={"year": None, "month": None},
        regenerar=True,
    )

    assert resultado["narrativa"] == "Narrativa regenerada."
    assert resultado["desde_cache"] is False
    mock_ia_client.assert_called_once()


def test_extraer_indicadores_clustering_excluye_arrays_por_registro():
    """El payload de clustering no debe incluir arrays por-registro (pca, clusters)."""
    clustering_resultado = {
        "n_clusters": 2,
        "n_samples": 50,
        "features_used": ["Edad"],
        "cluster_sizes": [30, 20],
        "cluster_profiles": [{"cluster_id": 0, "size": 30}],
        "pca_2d": {"x": [1, 2, 3], "y": [4, 5, 6]},
        "clusters": [0, 1, 0],
    }
    resultado = extraer_indicadores_para_narrativa("clustering", None, clustering_resultado)
    assert "pca_2d" not in resultado
    assert "clusters" not in resultado
    assert resultado["n_clusters"] == 2
    assert resultado["cluster_sizes"] == [30, 20]


def test_extraer_indicadores_tipo_invalido_lanza_valueerror():
    """Un tipo de narrativa desconocido debe lanzar ValueError."""
    try:
        extraer_indicadores_para_narrativa("no_existe", {}, None)
        assert False, "Debió lanzar ValueError"
    except ValueError:
        pass
