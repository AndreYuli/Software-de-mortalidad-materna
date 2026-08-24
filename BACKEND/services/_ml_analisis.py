"""Operaciones de aprendizaje automático (ML) reutilizables sobre DataFrames."""

from typing import Any

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class AnalisisML:
    """Clase para ejecutar algoritmos de ML estandarizados."""

    def __init__(self, df: pd.DataFrame):
        """Inicializa el análisis ML con un DataFrame.

        Args:
            df: DataFrame ya preparado para análisis numérico.
        """
        self.df = df.copy()

    def clustering_kmeans(self, columnas: list[str], n_clusters: int = 3) -> dict[str, Any]:
        """Aplica K-means con escalado y proyección PCA 2D/3D.

        Args:
            columnas: Columnas numéricas a usar en el clustering.
            n_clusters: Número de clusters K-means.

        Returns:
            Dict con clusters, PCA 2D/3D y perfiles por cluster.

        Raises:
            ValueError: Si hay columnas o registros insuficientes.
        """
        cols = [c for c in columnas if c in self.df.columns]
        if len(cols) < 2:
            raise ValueError("Datos insuficientes para clustering")
        df_c = self.df[cols].dropna()
        if len(df_c) < n_clusters:
            raise ValueError(f"Se necesitan al menos {n_clusters} registros completos")

        x = StandardScaler().fit_transform(df_c)
        clusters = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(x)
        pca2 = PCA(n_components=2).fit_transform(x)
        pca3 = PCA(n_components=3).fit_transform(x)

        df_c = df_c.copy()
        df_c["cluster"] = clusters
        cluster_profiles: list[dict[str, Any]] = [
            {
                "cluster_id": i,
                "size": int((clusters == i).sum()),
                "features": {c: float(df_c[df_c["cluster"] == i][c].mean()) for c in cols},
            }
            for i in range(n_clusters)
        ]

        resultado: dict[str, Any] = {
            "n_clusters": n_clusters,
            "n_samples": len(df_c),
            "features_used": cols,
            "clusters": clusters.tolist(),
            "pca_2d": {"x": pca2[:, 0].tolist(), "y": pca2[:, 1].tolist()},
            "pca_3d": {
                "x": pca3[:, 0].tolist(),
                "y": pca3[:, 1].tolist(),
                "z": pca3[:, 2].tolist(),
            },
            "cluster_sizes": [int((clusters == i).sum()) for i in range(n_clusters)],
            "cluster_profiles": cluster_profiles,
        }
        return resultado

    def clustering_jerarquico(self, columnas: list[str], method: str = "ward") -> dict[str, Any]:
        """Calcula la matriz de enlace jerárquico para visualización de dendrograma.

        Args:
            columnas: Columnas a incluir en el análisis.
            method: Método de enlace scipy ('ward', 'complete', 'average').

        Returns:
            Dict con linkage_matrix, n_samples, method y features_used.

        Raises:
            ValueError: Si no hay columnas o registros suficientes para el clustering.
        """
        cols = [c for c in columnas if c in self.df.columns]
        if len(cols) < 2:
            raise ValueError("Datos insuficientes para clustering jerárquico")
        df_c = self.df[cols].dropna()
        if len(df_c) < 3:
            raise ValueError("Se necesitan al menos 3 registros")
        if len(df_c) > 100:
            df_c = df_c.sample(100, random_state=42)

        x = StandardScaler().fit_transform(df_c)
        linkage_matrix = linkage(x, method=method).tolist()
        resultado: dict[str, Any] = {
            "linkage_matrix": linkage_matrix,
            "n_samples": len(df_c),
            "method": method,
            "features_used": cols,
        }
        return resultado

    def heatmap_correlacion(
        self,
        max_columns: int = 10,
        keywords: list[str] | None = None,
    ) -> dict[str, Any]:
        """Calcula la matriz de correlación entre variables numéricas relevantes.

        Args:
            max_columns: Número máximo de columnas a considerar si no hay keywords.
            keywords: Palabras clave para filtrar las columnas numéricas.

        Returns:
            Dict con columns y correlation_matrix para renderizar el heatmap.

        Raises:
            ValueError: Si no hay suficientes columnas numéricas para correlacionar.
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) < 2:
            raise ValueError("Datos numéricos insuficientes")

        if keywords:
            relevant = [c for c in numeric_cols if any(kw.lower() in c.lower() for kw in keywords)]
        else:
            relevant = []

        if not relevant:
            relevant = numeric_cols[:max_columns]

        corr = self.df[relevant].corr()
        matriz: list[list[float]] = corr.values.tolist()
        resultado: dict[str, Any] = {
            "columns": relevant,
            "correlation_matrix": matriz,
            "values": matriz,
        }
        return resultado
