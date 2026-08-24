"""Utilidades para la construcción de grafos Sankey."""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class SankeyBuilder:
    """Constructor de visualizaciones de tipo Grafo Sankey a partir de DataFrames."""

    def __init__(self, df: pd.DataFrame):
        """Inicializa el constructor de Sankey.

        Args:
            df: DataFrame con los datos de flujo.
        """
        self.df = df.copy()

    def analizar_sankey_flujo(
        self,
        col_origen_keyword: str,
        col_medio_keyword: str,
        col_destino_keyword: str,
        destino_mapping: dict[int, str] | None = None,
        prefix_origen: str = "[Parto]",
        prefix_medio: str = "[Nivel]",
        prefix_destino: str = "[Muerte]",
    ) -> dict[str, Any]:
        """Extrae el flujo clínico a través de tres etapas.

        Args:
            col_origen_keyword: Keyword para buscar la columna de origen (ej. '9.4').
            col_medio_keyword: Keyword para buscar la columna intermedia (ej. '9.6').
            col_destino_keyword: Keyword para buscar la columna de destino (ej. '9.1').
            destino_mapping: Diccionario opcional para traducir códigos numéricos en destino.
            prefix_origen: Prefijo para las etiquetas de origen.
            prefix_medio: Prefijo para las etiquetas intermedias.
            prefix_destino: Prefijo para las etiquetas de destino.

        Returns:
            Dict con nodos y enlaces (source, target, value) del grafo Sankey.
        """
        real_col_origen = next((c for c in self.df.columns if col_origen_keyword in c), None)
        real_col_medio = next((c for c in self.df.columns if col_medio_keyword in c), None)
        real_col_destino = next((c for c in self.df.columns if col_destino_keyword in c), None)

        if not all([real_col_origen, real_col_medio, real_col_destino]):
            logger.warning(
                "SankeyBuilder: Columnas requeridas no encontradas: origen=%s, medio=%s, destino=%s",
                real_col_origen,
                real_col_medio,
                real_col_destino,
            )
            return {"nodos": [], "links": {"source": [], "target": [], "value": []}}

        col_origen: str = str(real_col_origen)
        col_medio: str = str(real_col_medio)
        col_destino: str = str(real_col_destino)

        df_flujo = self.df[[col_origen, col_medio, col_destino]].copy()

        if df_flujo.empty:
            logger.warning(
                "SankeyBuilder: DataFrame de flujo está vacío después de seleccionar columnas."
            )
            return {"nodos": [], "links": {"source": [], "target": [], "value": []}}

        valores_desconocidos = {"nan", "None", "", "Sin dato", "none", "null"}

        def _formatear_valor(valor: Any) -> str:
            val_str = str(valor).strip() if valor is not None else ""
            if val_str in valores_desconocidos or not val_str:
                return "Desconocido"
            return val_str

        def _etiqueta_destino(valor: Any) -> str:
            val_str = _formatear_valor(valor)
            if val_str == "Desconocido":
                return "Desconocido"
            if destino_mapping:
                try:
                    num_val = int(float(val_str))
                    if num_val in destino_mapping:
                        return destino_mapping[num_val]
                except (ValueError, TypeError):
                    pass
            return val_str

        for col in [col_origen, col_medio]:
            df_flujo[col] = df_flujo[col].apply(_formatear_valor)
        df_flujo[col_destino] = df_flujo[col_destino].apply(_etiqueta_destino)

        nodos_origen = [f"{prefix_origen} {x}" for x in df_flujo[col_origen].unique()]
        nodos_medio = [f"{prefix_medio} {x}" for x in df_flujo[col_medio].unique()]
        nodos_destino = [f"{prefix_destino} {x}" for x in df_flujo[col_destino].unique()]

        nodos = list(dict.fromkeys(nodos_origen + nodos_medio + nodos_destino))
        nodo_a_idx = {n: i for i, n in enumerate(nodos)}

        links_source, links_target, links_value = [], [], []

        flujo_1 = df_flujo.groupby([col_origen, col_medio]).size().reset_index(name="count")
        for _, row in flujo_1.iterrows():
            if row["count"] > 0:
                links_source.append(nodo_a_idx[f"{prefix_origen} {row[col_origen]}"])
                links_target.append(nodo_a_idx[f"{prefix_medio} {row[col_medio]}"])
                links_value.append(int(row["count"]))

        flujo_2 = df_flujo.groupby([col_medio, col_destino]).size().reset_index(name="count")
        for _, row in flujo_2.iterrows():
            if row["count"] > 0:
                links_source.append(nodo_a_idx[f"{prefix_medio} {row[col_medio]}"])
                links_target.append(nodo_a_idx[f"{prefix_destino} {row[col_destino]}"])
                links_value.append(int(row["count"]))

        return {
            "nodos": nodos,
            "links": {
                "source": links_source,
                "target": links_target,
                "value": links_value,
            },
        }
