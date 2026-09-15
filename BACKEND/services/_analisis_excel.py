"""Constantes de columnas y helpers de lectura de archivos Excel SIVIGILA."""

import logging
from typing import Any

import openpyxl
import pandas as pd

from utils.column_validators import _normalizar_encabezado
from utils.date_parsers import parse_fecha_robusta

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de columnas requeridas y alias
# ---------------------------------------------------------------------------

_COLUMNAS_MORTALIDAD = [
    "A. Nombres y Apellidos",
    "B. Tipo ID",
    "C. Número ID",
    "5.1 Sitio de Defunción",
    "6.1 Convivencia",
    "6.3 Escolaridad",
    "6.4 Regulación Fecundidad",
    "6.5 Gestaciones",
    "6.6 Partos Vaginales",
    "6.7 Cesáreas",
    "6.8 Muertos",
    "6.9 Vivos",
    "6.10 Abortos",
    "8.1 No. CPN",
    "8.2 Semana inicio CPN",
    "9.1 Momento de la muerte",
    "9.2 Semana gestación",
    "9.4 Tipo de parto",
    "10.1 Causa básica CIE-10",
    "10.3.1 Demora 1",
    "10.3.2 Demora 2",
    "10.3.3 Demora 3",
    "10.3.4 Demora 4",
    "Fecha de Nacimiento",
]

_COLUMNAS_MORBILIDAD = [
    "Nombres y apellidos",
    "Tipo de ID",
    "N° identificación",
    "N° gestaciones",
    "Partos vaginales",
    "Cesáreas",
    "Abortos",
    "N° controles prenatales",
    "Semanas inicio CPN",
    "Edad gestacional ocurrencia (sem)",
    "Momento ocurrencia",
    "Eclampsia",
    "Sepsis sistémica severa",
    "Hemorragia obstétrica severa",
    "Preeclampsia",
    "Ruptura uterina",
    "Ingreso UCI",
    "Cirugía adicional",
    "Transfusión",
    "Total criterios",
    "Causa principal CIE-10",
    "Días estancia hospitalaria",
    "Días estancia UCI",
    "Fecha de Nacimiento",
    "Fecha de egreso",
]

_COLUMNAS_REQUERIDAS = {
    "mortalidad": _COLUMNAS_MORTALIDAD,
    "morbilidad": _COLUMNAS_MORBILIDAD,
}

_ALIAS_COLUMNAS = {
    "morbilidad": {
        "Nombres y apellidos": ["Nombre y apellidos", "Nombres y Apellidos"],
        "Tipo de ID": [
            "Tipo ID",
            "Tipo identificación",
            "Tipo de identificación",
            "Tipo de documento",
            "Tipo documento",
        ],
        "N° identificación": [
            "No identificación",
            "Nro identificación",
            "Nº identificación",
            "Número identificación",
        ],
        "N° gestaciones": ["No gestaciones", "Nro gestaciones", "Nº gestaciones"],
        "N° controles prenatales": ["No controles prenatales", "Nro controles prenatales"],
        "Causa principal CIE-10": ["Causa principal cie10", "Causa principal CIE10"],
        "Días estancia hospitalaria": ["Dias estancia hospitalaria"],
        "Días estancia UCI": ["Dias estancia UCI"],
        "Fecha de Nacimiento": [
            "Fecha de nacimiento",
            "Fecha nacimiento",
            "Fecha de nacimiento (dd/mm/aaaa)",
            "Fecha nacimiento (dd/mm/aaaa)",
        ],
        "Fecha de egreso": [
            "Fecha egreso",
            "Fecha de egreso (dd/mm/aaaa)",
            "Fecha egreso (dd/mm/aaaa)",
        ],
        "Zona de residencia": ["Zona residencia", "Zona"],
        "Población vulnerable": [
            "Poblacion vulnerable",
            "Población vulnerable",
            "Poblacion vulnerable",
        ],
        "Etnia": ["Grupo étnico", "Grupo etnico", "Etnia"],
        "Tipo de afiliación": [
            "Tipo afiliación",
            "Tipo afiliacion",
            "Afiliación",
            "Afiliacion",
            "Régimen de afiliación",
            "Regimen de afiliacion",
        ],
    },
    "mortalidad": {
        "A. Nombres y Apellidos": [
            "Nombres y Apellidos",
            "Nombres y apellidos",
            "Nombre y apellidos",
        ],
        "B. Tipo ID": [
            "B. Tipo de ID",
            "B Tipo ID",
            "Tipo ID",
            "Tipo de ID",
            "Tipo de documento",
            "Tipo documento",
        ],
        "C. Número ID": [
            "C. Numero ID",
            "C Número ID",
            "Número ID",
            "Numero ID",
            "Numero de documento",
            "Número de documento",
        ],
        "5.1 Sitio de Defunción": [
            "5.1 Sitio de defuncion",
            "Sitio de Defunción",
            "Sitio de defuncion",
        ],
        "5.2 Fecha de defunción": [
            "5.2 Fecha defunción",
            "Fecha de defunción",
            "5.2 Fecha de defuncion (dd/mm/aaaa)",
            "5.2 Fecha de defuncion",
            "Fecha de defuncion",
        ],
        "6.1 Convivencia": ["6.1 convivencia", "Convivencia", "Convivencia paciente"],
        "6.3 Escolaridad": ["6.3 escolaridad", "Escolaridad"],
        "6.4 Regulación Fecundidad": [
            "6.4 Regulacion Fecundidad",
            "6.4 Regulación de la fecundidad",
            "Regulación Fecundidad",
            "Regulacion Fecundidad",
            "Regulación de Fecundidad",
            "Regulación de la fecundidad",
            "Regulacion de la fecundidad",
        ],
        "6.5 Gestaciones": ["6.5 gestaciones", "Gestaciones", "N° Gestaciones", "No Gestaciones"],
        "6.6 Partos Vaginales": ["6.6 partos vaginales", "Partos Vaginales", "Partos vaginales"],
        "6.7 Cesáreas": ["6.7 cesareas", "Cesáreas", "Cesareas"],
        "6.8 Muertos": ["6.8 muertos", "Muertos", "Hijos Muertos", "Nacidos muertos"],
        "6.9 Vivos": ["6.9 vivos", "Vivos", "Hijos Vivos"],
        "6.10 Abortos": ["6.10 abortos", "Abortos"],
        "8.1 No. CPN": [
            "8.1 N° CPN",
            "8.1 Nº CPN",
            "8.1 No CPN",
            "No. CPN",
            "N° CPN",
            "No CPN",
            "Controles prenatales",
        ],
        "8.2 Semana inicio CPN": [
            "8.2 semana inicio cpn",
            "Semana inicio CPN",
            "Semana de inicio CPN",
        ],
        "9.1 Momento de la muerte": [
            "9.1 momento de la muerte",
            "Momento de la muerte",
            "Momento muerte",
        ],
        "9.2 Semana gestación": [
            "9.2 semana gestacion",
            "9.2 Semana de gestación para la mortalidad materna",
            "Semana gestación",
            "Semana de gestacion",
            "Semana gestacion",
            "Semana de gestación para la mortalidad materna",
        ],
        "9.4 Tipo de parto": ["9.4 Tipo parto", "Tipo de parto", "Tipo parto"],
        "9.6 Nivel atención parto": [
            "9.6 Nivel de atención",
            "9.6 Nivel atencion parto",
            "9.6 Nivel atencion",
            "Nivel atención parto",
            "Nivel atencion parto",
        ],
        "10.1 Causa básica CIE-10": [
            "10.1 causa basica cie-10",
            "10.1 Causa de defunción",
            "Causa de defunción",
            "10.1 Causa basica CIE10",
            "Causa básica CIE-10",
            "Causa basica CIE10",
            "Causa basica",
        ],
        "10.3.1 Demora 1": ["10.3.1 demora 1", "Demora 1"],
        "10.3.2 Demora 2": ["10.3.2 demora 2", "Demora 2"],
        "10.3.3 Demora 3": ["10.3.3 demora 3", "Demora 3"],
        "10.3.4 Demora 4": ["10.3.4 demora 4", "Demora 4"],
        "Fecha de Nacimiento": [
            "Fecha de nacimiento",
            "Fecha nacimiento",
            "Fecha de nacimiento (dd/mm/aaaa)",
            "Fecha nacimiento (dd/mm/aaaa)",
        ],
    },
}

# ---------------------------------------------------------------------------
# Helpers de canonización y lectura
# ---------------------------------------------------------------------------


def _construir_mapa_alias(tipo: str) -> dict[str, str]:
    """Construye el mapa de encabezado normalizado al nombre canónico de columna.

    Args:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').

    Returns:
        Diccionario de encabezado normalizado → nombre canónico.
    """
    mapa: dict[str, str] = {}
    for canonical in _COLUMNAS_REQUERIDAS[tipo]:
        mapa[_normalizar_encabezado(canonical)] = canonical
    for canonical, alias_list in _ALIAS_COLUMNAS.get(tipo, {}).items():
        mapa[_normalizar_encabezado(canonical)] = canonical
        for alias in alias_list:
            mapa[_normalizar_encabezado(alias)] = canonical
    return mapa


def _obtener_columnas_faltantes(tipo: str, columnas_archivo: list[str]) -> list[str]:
    """Devuelve las columnas requeridas ausentes en el archivo.

    Args:
        tipo: Tipo de análisis.
        columnas_archivo: Nombres de columnas presentes en el archivo.

    Returns:
        Lista de nombres canónicos de columnas faltantes.
    """
    mapa = _construir_mapa_alias(tipo)
    presentes = {
        mapa[_normalizar_encabezado(col)]
        for col in columnas_archivo
        if _normalizar_encabezado(col) in mapa
    }
    columnas_faltantes: list[str] = [
        col for col in _COLUMNAS_REQUERIDAS[tipo] if col not in presentes
    ]
    return columnas_faltantes


def _puntaje_encabezados(tipo: str, columnas: list[str] | None) -> int:
    """Cuenta cuántas columnas requeridas reconoce la lista de encabezados dada.

    Args:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').
        columnas: Encabezados candidatos a evaluar.

    Returns:
        Número de columnas requeridas reconocidas; -1 si no hay encabezados.
    """
    if not columnas:
        return -1
    faltantes = _obtener_columnas_faltantes(tipo, columnas)
    return len(_COLUMNAS_REQUERIDAS[tipo]) - len(faltantes)


def _canonizar_columnas_dataframe(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Renombra las columnas del DataFrame a sus nombres canónicos.

    Args:
        df: DataFrame con columnas originales del archivo.
        tipo: Tipo de análisis.

    Returns:
        DataFrame con columnas renombradas según el mapa de alias.
    """
    mapa = _construir_mapa_alias(tipo)
    renames: dict[str, str] = {}
    for col in df.columns:
        canonical = mapa.get(_normalizar_encabezado(col))
        if canonical is not None and canonical != col and canonical not in df.columns:
            renames[col] = canonical
    df_canonizado: pd.DataFrame = df.rename(columns=renames)
    return df_canonizado


def _seleccionar_fila_encabezados(filas: list[list[Any]], tipo: str) -> list[str]:
    """Elige la fila con mejor coincidencia de columnas requeridas.

    Args:
        filas: Primeras filas del libro Excel como listas de valores.
        tipo: Tipo de análisis.

    Returns:
        Lista de valores de la fila con mejor puntaje de coincidencia.
    """
    mejor: list[str] = []
    mejor_puntaje = -1
    for fila in filas:
        cols = [str(v).strip() for v in fila if v is not None and str(v).strip()]
        if not cols:
            continue
        puntaje = len(_COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, cols))
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = cols, puntaje
    return mejor


def _leer_columnas_excel(file_like: Any, tipo: str) -> list[str] | None:
    """Lee las columnas del Excel con openpyxl para detectar la hoja más relevante.

    Args:
        file_like: Objeto de archivo o buffer en modo binario.
        tipo: Tipo de análisis.

    Returns:
        Lista de columnas detectadas, o None si falla la lectura.
    """
    resultado: list[str] | None = None
    try:
        wb = openpyxl.load_workbook(file_like, read_only=True, data_only=True)
        mejor: list[str] = []
        mejor_puntaje = -1
        for hoja in wb.worksheets:
            filas = [[cell.value for cell in row] for row in hoja.iter_rows(min_row=1, max_row=5)]
            fila = _seleccionar_fila_encabezados(filas, tipo)
            puntaje = _puntaje_encabezados(tipo, fila)
            if puntaje > mejor_puntaje:
                mejor, mejor_puntaje = fila, puntaje
        wb.close()
        resultado = mejor
    except Exception as exc:
        logger.warning("No se pudo leer el archivo Excel con openpyxl: %s", exc)
    return resultado


def _detectar_indice_encabezados(df_sin_header: pd.DataFrame, tipo: str) -> int:
    """Detecta el índice de fila que contiene los encabezados del DataFrame.

    Args:
        df_sin_header: DataFrame leído sin encabezados (header=None).
        tipo: Tipo de análisis.

    Returns:
        Índice de la fila con mejor coincidencia de columnas requeridas.
    """
    mejor_idx = 0
    mejor_puntaje = -1
    for idx in range(min(5, len(df_sin_header))):
        celdas = df_sin_header.iloc[idx].tolist()
        cols = [str(v).strip() for v in celdas if not pd.isna(v) and str(v).strip()]
        puntaje = _puntaje_encabezados(tipo, cols)
        if puntaje > mejor_puntaje:
            mejor_idx, mejor_puntaje = idx, puntaje
    return mejor_idx


def _leer_dataframe_excel(file_like: Any, tipo: str) -> pd.DataFrame:
    """Lee el DataFrame del Excel detectando automáticamente la hoja y fila de encabezados.

    Args:
        file_like: Objeto de archivo o buffer en modo binario.
        tipo: Tipo de análisis.

    Returns:
        DataFrame con columnas canonizadas listo para procesar.
    """
    file_like.seek(0)
    hojas = pd.read_excel(file_like, engine="openpyxl", header=None, sheet_name=None)
    mejor_hoja, mejor_idx, mejor_puntaje = None, 0, -1
    for nombre, df in hojas.items():
        idx = _detectar_indice_encabezados(df, tipo)
        fila = df.iloc[idx].tolist() if len(df) > idx else []
        cols = [str(v).strip() for v in fila if not pd.isna(v) and str(v).strip()]
        puntaje = _puntaje_encabezados(tipo, cols)
        if puntaje > mejor_puntaje:
            mejor_hoja, mejor_idx, mejor_puntaje = nombre, idx, puntaje
    file_like.seek(0)
    df_raw = pd.read_excel(file_like, engine="openpyxl", header=mejor_idx, sheet_name=mejor_hoja)
    df_canonizado: pd.DataFrame = _canonizar_columnas_dataframe(df_raw, tipo)
    return df_canonizado


# ---------------------------------------------------------------------------
# Preparación de DataFrame
# ---------------------------------------------------------------------------


def preparar_dataframe_analisis(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Normaliza el DataFrame y elimina filas vacías o duplicadas.

    Calcula la columna 'Edad' a partir de 'Fecha de Nacimiento' y la fecha del evento.

    Args:
        df: DataFrame tal como sale de pd.read_excel.

    Returns:
        Tupla (df_limpio, info_limpieza) con conteos de filas eliminadas.
    """
    normalizado = df.copy()
    total_original = len(normalizado)
    filas_vacias = 0
    filas_duplicadas = 0

    if total_original > 0:
        birth_col = "Fecha de Nacimiento"
        event_col_candidates = [
            "9.3 Fecha parto (dd/mm/aaaa)",
            "9.3 Fecha parto",
            "5.2 Fecha de defunción",
            "5.2 Fecha de defuncion",
            "Fecha de egreso",
            "Fecha de egreso (dd/mm/aaaa)",
        ]

        if birth_col in normalizado.columns:
            event_col = next((c for c in event_col_candidates if c in normalizado.columns), None)
            if event_col:
                try:
                    nacs = parse_fecha_robusta(normalizado[birth_col])
                    evs = parse_fecha_robusta(normalizado[event_col])
                    years = evs.dt.year - nacs.dt.year
                    before_birthday = (evs.dt.month < nacs.dt.month) | (
                        (evs.dt.month == nacs.dt.month) & (evs.dt.day < nacs.dt.day)
                    )
                    edades = years - before_birthday.astype(int)
                    normalizado["Edad"] = edades.where((edades >= 0) & (edades <= 120))
                except Exception as exc:
                    logger.warning("No se pudo calcular la columna Edad: %s", exc)

        for col in normalizado.select_dtypes(include=["object"]).columns:
            normalizado[col] = normalizado[col].apply(
                lambda v: v.strip() if isinstance(v, str) else v
            )

        sin_vacias = normalizado.dropna(how="all")
        filas_vacias = total_original - len(sin_vacias)
        sin_duplicadas = sin_vacias.drop_duplicates().reset_index(drop=True)
        filas_duplicadas = len(sin_vacias) - len(sin_duplicadas)
        normalizado = sin_duplicadas

    info_limpieza: dict[str, int] = {
        "total_original": total_original,
        "filas_vacias_omitidas": filas_vacias,
        "filas_duplicadas_omitidas": filas_duplicadas,
    }
    resultado: tuple[pd.DataFrame, dict[str, int]] = (normalizado, info_limpieza)
    return resultado
