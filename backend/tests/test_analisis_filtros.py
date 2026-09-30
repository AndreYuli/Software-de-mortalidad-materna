"""Tests de filtrado temporal (año, mes, semana ISO, día)."""

import pandas as pd

from services._analisis_filtros import _filtrar_por_fecha, _ultima_semana_reportada
from utils.date_parsers import parse_fecha_robusta


def _df_morbilidad_con_fechas() -> pd.DataFrame:
    """DataFrame mínimo de morbilidad con columna de fecha de egreso."""
    return pd.DataFrame(
        {
            'Fecha de egreso': [
                '15/03/2026',  # semana ISO 11
                '16/03/2026',  # semana ISO 12
                '01/01/2026',  # semana ISO 1
                None,
            ],
            'N° identificación': [1, 2, 3, 4],
        }
    )


def test_filtrar_por_semana_iso_devuelve_solo_esa_semana():
    """Filtrar por semana ISO debe devolver solo las filas de esa semana."""
    df = _df_morbilidad_con_fechas()
    resultado = _filtrar_por_fecha(df, 'morbilidad', year=None, month=None, week='11')
    assert len(resultado) == 1
    assert resultado['N° identificación'].tolist() == [1]


def test_filtrar_por_semana_no_falla_con_fechas_vacias():
    """Una fila con fecha None (NaT) no debe romper la comparación de semana ISO."""
    df = _df_morbilidad_con_fechas()
    resultado = _filtrar_por_fecha(df, 'morbilidad', year=None, month=None, week='12')
    assert len(resultado) == 1
    assert resultado['N° identificación'].tolist() == [2]


def test_filtrar_por_dia_del_mes():
    """Filtrar por día del mes debe devolver solo las filas de ese día."""
    df = _df_morbilidad_con_fechas()
    resultado = _filtrar_por_fecha(df, 'morbilidad', year=None, month=None, day='15')
    assert resultado['N° identificación'].tolist() == [1]


def test_filtrar_combinando_year_month_week_day():
    """Los cuatro filtros deben combinarse con AND."""
    df = _df_morbilidad_con_fechas()
    resultado = _filtrar_por_fecha(df, 'morbilidad', year='2026', month='3', week='11', day='15')
    assert resultado['N° identificación'].tolist() == [1]


def test_ultima_semana_reportada_toma_la_fecha_mas_reciente():
    """Debe usar la fecha más reciente del DataFrame, no la primera fila."""
    df = _df_morbilidad_con_fechas()
    resultado = _ultima_semana_reportada(df, 'morbilidad')
    assert resultado == {'anio': 2026, 'semana': 12}


def test_ultima_semana_reportada_none_sin_fechas_validas():
    """Sin fechas válidas debe devolver None en vez de lanzar una excepción."""
    df = pd.DataFrame({'Fecha de egreso': [None, None], 'N° identificación': [1, 2]})
    assert _ultima_semana_reportada(df, 'morbilidad') is None


def test_ultima_semana_reportada_no_invierte_dia_y_mes_en_fechas_iso():
    """'2026-02-12' (ISO, como la BD) es el 12 de febrero (semana 7), no el 2 de diciembre."""
    df = pd.DataFrame({'5.2 Fecha de defunción': ['2026-02-12', '2026-01-24']})
    assert _ultima_semana_reportada(df, 'mortalidad') == {'anio': 2026, 'semana': 7}


def test_parse_fecha_robusta_mezcla_iso_y_dia_primero():
    """Las fechas ISO se leen tal cual y las dd/mm/aaaa siguen leyéndose con día primero."""
    fechas = parse_fecha_robusta(pd.Series(['2026-02-12', '12/02/2026', '15/03/2026']))
    assert fechas.dt.strftime('%Y-%m-%d').tolist() == ['2026-02-12', '2026-02-12', '2026-03-15']
