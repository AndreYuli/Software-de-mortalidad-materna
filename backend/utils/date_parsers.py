"""Utilidades para el parseo de fechas."""

import warnings
from datetime import date, time
from typing import Any

import pandas as pd

from utils.text_utils import is_empty

_EXCEL_SERIAL_ORIGIN = pd.Timestamp("1899-12-30")


def _extraer_serial_excel(value: Any) -> date | None:
    """Convierte un serial numérico de Excel a date, o None si no aplica.

    Los seriales de Excel son enteros que representan días desde 1899-12-30.
    Solo se considera válido el rango 1.000–100.000 (años ~1902–2173).

    Args:
        value: Valor candidato a serial Excel.

    Returns:
        Objeto date convertido desde el serial, o None si el valor no es
        numérico o está fuera del rango válido.
    """
    resultado: date | None
    try:
        n = int(float(value))
        if 1000 < n < 100_000:
            resultado = (_EXCEL_SERIAL_ORIGIN + pd.Timedelta(days=n)).date()
        else:
            resultado = None
    except (ValueError, TypeError):
        resultado = None
    return resultado


def _parse_date(value: Any) -> date | None:
    """Convierte un valor de celda a date, incluyendo seriales de Excel.

    Los seriales de Excel son enteros del tipo 44000 que representan días
    desde 1899-12-30. Esta función los detecta y los convertirá.

    Args:
        value: Número serial, string de fecha o datetime.

    Returns:
        Objeto date o None si no se puede parsear.
    """
    resultado: date | None
    if is_empty(value):
        resultado = None
    else:
        val_str = str(value).strip()
        if not ("/" in val_str or "-" in val_str or len(val_str) > 8):
            serial = _extraer_serial_excel(value)
        else:
            serial = None
        if serial is not None:
            resultado = serial
        else:
            fecha = pd.to_datetime(value, errors="coerce", dayfirst=True)
            anio_1970 = not pd.isna(fecha) and fecha.year == 1970
            epoch_falso = anio_1970 and "1970" not in val_str and "70" not in val_str
            if pd.isna(fecha) or epoch_falso:
                resultado = _extraer_serial_excel(value)
            else:
                resultado = fecha.date()
    return resultado


def _parse_time(value: Any) -> time | None:
    """Convierte un valor de celda a time o None si no es parseable.

    Args:
        value: Valor de celda con hora.

    Returns:
        Objeto time o None.
    """
    resultado: time | None
    if is_empty(value):
        resultado = None
    else:
        hora = pd.to_datetime(value, errors="coerce")
        if pd.isna(hora):
            resultado = None
        else:
            resultado = hora.time()
    return resultado


def parse_fecha_robusta(serie: pd.Series) -> pd.Series:
    """Parsea una Serie con fechas en múltiples formatos SIVIGILA.

    Maneja datetimes nativos, seriales de Excel (enteros >1000) y
    strings en distintos formatos.

    Args:
        serie: Serie con valores de fecha.

    Returns:
        Serie de tipo datetime64 con NaT donde no se pudo parsear.
    """
    resultado: pd.Series
    if pd.api.types.is_datetime64_any_dtype(serie):
        resultado = serie
    else:
        s_numeric = pd.to_numeric(serie, errors="coerce")
        is_excel_serial = (s_numeric > 1000) & (s_numeric < 100_000)

        serie_clean = serie.copy()
        if is_excel_serial.any():
            serie_clean = serie_clean.mask(is_excel_serial)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, message=".*Parsing dates.*")
            fechas = pd.to_datetime(serie_clean, dayfirst=True, errors="coerce")

        if is_excel_serial.any():
            excel_days = s_numeric[is_excel_serial].astype(int)
            fechas_excel = pd.to_datetime(
                excel_days,
                unit="D",
                origin="1899-12-30",
                errors="coerce",
            )
            fechas = fechas.fillna(fechas_excel)

        por_vias_alternas = fechas.isna() & serie_clean.notna()
        if por_vias_alternas.any():
            fechas = fechas.fillna(
                pd.to_datetime(serie_clean[por_vias_alternas].astype(str), errors="coerce")
            )
        resultado = fechas
    return resultado
