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
