"""DataFrames sintéticos de ejemplo para tests de regresión de los processors."""

import pandas as pd


def df_mortalidad_ejemplo() -> pd.DataFrame:
    """Construye un DataFrame sintético de 6 casos de mortalidad con columnas SIVIGILA 550.

    Returns:
        DataFrame con columnas suficientes para ejercitar estadísticas básicas,
        momento de muerte, demoras, causas CIE-10 y clustering de factores de riesgo
        (requiere al menos 3 columnas candidatas para que el PCA 3D no falle).
    """
    return pd.DataFrame(
        {
            "Edad": [22, 31, 27, 19, 35, 24],
            "6.5 Gestaciones": [2, 3, 1, 1, 4, 2],
            "6.7 Cesáreas": [0, 1, 0, 1, 0, 1],
            "8.1 No. CPN": [4, 6, 2, 0, 8, 5],
            "9.1 Momento de la muerte": [1, 2, 3, 1, 4, 2],
            "9.4 Tipo de parto": ["Vaginal", "Cesárea", "Vaginal", "Cesárea", "Vaginal", "Cesárea"],
            "9.6 Nivel atención parto": [
                "Nivel 1",
                "Nivel 2",
                "Nivel 1",
                "Nivel 3",
                "Nivel 2",
                "Nivel 1",
            ],
            "10.1 Causa básica CIE-10": ["O14.1", "O72.1", "O14.1", "O99.4", "O72.1", "O14.1"],
            "10.3.1 Demora 1": [1, 0, 1, 1, 0, 0],
            "10.3.2 Demora 2": [1, 0, 0, 1, 0, 1],
            "10.3.3 Demora 3": [0, 0, 1, 1, 0, 0],
            "10.3.4 Demora 4": [1, 1, 0, 1, 0, 0],
        }
    )


def df_morbilidad_ejemplo() -> pd.DataFrame:
    """Construye un DataFrame sintético de 6 casos de morbilidad con columnas SIVIGILA 549.

    Returns:
        DataFrame con columnas suficientes para ejercitar estadísticas básicas,
        criterios de inclusión y tiempo de remisión.
    """
    return pd.DataFrame(
        {
            "Edad": [24, 29, 33, 20, 27, 31],
            "N° gestaciones": [1, 2, 3, 1, 2, 4],
            "Partos vaginales": [0, 1, 2, 0, 1, 3],
            "Cesáreas": [1, 0, 1, 1, 0, 0],
            "N° controles prenatales": [3, 5, 6, 1, 4, 7],
            "Edad gestacional ocurrencia (sem)": [32, 28, 36, 24, 30, 34],
            "Eclampsia": [1, 0, 0, 0, 1, 0],
            "Preeclampsia": [0, 1, 1, 0, 0, 1],
            "Total criterios": [1, 1, 2, 0, 1, 1],
            "Días estancia hospitalaria": [3, 5, 8, 2, 4, 6],
            "Tiempo remisión (h)": [2.5, 1.0, 4.0, 0.5, 3.0, 6.0],
        }
    )
