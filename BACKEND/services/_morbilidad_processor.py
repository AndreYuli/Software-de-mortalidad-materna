"""Procesador estadístico de datos de Morbilidad Materna Extrema (Evento SIVIGILA 549)."""

import unicodedata
from typing import Any

import pandas as pd

from services._ml_analisis import AnalisisML
from services.procesador_base import ProcesadorBase
from utils.type_parsers import es_valor_positivo

_KEYWORDS_FALLAS = (
    "cardiaca",
    "vascular",
    "renal",
    "hepatica",
    "metabolica",
    "cerebral",
    "respiratoria",
    "coagulacion",
)

_CORRECCIONES_NOMBRE = {
    "Cardaca": "Cardiaca",
    "Heptica": "Hepatica",
    "Metablica": "Metabolica",
    "Coagulacin": "Coagulacion",
}

_COLS_SEVERIDAD = [
    "Ingreso UCI",
    "Cirugía adicional",
    "Ciruga adicional",
    "Transfusión",
    "Transfusin",
]

_COLUMNA_CAUSA_PRINCIPAL = "Causa principal CIE-10"


def _normalizar(texto: str) -> str:
    """Elimina tildes y pasa a minúsculas.

    Args:
        texto: Texto original.

    Returns:
        Texto en minúsculas sin tildes.
    """
    return unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()


class MorbilidadProcessor(ProcesadorBase):
    """Procesador de datos de Morbilidad Materna Extrema (Evento SIVIGILA 549)."""

    MOMENTO_OCURRENCIA = {
        1: "Durante el embarazo",
        2: "Durante el parto",
        3: "Puerperio inmediato (0-7 días)",
        4: "Puerperio tardío (8-42 días)",
    }
    CRITERIOS_INCLUSION = {
        "Eclampsia": "Eclampsia",
        "Sepsis sistémica severa": "Sepsis",
        "Hemorragia obstétrica severa": "Hemorragia",
        "Preeclampsia": "Preeclampsia severa",
        "Ruptura uterina": "Ruptura uterina",
    }
    _INST_REF_COLS = [
        "Institución referencia 1",
        "Institucion referencia 1",
        "Institución de referencia 1",
        "Institucion de referencia 1",
    ]
    _TIEMPO_REM_COLS = [
        "Tiempo remisión (h)",
        "Tiempo remision (h)",
        "Tiempo remisión horas",
        "Tiempo remision horas",
    ]

    def __init__(self, df: pd.DataFrame):
        """Inicializa el procesador con el DataFrame de morbilidad.

        Args:
            df: DataFrame con datos de morbilidad ya preparado.
        """
        super().__init__(df)
        self._limpiar()
        self._ml = AnalisisML(self.df)

    def _limpiar(self) -> None:
        for col in [
            "N° gestaciones",
            "Partos vaginales",
            "Cesáreas",
            "Abortos",
            "N° controles prenatales",
            "Edad gestacional ocurrencia (sem)",
            "Total criterios",
            "Días estancia hospitalaria",
            "Días estancia UCI",
        ]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        self.df = self.df.dropna(how="all")

    def _find_col(self, candidates: list[str]) -> str | None:
        """Busca la primera columna presente en el DataFrame de entre las candidatas.

        Args:
            candidates: Lista de nombres de columna candidatos.

        Returns:
            Nombre de la primera columna encontrada, o None si ninguna existe.
        """
        return next((c for c in candidates if c in self.df.columns), None)

    def calcular_estadisticas_basicas(self) -> dict[str, Any]:
        """Calcula los indicadores epidemiológicos básicos del conjunto de casos.

        Returns:
            Dict con total_casos, edad_promedio, estancias y criterios promedio.
        """
        stats: dict[str, Any] = {
            "total_casos": len(self.df),
            "edad_promedio": None,
            "estancia_hospitalaria_promedio": None,
            "estancia_uci_promedio": None,
            "criterios_promedio": None,
        }
        self._calcular_promedio_edad(stats)

        for key, col in [
            ("estancia_hospitalaria_promedio", "Días estancia hospitalaria"),
            ("estancia_uci_promedio", "Días estancia UCI"),
            ("criterios_promedio", "Total criterios"),
        ]:
            if col in self.df.columns:
                stats[key] = float(self.df[col].mean())
        return stats

    def analizar_criterios_inclusion(self) -> dict[str, Any]:
        """Mide la frecuencia de cada criterio de inclusión de morbilidad materna extrema.

        Returns:
            Dict con casos y porcentaje por cada criterio de inclusión MME.
        """
        resultado: dict[str, Any] = {}
        for col, nombre in self.CRITERIOS_INCLUSION.items():
            if col in self.df.columns:
                total = self.df[col].notna().sum()
                casos = self.df[col].apply(es_valor_positivo).sum()
                resultado[col] = {
                    "nombre": nombre,
                    "casos": int(casos),
                    "porcentaje": float(casos / total * 100) if total > 0 else 0,
                }
        return resultado

    def analizar_momento_ocurrencia(self) -> dict[str, Any]:
        """Distribuye los casos según el momento clínico en que ocurrió el evento.

        Returns:
            Dict con distribución del momento de ocurrencia del evento.
        """
        resultado: dict[str, Any] = {}
        if "Momento ocurrencia" in self.df.columns:
            dist = self.df["Momento ocurrencia"].value_counts().to_dict()
            distribucion: dict[str, int] = {
                self.MOMENTO_OCURRENCIA.get(k, f"Código {k}"): int(v) for k, v in dist.items()
            }
            resultado = {"distribucion": distribucion}
        return resultado

    def analizar_institucion_referencia(self) -> dict[str, Any]:
        """Identifica las instituciones de referencia más frecuentes en los casos.

        Returns:
            Dict con top 15 instituciones de referencia y conteos, incluyendo severidad.
        """
        resultado: dict[str, Any] = {}
        col = self._find_col(self._INST_REF_COLS)
        if col is not None:
            serie = self.df[col].dropna().astype(str).str.strip()
            serie = serie[~serie.str.lower().isin({"", "nan", "none", "null", "sin dato"})]
            if not serie.empty:
                top = serie.value_counts().head(15)
                instituciones: list[str] = top.index.tolist()
                conteos: list[int] = [int(v) for v in top.values]

                col_uci = next(
                    (c for c in self.df.columns if "uci" in c.lower() and "ingreso" in c.lower()),
                    None,
                )
                if not col_uci:
                    col_uci = next((c for c in self.df.columns if "uci" in c.lower()), None)
                col_cirugia = next((c for c in self.df.columns if "cirug" in c.lower()), None)

                con_uci = []
                con_cirugia = []

                for inst in instituciones:
                    mask = self.df[col].astype(str).str.strip() == inst
                    c_uci = (
                        self.df.loc[mask, col_uci].apply(es_valor_positivo).sum() if col_uci else 0
                    )
                    c_cir = (
                        self.df.loc[mask, col_cirugia].apply(es_valor_positivo).sum()
                        if col_cirugia
                        else 0
                    )
                    con_uci.append(int(c_uci))
                    con_cirugia.append(int(c_cir))

                resultado = {
                    "instituciones": instituciones,
                    "conteos": conteos,
                    "con_uci": con_uci,
                    "con_cirugia": con_cirugia,
                    "total_con_dato": int(len(serie)),
                    "total_casos": int(len(self.df)),
                }
        return resultado

    def analizar_tiempo_remision(self) -> dict[str, Any]:
        """Analiza la distribución del tiempo de remisión entre instituciones en horas.

        Returns:
            Dict con estadísticas de boxplot del tiempo de remisión en horas.
        """
        resultado: dict[str, Any] = {}
        col = self._find_col(self._TIEMPO_REM_COLS)
        if col is not None:
            serie = pd.to_numeric(self.df[col], errors="coerce").dropna()
            serie = serie[serie >= 0]
            if len(serie) >= 3:
                valores: list[float] = serie.clip(upper=serie.quantile(0.99)).head(500).tolist()
                resultado = {
                    "valores": valores,
                    "min": float(serie.min()),
                    "q1": float(serie.quantile(0.25)),
                    "median": float(serie.median()),
                    "mean": float(serie.mean()),
                    "q3": float(serie.quantile(0.75)),
                    "max": float(serie.max()),
                    "total": int(len(serie)),
                }
        return resultado

    def analizar_causas_cie10(self, top_n: int = 10) -> dict[str, Any]:
        """Identifica las causas principales más frecuentes codificadas en CIE-10.

        Args:
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas y total_causas_unicas.
        """
        return self._analizar_causas_cie10(_COLUMNA_CAUSA_PRINCIPAL, top_n)

    def analizar_obstetrico_por_edad(self) -> dict[str, Any]:
        """Cruza variables obstétricas con grupos de edad para detectar patrones.

        Returns:
            Dict con histograma de variables obstétricas por grupo de edad.
        """
        variables = [
            ("N° gestaciones", "Gestaciones"),
            ("Partos vaginales", "Partos vaginales"),
            ("Cesáreas", "Cesáreas"),
            ("Abortos", "Abortos"),
        ]
        return super().analizar_obstetrico_por_edad(variables)

    def clustering_perfiles_morbilidad(self, n_clusters: int = 3) -> dict[str, Any]:
        """Aplica K-means para identificar perfiles clínicos en la población con MME.

        Args:
            n_clusters: Número de clusters K-means.

        Returns:
            Dict con clusters, PCA 2D/3D y perfiles por cluster.
        """
        cols = [
            "N° gestaciones",
            "Partos vaginales",
            "Cesáreas",
            "N° controles prenatales",
            "Edad gestacional ocurrencia (sem)",
            "Total criterios",
            "Días estancia hospitalaria",
        ]
        return self._ml.clustering_kmeans(columnas=cols, n_clusters=n_clusters)

    def heatmap_correlacion(self) -> dict[str, Any]:
        """Calcula la matriz de correlación entre variables numéricas relevantes.

        Returns:
            Dict con columns y correlation_matrix para renderizar el heatmap.
        """
        keywords = [
            "gestaciones",
            "Partos",
            "Cesáreas",
            "controles",
            "gestacional",
            "estancia",
            "criterios",
        ]
        return self._ml.heatmap_correlacion(max_columns=10, keywords=keywords)

    def analizar_severidad_fallas(self) -> dict[str, Any]:
        """Calcula indicadores de severidad y distribución de fallas orgánicas.

        Returns:
            Dict con fallas presentes y severidad global en los casos analizados.
        """
        fallas_presentes = {}
        for col in self.df.columns:
            if "falla" in col.lower() and any(k in _normalizar(col) for k in _KEYWORDS_FALLAS):
                nombre_limpio = col.title()
                for mal, bien in _CORRECCIONES_NOMBRE.items():
                    nombre_limpio = nombre_limpio.replace(mal, bien)
                casos = self.df[col].apply(es_valor_positivo).sum()
                fallas_presentes[col] = {"nombre": nombre_limpio, "casos": int(casos)}

        severidad = {}
        for col in self.df.columns:
            if any(k.lower() in col.lower() for k in _COLS_SEVERIDAD):
                nombre_limpio = self._etiqueta_severidad(col)
                casos = self.df[col].apply(es_valor_positivo).sum()
                if nombre_limpio not in severidad:
                    severidad[nombre_limpio] = {"nombre": nombre_limpio, "casos": int(casos)}
                else:
                    previos = severidad[nombre_limpio]["casos"]
                    severidad[nombre_limpio]["casos"] = max(previos, int(casos))

        resultado: dict[str, Any] = {
            "fallas": list(fallas_presentes.values()),
            "severidad": list(severidad.values()),
            "total_casos": len(self.df),
        }
        return resultado

    @staticmethod
    def _etiqueta_severidad(col: str) -> str:
        """Traduce el nombre de columna de severidad a su etiqueta legible.

        Args:
            col: Nombre de la columna del DataFrame.

        Returns:
            Etiqueta canónica ('Ingreso UCI', 'Cirugía Adicional' o 'Transfusión').
        """
        col_lower = col.lower()
        if "uci" in col_lower:
            return "Ingreso UCI"
        if "cirug" in col_lower:
            return "Cirugía Adicional"
        return "Transfusión"
