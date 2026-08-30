"""Lógica de cálculo estadístico para análisis de mortalidad y morbilidad."""

from typing import Any

from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis
from services._analisis_excel import _canonizar_columnas_dataframe, preparar_dataframe_analisis
from services._analisis_filtros import (
    _calcular_distribucion_mensual,
    _enriquecer_df_con_fecha,
    _extraer_anos_disponibles,
    _filtrar_por_fecha,
)
from services._analisis_persistencia import _construir_df_desde_bd
from services._morbilidad_processor import MorbilidadProcessor
from services._mortalidad_processor import MortalidadProcessor
from utils.json_utils import _sanitize_json

_COLUMNAS_EXTRA = [
    ("5.1 Sitio de Defunción", "Distribución por Sitio de Defunción", "Sitio", "Casos"),
    ("6.3 Escolaridad", "Distribución por Nivel de Escolaridad", "Escolaridad", "Casos"),
    ("6.1 Convivencia", "Distribución por Convivencia", "Convivencia", "Casos"),
]


def calcular_completo(
    analisis: Analisis, year: str | None, month: str | None, db: Session
) -> dict[str, Any]:
    """Genera el análisis estadístico completo con filtros de fecha opcionales.

    Args:
        analisis: Instancia del modelo Analisis.
        year: Año para filtrar (opcional).
        month: Mes para filtrar (opcional).
        db: Sesión de base de datos.

    Returns:
        Dict con estadísticas, distribuciones y metadatos.

    Raises:
        FileNotFoundError: Si el archivo físico del análisis no existe.
        RuntimeError: Si falla el procesamiento de datos.
    """
    try:
        df_raw = _construir_df_desde_bd(db, analisis.tipo)
        if df_raw is None or df_raw.empty:
            raise ValueError(f"No hay datos en la base de datos para {analisis.tipo}")

        df = _canonizar_columnas_dataframe(df_raw, analisis.tipo)
        df, limpieza = preparar_dataframe_analisis(df)
        df = _enriquecer_df_con_fecha(db, df, analisis.tipo)
        anos = _extraer_anos_disponibles(df, analisis.tipo)
        df = _filtrar_por_fecha(df, analisis.tipo, year, month)

        meta: dict[str, Any] = {
            "id": analisis.id,
            "nombre_archivo": analisis.nombre_archivo,
            "fecha_carga": analisis.fecha_carga.isoformat(),
            "limpieza_datos": limpieza,
            "anos_disponibles": anos,
            "filtros_activos": {"year": year, "month": month},
            "distribucion_mensual": _calcular_distribucion_mensual(df, analisis.tipo),
        }

        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = {
                **meta,
                "tipo": "mortalidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "momento_muerte": p.analizar_momento_muerte(),
                "demoras": p.analizar_demoras(),
                "causas_cie10": p.analizar_causas_cie10(top_n=10),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "heatmap_demoras": p.analizar_heatmap_causa_demoras(top_n=20),
                "sankey_flujo": p.analizar_sankey_flujo(),
            }
        else:
            p = MorbilidadProcessor(df)
            resultado = {
                **meta,
                "tipo": "morbilidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "causas_cie10": p.analizar_causas_cie10(top_n=10),
                "criterios_inclusion": p.analizar_criterios_inclusion(),
                "momento_ocurrencia": p.analizar_momento_ocurrencia(),
                "institucion_referencia": p.analizar_institucion_referencia(),
                "tiempo_remision": p.analizar_tiempo_remision(),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "severidad_fallas": p.analizar_severidad_fallas(),
            }

        respuesta = _sanitize_json(resultado)
        return respuesta
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error al procesar el análisis: {exc}") from exc


def ejecutar_clustering(
    analisis: Analisis, tipo_clustering: str, n_clusters: int, db: Session
) -> dict[str, Any]:
    """Ejecuta clustering sobre los datos del análisis.

    Args:
        analisis: Instancia del modelo Analisis.
        tipo_clustering: 'kmeans' o 'jerarquico'.
        n_clusters: Número de clusters.
        db: Sesión de base de datos.

    Returns:
        Dict con resultado del clustering.

    Raises:
        FileNotFoundError: Si el archivo físico del análisis no existe.
        RuntimeError: Si falla el algoritmo de clustering.
    """
    try:
        df_raw = _construir_df_desde_bd(db, analisis.tipo)
        if df_raw is None or df_raw.empty:
            raise ValueError(f"No hay datos en la base de datos para {analisis.tipo}")

        df, limpieza = preparar_dataframe_analisis(df_raw)
        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = (
                p.clustering_jerarquico()
                if tipo_clustering == "jerarquico"
                else p.clustering_factores_riesgo(n_clusters=n_clusters)
            )
        else:
            resultado = MorbilidadProcessor(df).clustering_perfiles_morbilidad(
                n_clusters=n_clusters,
            )

        resultado.update(
            {
                "analisis_id": analisis.id,
                "tipo_analisis": analisis.tipo,
                "tipo_clustering": tipo_clustering,
                "limpieza_datos": limpieza,
            }
        )
        respuesta = _sanitize_json(resultado)
        return respuesta
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error en clustering: {exc}") from exc


def calcular_heatmap(analisis: Analisis, db: Session) -> dict[str, Any]:
    """Genera el heatmap de correlación para un análisis de morbilidad.

    Args:
        analisis: Instancia del modelo Analisis (debe ser de tipo morbilidad).
        db: Sesión de base de datos.

    Returns:
        Dict con datos del heatmap.

    Raises:
        FileNotFoundError: Si el archivo físico del análisis no existe.
        RuntimeError: Si falla el procesamiento.
    """
    try:
        df_raw = _construir_df_desde_bd(db, analisis.tipo)
        if df_raw is None or df_raw.empty:
            raise ValueError(f"No hay datos en la base de datos para {analisis.tipo}")

        df, limpieza = preparar_dataframe_analisis(df_raw)
        procesador = MorbilidadProcessor(df)
        resultado: dict[str, Any] = procesador.heatmap_correlacion()
        resultado.update({"analisis_id": analisis.id, "limpieza_datos": limpieza})
        respuesta = _sanitize_json(resultado)
        return respuesta
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error al generar heatmap: {exc}") from exc


def calcular_extra_columna(analisis: Analisis, columna_idx: int, db: Session) -> dict[str, Any]:
    """Devuelve la distribución de la primera columna extra disponible para mortalidad.

    Args:
        analisis: Instancia del modelo Analisis (debe ser de tipo mortalidad).
        columna_idx: Indice de la columna extra a consultar.
        db: Sesión de base de datos.

    Returns:
        Dict con {'chart': datos} si hay datos, o {'chart': None} si no.

    Raises:
        FileNotFoundError: Si el archivo físico del análisis no existe.
        RuntimeError: Si falla el procesamiento.
    """
    try:
        df_raw = _construir_df_desde_bd(db, analisis.tipo)
        if df_raw is None or df_raw.empty:
            raise ValueError(f"No hay datos en la base de datos para {analisis.tipo}")

        df = _canonizar_columnas_dataframe(df_raw, "mortalidad")
        df, _ = preparar_dataframe_analisis(df)

        chart: dict[str, Any] | None = None
        for col, titulo, x_title, y_title in _COLUMNAS_EXTRA:
            if col not in df.columns:
                continue
            serie = df[col].dropna().astype(str).str.strip()
            serie = serie[~serie.str.lower().isin({"", "nan", "none", "null"})]
            if serie.empty:
                continue
            conteos = serie.value_counts()
            chart = {
                "title": titulo,
                "subtitle": f"Total: {len(serie)} casos con dato registrado",
                "labels": conteos.index.tolist(),
                "values": [int(v) for v in conteos.values],
                "total": int(len(serie)),
                "xTitle": x_title,
                "yTitle": y_title,
                "orientation": "h",
            }
            break

        respuesta = {"chart": chart}
        return respuesta
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error al procesar extra columna: {exc}") from exc
