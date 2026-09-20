"""Procesador estadístico de datos de Mortalidad Materna (Evento SIVIGILA 550)."""

from typing import Any

import pandas as pd

from services._ml_analisis import AnalisisML
from services._sankey_builder import SankeyBuilder
from services.procesador_base import ProcesadorBase
from utils.type_parsers import es_valor_positivo

_COLUMNA_MOMENTO_MUERTE = '9.1 Momento de la muerte'
_COLUMNA_CAUSA_BASICA = '10.1 Causa básica CIE-10'
_VALORES_DESCONOCIDOS = {
    'nan': 'Desconocido',
    'None': 'Desconocido',
    '': 'Desconocido',
    'Sin dato': 'Desconocido',
}


class MortalidadProcessor(ProcesadorBase):
    """Procesador de datos de Mortalidad Materna (Evento SIVIGILA 550)."""

    MOMENTO_MUERTE = {
        1: 'Durante el embarazo',
        2: 'Durante el parto',
        3: 'Puerperio (hasta 42 días)',
        4: 'Tardía (43 días - 1 año)',
    }
    DEMORAS = {
        'demora_1': 'Reconocimiento del problema',
        'demora_2': 'Decisión de buscar atención',
        'demora_3': 'Acceso al centro de salud',
        'demora_4': 'Calidad de atención recibida',
    }

    def __init__(self, df: pd.DataFrame):
        """Inicializa el procesador con el DataFrame de mortalidad.

        Args:
            df: DataFrame con datos de mortalidad ya preparado.
        """
        super().__init__(df)
        self._limpiar()
        self._ml = AnalisisML(self.df)
        self._sankey = SankeyBuilder(self.df)

    def _limpiar(self) -> None:
        for col in [
            '6.5 Gestaciones',
            '6.6 Partos Vaginales',
            '6.7 Cesáreas',
            '6.8 Muertos',
            '6.9 Vivos',
            '6.10 Abortos',
            '8.1 No. CPN',
            '8.2 Semana inicio CPN',
            '9.2 Semana gestación',
        ]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        self.df = self.df.dropna(how='all')

    def calcular_estadisticas_basicas(self) -> dict[str, Any]:
        """Calcula los indicadores epidemiológicos básicos del conjunto de casos.

        Returns:
            Dict con total_casos, edad_promedio, gestaciones_promedio y controles_promedio.
        """
        stats: dict[str, Any] = {
            'total_casos': len(self.df),
            'edad_promedio': None,
            'gestaciones_promedio': None,
            'controles_prenatales_promedio': None,
        }
        self._calcular_promedio_edad(stats)

        if '6.5 Gestaciones' in self.df.columns:
            stats['gestaciones_promedio'] = float(self.df['6.5 Gestaciones'].mean())
        if '8.1 No. CPN' in self.df.columns:
            stats['controles_prenatales_promedio'] = float(self.df['8.1 No. CPN'].mean())
        return stats

    def analizar_momento_muerte(self) -> dict[str, Any]:
        """Distribuye los casos según el momento clínico en que ocurrió la muerte.

        Returns:
            Dict con distribución del momento de muerte y total.
        """
        resultado: dict[str, Any] = {}
        if _COLUMNA_MOMENTO_MUERTE in self.df.columns:
            dist = self.df[_COLUMNA_MOMENTO_MUERTE].value_counts().to_dict()
            distribucion: dict[str, int] = {
                self.MOMENTO_MUERTE.get(k, f'Código {k}'): int(v) for k, v in dist.items()
            }
            resultado = {
                'distribucion': distribucion,
                'total': int(sum(dist.values())),
            }
        return resultado

    def analizar_demoras(self) -> dict[str, Any]:
        """Mide la presencia de las cuatro demoras obstétricas en los casos registrados.

        Returns:
            Dict con proporción de casos para cada una de las cuatro demoras.
        """
        cols: dict[str, str] = {
            'demora_1': '10.3.1 Demora 1',
            'demora_2': '10.3.2 Demora 2',
            'demora_3': '10.3.3 Demora 3',
            'demora_4': '10.3.4 Demora 4',
        }
        resultado: dict[str, Any] = {}
        for key, col in cols.items():
            if col in self.df.columns:
                total = self.df[col].notna().sum()
                con_demora = self.df[col].apply(es_valor_positivo).sum()
                resultado[key] = {
                    'nombre': self.DEMORAS[key],
                    'casos_con_demora': int(con_demora),
                    'porcentaje': float(con_demora / total * 100) if total > 0 else 0,
                }
        return resultado

    def analizar_heatmap_causa_demoras(self, top_n: int = 10) -> dict[str, Any]:
        """Calcula una matriz de correlación (conteo) entre las Causas principales y las Demoras."""
        resultado: dict[str, Any] = {}
        if _COLUMNA_CAUSA_BASICA not in self.df.columns:
            return resultado

        cols_demoras = {
            'demora_1': '10.3.1 Demora 1',
            'demora_2': '10.3.2 Demora 2',
            'demora_3': '10.3.3 Demora 3',
            'demora_4': '10.3.4 Demora 4',
        }

        top_causas_series = self.df[_COLUMNA_CAUSA_BASICA].value_counts().head(top_n)
        top_causas = top_causas_series.index.tolist()
        df_top = self.df[self.df[_COLUMNA_CAUSA_BASICA].isin(top_causas)].copy()

        matriz = []
        for demora_key, demora_col in cols_demoras.items():
            fila = []
            if demora_col in df_top.columns:
                for causa in top_causas:
                    sub = df_top[df_top[_COLUMNA_CAUSA_BASICA] == causa][demora_col]
                    con_demora = sub.apply(es_valor_positivo).sum()
                    fila.append(int(con_demora))
            else:
                fila = [0] * len(top_causas)
            matriz.append(fila)

        resultado = {
            'causas': [str(c) for c in top_causas],
            'demoras': [self.DEMORAS[k] for k in cols_demoras.keys()],
            'valores': matriz,
        }
        return resultado

    def analizar_sankey_flujo(self) -> dict[str, Any]:
        """Extrae el flujo clínico: Tipo Parto -> Nivel Atención -> Momento Muerte.

        Returns:
            Dict con nodos y enlaces listos para visualizar un grafo Sankey.
        """
        return self._sankey.analizar_sankey_flujo(
            col_origen_keyword='9.4',
            col_medio_keyword='9.6',
            col_destino_keyword='9.1',
            destino_mapping=self.MOMENTO_MUERTE,
            prefix_origen='[Parto]',
            prefix_medio='[Nivel]',
            prefix_destino='[Muerte]',
        )

    def analizar_causas_cie10(self, top_n: int = 10) -> dict[str, Any]:
        """Identifica las causas de muerte más frecuentes codificadas en CIE-10.

        Args:
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas y total_causas_unicas.
        """
        return self._analizar_causas_cie10(_COLUMNA_CAUSA_BASICA, top_n)

    def analizar_obstetrico_por_edad(self) -> dict[str, Any]:
        """Cruza variables obstétricas con grupos de edad para detectar patrones.

        Returns:
            Dict con histograma de variables obstétricas por grupo de edad.
        """
        variables = [
            ('6.5 Gestaciones', 'Gestaciones'),
            ('6.6 Partos Vaginales', 'Partos vaginales'),
            ('6.7 Cesáreas', 'Cesáreas'),
            ('6.10 Abortos', 'Abortos'),
        ]
        return super().analizar_obstetrico_por_edad(variables)

    def clustering_factores_riesgo(self, n_clusters: int = 3) -> dict[str, Any]:
        """Aplica K-means para identificar perfiles de riesgo en la población estudiada.

        Args:
            n_clusters: Número de clusters K-means.

        Returns:
            Dict con clusters, PCA 2D/3D y perfiles por cluster.
        """
        cols = [
            '6.5 Gestaciones',
            '6.6 Partos Vaginales',
            '6.7 Cesáreas',
            '6.10 Abortos',
            '8.1 No. CPN',
            '9.2 Semana gestación',
        ]
        return self._ml.clustering_kmeans(columnas=cols, n_clusters=n_clusters)

    def clustering_jerarquico(self, method: str = 'ward') -> dict[str, Any]:
        """Calcula la matriz de enlace jerárquico para visualización de dendrograma.

        Args:
            method: Método de enlace scipy ('ward', 'complete', 'average').

        Returns:
            Dict con linkage_matrix, n_samples, method y features_used.
        """
        cols = [
            '6.5 Gestaciones',
            '6.6 Partos Vaginales',
            '6.7 Cesáreas',
            '8.1 No. CPN',
            '9.2 Semana gestación',
        ]
        return self._ml.clustering_jerarquico(columnas=cols, method=method)
