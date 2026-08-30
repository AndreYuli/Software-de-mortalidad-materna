"""Clase base común para los procesadores de datos estadísticos."""

from typing import Any

import pandas as pd


class ProcesadorBase:
    """Clase base con utilidades compartidas para procesamiento de datos."""

    def __init__(self, df: pd.DataFrame):
        """Inicializa el procesador con el DataFrame.

        Args:
            df: DataFrame con datos.
        """
        self.df = df.copy()

    def _calcular_promedio_edad(self, stats: dict[str, Any]) -> None:
        """Calcula el promedio de edad si la columna existe y lo añade a stats.

        Args:
            stats: Diccionario de estadísticas a actualizar.
        """
        if "Edad" in self.df.columns:
            edades = self.df["Edad"].dropna()
            if not edades.empty:
                stats["edad_promedio"] = float(edades.mean())

    def analizar_obstetrico_por_edad(self, variables: list[tuple[str, str]]) -> dict[str, Any]:
        """Cruza variables obstétricas con grupos de edad para detectar patrones.

        Args:
            variables: Lista de tuplas (columna_df, nombre_legible).

        Returns:
            Dict con histograma de variables obstétricas por grupo de edad.
        """
        grupos = [
            {"label": "<20", "min": 0, "max": 19},
            {"label": "20-29", "min": 20, "max": 29},
            {"label": "30-39", "min": 30, "max": 39},
            {"label": "≥40", "min": 40, "max": 120},
        ]
        tiene_edad = "Edad" in self.df.columns
        resultado: dict[str, Any] = {}
        for col, nombre in variables:
            if col not in self.df.columns:
                continue
            serie_raw = pd.to_numeric(self.df[col], errors="coerce")
            serie = serie_raw.dropna()
            if len(serie) < 2:
                continue
            max_val = min(int(serie.max()), 10)
            eje: list[int] = list(range(0, max_val + 1))
            por_edad: dict[str, Any] = {}
            if tiene_edad:
                edades = pd.to_numeric(self.df["Edad"], errors="coerce")
                for g in grupos:
                    sub = pd.to_numeric(
                        self.df.loc[(edades >= g["min"]) & (edades <= g["max"]), col],
                        errors="coerce",
                    ).dropna()
                    if len(sub) > 0:
                        por_edad[g["label"]] = [int((sub == v).sum()) for v in eje]
            resultado[col] = {
                "nombre": nombre,
                "valores_eje": eje,
                "conteos_total": [int((serie == v).sum()) for v in eje],
                "por_edad": por_edad,
                "promedio": float(serie.mean()),
                "total": int(len(serie)),
            }
        return resultado

    def _analizar_causas_cie10(self, columna: str, top_n: int) -> dict[str, Any]:
        """Identifica las causas más frecuentes codificadas en CIE-10 de una columna.

        Args:
            columna: Nombre de la columna con el código CIE-10 de la causa.
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas (código, casos, porcentaje) y
            total_causas_unicas. Dict vacío si la columna no existe.
        """
        resultado: dict[str, Any] = {}
        if columna not in self.df.columns:
            return resultado
        total_casos = len(self.df)
        causas = self.df[columna].value_counts().head(top_n)
        top_causas: list[dict[str, Any]] = [
            {
                "codigo": str(k),
                "casos": int(v),
                "porcentaje": float(v / total_casos * 100) if total_casos > 0 else 0.0,
            }
            for k, v in causas.items()
        ]
        resultado = {
            "top_causas": top_causas,
            "total_causas_unicas": int(self.df[columna].nunique()),
        }
        return resultado

    def analizar_distribucion_edad_riesgo(self) -> dict[str, Any]:
        """Agrupa los casos por los cortes de edad de mayor riesgo obstétrico.

        Los cortes (<19, 19-34, ≥35 años) son los definidos por la experta de
        dominio para priorizar el seguimiento de los extremos de edad
        materna, y son distintos de los 4 grupos usados en
        `analizar_obstetrico_por_edad` (que sirven para cruces con otras
        variables obstétricas, no para esta distribución simple).

        Returns:
            Dict con 'labels' (nombres de los 3 grupos), 'valores' (conteo
            de casos por grupo) y 'total' (casos con edad registrada). Dict
            vacío si no hay columna 'Edad' o no hay datos válidos.
        """
        resultado: dict[str, Any] = {}
        if "Edad" not in self.df.columns:
            return resultado
        edades = pd.to_numeric(self.df["Edad"], errors="coerce").dropna()
        if edades.empty:
            return resultado

        grupos = [
            {"label": "<19 años", "min": 0, "max": 18},
            {"label": "19-34 años", "min": 19, "max": 34},
            {"label": "≥35 años", "min": 35, "max": 120},
        ]
        valores = [int(((edades >= g["min"]) & (edades <= g["max"])).sum()) for g in grupos]
        resultado = {
            "labels": [g["label"] for g in grupos],
            "valores": valores,
            "total": int(len(edades)),
        }
        return resultado
