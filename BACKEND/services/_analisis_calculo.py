"""Lógica de cálculo estadístico para análisis de mortalidad y morbilidad."""

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis
from services._analisis_excel import _canonizar_columnas_dataframe, preparar_dataframe_analisis
from services._analisis_filtros import (
    _calcular_distribucion_mensual,
    _enriquecer_df_con_fecha,
    _extraer_anos_disponibles,
    _filtrar_por_fecha,
    _ultima_semana_reportada,
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
    analisis: Analisis,
    year: str | None,
    month: str | None,
    db: Session,
    week: str | None = None,
    day: str | None = None,
) -> dict[str, Any]:
    """Genera el análisis estadístico completo con filtros de fecha opcionales.

    Args:
        analisis: Instancia del modelo Analisis.
        year: Año para filtrar (opcional).
        month: Mes para filtrar (opcional).
        db: Sesión de base de datos.
        week: Semana ISO del año para filtrar (opcional).
        day: Día del mes para filtrar (opcional).

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
        ultima_semana = _ultima_semana_reportada(df, analisis.tipo)
        df = _filtrar_por_fecha(df, analisis.tipo, year, month, week, day)

        meta: dict[str, Any] = {
            "id": analisis.id,
            "nombre_archivo": analisis.nombre_archivo,
            "fecha_carga": analisis.fecha_carga.isoformat(),
            "limpieza_datos": limpieza,
            "anos_disponibles": anos,
            "ultima_semana_reportada": ultima_semana,
            "filtros_activos": {"year": year, "month": month, "week": week, "day": day},
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
                "distribucion_edad_gestacional": p.analizar_distribucion_edad_gestacional(),
                "distribucion_sociodemografica": p.analizar_distribucion_sociodemografica(),
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
                "distribucion_edad_gestacional": p.analizar_distribucion_edad_gestacional(),
                "distribucion_sociodemografica": p.analizar_distribucion_sociodemografica(),
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


def calcular_cruce(
    analisis: Analisis,
    var_socio: str,
    var_clinica: str,
    db: Session,
) -> dict[str, Any]:
    """Calcula un cruce entre una variable sociodemográfica y una clínica.

    Args:
        analisis: Instancia del modelo Analisis.
        var_socio: Variable sociodemográfica (clave corta).
        var_clinica: Variable clínica (clave corta).
        db: Sesión de base de datos.

    Returns:
        Dict con 'categorias_socio', 'categorias_clinica', 'matriz' (conteos)
        y 'total'.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si las variables no son válidas o no existen.
        RuntimeError: Si falla el procesamiento.
    """
    variables_socio = {
        "zona_residencia": "Zona de residencia",
        "poblacion_vulnerable": "Población vulnerable",
        "etnia": "Etnia",
        "tipo_afiliacion": "Tipo de afiliación",
    }

    variables_clinicas_mortalidad = {
        "gestaciones": "6.5 Gestaciones",
        "partos_vaginales": "6.6 Partos Vaginales",
        "cesareas": "6.7 Cesáreas",
        "tipo_parto": "9.4 Tipo de parto",
        "semana_gestacion_muerte": "9.2 Semana gestación",
    }

    variables_clinicas_morbilidad = {
        "num_gestaciones": "N° gestaciones",
        "partos_vaginales": "Partos vaginales",
        "cesareas": "Cesáreas",
        # Nota: _MORBILIDAD_DB_MAPPING renombra la vista
        # terminacion_gestacion -> "Momento ocurrencia", por eso el cruce
        # usa ese nombre de columna del DataFrame.
        "terminacion_gestacion": "Momento ocurrencia",
        "edad_gestacional_sem": "Edad gestacional ocurrencia (sem)",
        "falla_hepatica": "falla_hepatica",
        "falla_renal": "falla_renal",
        "falla_coagulacion": "falla_coagulacion",
    }

    col_socio = variables_socio.get(var_socio)
    if col_socio is None:
        raise ValueError(f"Variable sociodemográfica no válida: {var_socio}")

    if analisis.tipo == "mortalidad":
        col_clinica = variables_clinicas_mortalidad.get(var_clinica)
        if col_clinica is None:
            raise ValueError(f"Variable clínica no válida para mortalidad: {var_clinica}")
    else:
        col_clinica = variables_clinicas_morbilidad.get(var_clinica)
        if col_clinica is None:
            raise ValueError(f"Variable clínica no válida para morbilidad: {var_clinica}")

    try:
        df_raw = _construir_df_desde_bd(db, analisis.tipo)
        if df_raw is None or df_raw.empty:
            raise ValueError(f"No hay datos en la base de datos para {analisis.tipo}")

        df = _canonizar_columnas_dataframe(df_raw, analisis.tipo)
        df, _ = preparar_dataframe_analisis(df)

        if col_socio not in df.columns:
            raise ValueError(f"La columna '{col_socio}' no existe en los datos")
        if col_clinica not in df.columns:
            raise ValueError(f"La columna '{col_clinica}' no existe en los datos")

        def _agrupar_serie(valores: pd.Series, col: str) -> pd.Series:
            if "falla" in col:
                return valores.apply(lambda v: "Sí" if v == 1 or v is True else "No")
            if col in ("6.5 Gestaciones", "N° gestaciones"):
                bins = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 100]
                labels = ["1", "2", "3", "4", "5", "≥6"]
                return pd.cut(
                    pd.to_numeric(valores, errors="coerce"), bins=bins, labels=labels
                ).astype(str)
            if col in ("6.6 Partos Vaginales", "Partos vaginales"):
                bins = [-0.5, 0.5, 1.5, 2.5, 3.5, 100]
                labels = ["0", "1", "2", "3", "≥4"]
                return pd.cut(
                    pd.to_numeric(valores, errors="coerce"), bins=bins, labels=labels
                ).astype(str)
            if col in ("6.7 Cesáreas", "Cesáreas"):
                bins = [-0.5, 0.5, 1.5, 2.5, 100]
                labels = ["0", "1", "2", "≥3"]
                return pd.cut(
                    pd.to_numeric(valores, errors="coerce"), bins=bins, labels=labels
                ).astype(str)
            if col in ("9.2 Semana gestación", "Edad gestacional ocurrencia (sem)"):
                bins = [0, 28, 37, 42, 200]
                labels = ["<28 sem", "28-36 sem", "37-41 sem", "≥42 sem"]
                return pd.cut(
                    pd.to_numeric(valores, errors="coerce"), bins=bins, labels=labels, right=False
                ).astype(str)
            return valores.astype(str).str.strip()

        df_valid = df[[col_socio, col_clinica]].copy()
        df_valid = df_valid.dropna()
        df_valid = df_valid[
            ~df_valid[col_socio].astype(str).str.lower().isin({"", "nan", "none", "null"})
        ]
        df_valid = df_valid[
            ~df_valid[col_clinica].astype(str).str.lower().isin({"", "nan", "none", "null"})
        ]

        if df_valid.empty:
            return {
                "categorias_socio": [],
                "categorias_clinica": [],
                "matriz": [],
                "total": 0,
                "var_socio_label": var_socio,
                "var_clinica_label": var_clinica,
            }

        df_valid["socio_cat"] = _agrupar_serie(df_valid[col_socio], col_socio)
        df_valid["clinica_cat"] = _agrupar_serie(df_valid[col_clinica], col_clinica)
        df_valid = df_valid[
            ~df_valid["socio_cat"].str.lower().isin({"nan", "none", "null", ""})
            & ~df_valid["clinica_cat"].str.lower().isin({"nan", "none", "null", ""})
        ]

        if df_valid.empty:
            return {
                "categorias_socio": [],
                "categorias_clinica": [],
                "matriz": [],
                "total": 0,
                "var_socio_label": var_socio,
                "var_clinica_label": var_clinica,
            }

        cross = pd.crosstab(df_valid["socio_cat"], df_valid["clinica_cat"])

        categorias_socio = cross.index.tolist()
        categorias_clinica = cross.columns.tolist()
        matriz = [row.tolist() for _, row in cross.iterrows()]

        respuesta: dict[str, Any] = {
            "categorias_socio": [str(c) for c in categorias_socio],
            "categorias_clinica": [str(c) for c in categorias_clinica],
            "matriz": matriz,
            "total": int(df_valid.shape[0]),
            "var_socio_label": var_socio,
            "var_clinica_label": var_clinica,
        }
        return _sanitize_json(respuesta)
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Error al calcular el cruce: {exc}") from exc


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
