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

    def _find_col(self, candidates: list[str]) -> str | None:
        """Busca la primera columna presente en el DataFrame de entre las candidatas.

        Args:
            candidates: Lista de nombres de columna candidatos.

        Returns:
            Nombre de la primera columna encontrada, o None si ninguna existe.
        """
        return next((c for c in candidates if c in self.df.columns), None)

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

    def analizar_distribucion_edad_gestacional(self) -> dict[str, Any]:
        """Agrupa los casos por semanas de gestación en categorías clínicas estándar.

        Los cortes (<28, 28-36, 37-41, ≥42 semanas) distinguen partos
        pretérmino, a término y postérmino, categorías clínicas estándar
        para evaluar el riesgo asociado a la duración de la gestación.
        Mortalidad y morbilidad usan columnas de origen distintas, por eso
        se busca la primera que exista.

        Returns:
            Dict con 'labels' (nombres de los 4 grupos), 'valores' (conteo
            de casos por grupo) y 'total' (casos con semanas de gestación
            registradas). Dict vacío si no hay columna de semanas de
            gestación o no hay datos válidos.
        """
        columna = self._find_col(["9.2 Semana gestación", "Edad gestacional ocurrencia (sem)"])
        if columna is None:
            return {}
        semanas = pd.to_numeric(self.df[columna], errors="coerce").dropna()
        if semanas.empty:
            return {}

        grupos = [
            {"label": "<28 semanas", "min": 0, "max": 27},
            {"label": "28-36 semanas", "min": 28, "max": 36},
            {"label": "37-41 semanas", "min": 37, "max": 41},
            {"label": "≥42 semanas", "min": 42, "max": 99},
        ]
        valores = [int(((semanas >= g["min"]) & (semanas <= g["max"])).sum()) for g in grupos]
        return {
            "labels": [g["label"] for g in grupos],
            "valores": valores,
            "total": int(len(semanas)),
        }
