"""Helpers de detección de fechas, filtrado temporal y distribución mensual."""

from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from db.models_sqlalchemy import CasoMorbilidad, CasoMortalidad, Paciente
from utils.date_parsers import parse_fecha_robusta

_MESES_ABREV = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _candidatos_fecha_col(tipo: str) -> list[str]:
    """Obtiene los nombres de columna posibles para la fecha principal del evento.

    Args:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').

    Returns:
        Lista de nombres de columna candidatos, en orden de preferencia.
    """
    candidatos: list[str] = ["Fecha de egreso", "Fecha egreso"]
    if tipo == "mortalidad":
        candidatos = ["5.2 Fecha de defunción", "5.2 Fecha de defuncion", "Fecha de defunción"]
    return candidatos


def _detectar_col_fecha(df: pd.DataFrame, tipo: str) -> str | None:
    """Detecta el nombre de la columna de fecha presente en el DataFrame.

    Busca priorizando columnas que contengan datos no-nulos.

    Args:
        df: DataFrame a inspeccionar.
        tipo: Tipo de análisis.

    Returns:
        Nombre de la columna de fecha encontrada, o None si no existe.
    """
    columna_fecha: str | None = None
    candidatos = _candidatos_fecha_col(tipo)
    # 1. Buscamos una columna candidata que tenga al menos algún dato no-nulo
    for col in candidatos:
        if col in df.columns and df[col].notna().any():
            columna_fecha = col
            break
    # 2. Si ninguna tiene datos, tomamos la primera candidata presente (aunque esté vacía)
    if columna_fecha is None:
        for col in candidatos:
            if col in df.columns:
                columna_fecha = col
                break
    # 3. Sin candidatos, buscamos cualquier columna con 'fecha' y datos (solo morbilidad)
    if columna_fecha is None and tipo == "morbilidad":
        columna_fecha = next(
            (col for col in df.columns if "fecha" in str(col).lower() and df[col].notna().any()),
            None,
        )
    # 4. Fallback final: cualquier columna con 'fecha' (solo para morbilidad)
    if columna_fecha is None and tipo == "morbilidad":
        columna_fecha = next((col for col in df.columns if "fecha" in str(col).lower()), None)
    return columna_fecha


def _extraer_anos_disponibles(df: pd.DataFrame, tipo: str) -> list[int]:
    """Extrae los años únicos disponibles en la columna de fecha del DataFrame.

    Args:
        df: DataFrame con datos de análisis.
        tipo: Tipo de análisis.

    Returns:
        Lista de años en orden descendente, o lista vacía si no hay columna de fecha.
    """
    col = _detectar_col_fecha(df, tipo)
    anos: list[int] = []
    if col is not None:
        anos_raw = parse_fecha_robusta(df[col]).dt.year.dropna().unique().astype(int).tolist()
        anos = sorted(anos_raw, reverse=True)
    return anos


def _filtrar_por_fecha(
    df: pd.DataFrame,
    tipo: str,
    year: str | None,
    month: str | None,
    week: str | None = None,
    day: str | None = None,
) -> pd.DataFrame:
    """Filtra el DataFrame por año, mes, semana ISO y/o día según la columna de fecha detectada.

    Args:
        df: DataFrame a filtrar.
        tipo: Tipo de análisis.
        year: Año como string, o None para no filtrar.
        month: Mes (1-12) como string, o None para no filtrar.
        week: Semana ISO del año (1-53) como string, o None para no filtrar.
        day: Día del mes (1-31) como string, o None para no filtrar.

    Returns:
        DataFrame filtrado y con índice reiniciado.
    """
    col = _detectar_col_fecha(df, tipo)
    df_filtrado: pd.DataFrame = df
    if col is not None:
        fechas = parse_fecha_robusta(df[col])
        mask = pd.Series([True] * len(df), index=df.index)
        if year:
            mask &= fechas.dt.year == int(year)
        if month:
            mask &= fechas.dt.month == int(month)
        if week:
            # .astype(int) directo rompe si hay fechas NaT (isocalendar da <NA>
            # nullable); comparar en el dtype nullable y luego fillna(False).
            mask &= (fechas.dt.isocalendar().week == int(week)).fillna(False)
        if day:
            mask &= fechas.dt.day == int(day)
        df_filtrado = df[mask].reset_index(drop=True)
    return df_filtrado


def _ultima_semana_reportada(df: pd.DataFrame, tipo: str) -> dict[str, int] | None:
    """Calcula la semana ISO y el año del caso más reciente en el DataFrame completo.

    Se usa para que el tablero principal indique la semana de la última
    carga, independientemente de qué filtros estén activos.

    Args:
        df: DataFrame completo (sin filtrar), con datos de análisis.
        tipo: Tipo de análisis.

    Returns:
        Dict con 'anio' y 'semana', o None si no hay columna de fecha o datos válidos.
    """
    col = _detectar_col_fecha(df, tipo)
    if col is None:
        return None
    fechas = parse_fecha_robusta(df[col]).dropna()
    if fechas.empty:
        return None
    fecha_max = fechas.max()
    iso = fecha_max.isocalendar()
    return {"anio": int(iso.year), "semana": int(iso.week)}


def _calcular_distribucion_mensual(df: pd.DataFrame, tipo: str) -> dict[str, Any]:
    """Calcula la distribución de casos por año y mes a partir de la columna de fecha.

    Args:
        df: DataFrame con datos de análisis.
        tipo: Tipo de análisis.

    Returns:
        Diccionario anidado {año: {mes: conteo}},
        o dict vacío si no hay columna de fecha o está vacía.
    """
    col = _detectar_col_fecha(df, tipo)
    distribucion: dict[str, Any] = {}
    if col is not None:
        fechas = parse_fecha_robusta(df[col]).dropna()
        if not fechas.empty:
            df_temp = pd.DataFrame(
                {"year": fechas.dt.year.astype(int), "month": fechas.dt.month.astype(int)}
            )
            grouped = df_temp.groupby(["year", "month"]).size()
            for (yr, mo), val in grouped.items():
                yr_str = str(yr)
                mo_str = str(mo)
                if yr_str not in distribucion:
                    distribucion[yr_str] = {}
                distribucion[yr_str][mo_str] = int(val)
    return distribucion


def _enriquecer_df_con_fecha(db: Session, df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """Enriquece el DataFrame con fechas obtenidas de la base de datos si faltan.

    Solo consulta la BD cuando la columna de fecha está ausente o completamente vacía.

    Args:
        db: Sesión de base de datos.
        df: DataFrame de análisis.
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').

    Returns:
        DataFrame con columna de fecha enriquecida, o el mismo DataFrame si ya tenía fechas.
    """
    dataframe_enriquecido: pd.DataFrame = df.copy()
    col = _detectar_col_fecha(dataframe_enriquecido, tipo)
    fechas_ya_presentes = col is not None and dataframe_enriquecido[col].notna().any()
    if not fechas_ya_presentes:
        if tipo == "mortalidad":
            casos = (
                db.query(CasoMortalidad.id_caso, Paciente.numero_id, CasoMortalidad.fecha_defuncion)
                .join(Paciente, CasoMortalidad.id_paciente == Paciente.id_paciente)
                .all()
            )
            fechas_map = {c.numero_id: c.fecha_defuncion for c in casos if c.numero_id}
            col_id, col_fecha_new = "C. Número ID", "5.2 Fecha de defunción"
        else:
            casos = (
                db.query(CasoMorbilidad.id_caso, Paciente.numero_id, CasoMorbilidad.fecha_egreso)
                .join(Paciente, CasoMorbilidad.id_paciente == Paciente.id_paciente)
                .all()
            )
            fechas_map = {c.numero_id: c.fecha_egreso for c in casos if c.numero_id}
            col_id, col_fecha_new = "N° identificación", "Fecha de egreso"
        if col_id in dataframe_enriquecido.columns:
            dataframe_enriquecido[col_fecha_new] = pd.to_datetime(
                dataframe_enriquecido[col_id].astype(str).map(fechas_map), errors="coerce"
            )
    return dataframe_enriquecido
