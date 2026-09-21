"""Tests del generador de datos de prueba con proporciones realistas."""

import random

import pandas as pd

from scripts.generar_excels_realistas import (
    CATALOGO_AFILIACION,
    CATALOGO_ETNIA,
    CATALOGO_POBLACION_VULNERABLE,
    CATALOGO_ZONA,
    FECHA_FIN,
    FECHA_INICIO,
    N_MORBILIDAD_DEFECTO,
    N_MORTALIDAD_DEFECTO,
    generar_morbilidad_realista,
    generar_mortalidad_realista,
)
from services._analisis_excel import _COLUMNAS_REQUERIDAS

COLUMNAS_SOCIODEMO = ['Zona de residencia', 'Población vulnerable', 'Etnia', 'Tipo de afiliación']


def test_relacion_morbilidad_mortalidad_es_50_a_1():
    """Test relacion morbilidad mortalidad es 50 a 1."""
    assert N_MORBILIDAD_DEFECTO / N_MORTALIDAD_DEFECTO == 50


def test_mortalidad_trae_las_columnas_requeridas_y_las_sociodemograficas():
    """Test mortalidad trae las columnas requeridas y las sociodemograficas."""
    df = generar_mortalidad_realista(50, random.Random(1))
    assert set(_COLUMNAS_REQUERIDAS['mortalidad']) <= set(df.columns)
    assert set(COLUMNAS_SOCIODEMO) <= set(df.columns)
    assert len(df) == 50


def test_morbilidad_trae_las_columnas_requeridas_y_las_sociodemograficas():
    """Test morbilidad trae las columnas requeridas y las sociodemograficas."""
    df = generar_morbilidad_realista(50, random.Random(1))
    assert set(_COLUMNAS_REQUERIDAS['morbilidad']) <= set(df.columns)
    assert set(COLUMNAS_SOCIODEMO) <= set(df.columns)
    assert len(df) == 50


def test_las_causas_no_son_uniformes_y_la_primera_es_hipertensiva():
    """Test las causas no son uniformes y la primera es hipertensiva."""
    df = generar_morbilidad_realista(3000, random.Random(7))
    frecuencias = df['Causa principal CIE-10'].value_counts(normalize=True)
    assert frecuencias.index[0] == 'O14.1'
    assert 0.20 <= frecuencias.iloc[0] <= 0.32
    assert frecuencias.iloc[0] > 2 * frecuencias.iloc[-1]

    df_mort = generar_mortalidad_realista(3000, random.Random(7))
    frecuencias_mort = df_mort['10.1 Causa básica CIE-10'].value_counts(normalize=True)
    assert frecuencias_mort.index[0] == 'O14.1'


def test_los_valores_sociodemograficos_pertenecen_a_los_catalogos():
    """Test los valores sociodemograficos pertenecen a los catalogos."""
    for df in (
        generar_mortalidad_realista(300, random.Random(3)),
        generar_morbilidad_realista(300, random.Random(3)),
    ):
        assert set(df['Zona de residencia']) <= set(CATALOGO_ZONA)
        assert set(df['Etnia']) <= set(CATALOGO_ETNIA)
        assert set(df['Población vulnerable']) <= set(CATALOGO_POBLACION_VULNERABLE)
        assert set(df['Tipo de afiliación']) <= set(CATALOGO_AFILIACION)


def test_la_zona_urbana_predomina():
    """Test la zona urbana predomina."""
    df = generar_morbilidad_realista(2000, random.Random(5))
    assert (df['Zona de residencia'] == 'Urbana').mean() > 0.6


def test_las_fechas_caen_en_el_periodo():
    """Test las fechas caen en el periodo."""
    df = generar_morbilidad_realista(500, random.Random(9))
    fechas = pd.to_datetime(df['Fecha de egreso'], dayfirst=True)
    assert fechas.min() >= pd.Timestamp(FECHA_INICIO)
    assert fechas.max() <= pd.Timestamp(FECHA_FIN)

    df_mort = generar_mortalidad_realista(200, random.Random(9))
    fechas_mort = pd.to_datetime(df_mort['5.2 Fecha de defunción'], dayfirst=True)
    assert fechas_mort.min() >= pd.Timestamp(FECHA_INICIO)
    assert fechas_mort.max() <= pd.Timestamp(FECHA_FIN)


def test_misma_semilla_mismo_resultado():
    """Test misma semilla mismo resultado."""
    a = generar_mortalidad_realista(80, random.Random(11))
    b = generar_mortalidad_realista(80, random.Random(11))
    pd.testing.assert_frame_equal(a, b)
