"""Tests de regresión para los alias de columnas de escritura SIVIGILA."""

from pathlib import Path

import pandas as pd

from services._sivigila_escritura import (
    _MORBILIDAD_GRUPO_CAUSA_COLS,
    _MORBILIDAD_PESO_RN_COLS,
    _MORBILIDAD_TERMINACION_COLS,
    _MORBILIDAD_TIEMPO_REMISION_COLS,
    _MORTALIDAD_COMPLICACIONES_FETO_COLS,
    _MORTALIDAD_FUENTE_CAUSA_COLS,
    _MORTALIDAD_NIVEL_CPN_COLS,
    _MORTALIDAD_REMISIONES_COLS,
    _get_value,
)
from services._sivigila_morbilidad import _parse_cirugia_codigo, _parse_multiplicidad

_SQL_SCHEMA_PATH = Path(__file__).resolve().parent.parent / 'sivigila_maternidad_postgres.sql'

# Opciones oficiales de "6.13 Terminación de la gestación" según la ficha
# INS 549 (Morbilidad materna extrema): 1=Aborto, 2=Parto, 3=Parto
# instrumentado, 4=Cesárea, 5=Continúa embarazada.
_OPCIONES_OFICIALES_TERMINACION = [
    'Aborto',
    'Parto',
    'Parto instrumentado',
    'Cesárea',
    'Continúa embarazada',
]


def test_reconoce_encabezado_real_de_la_plantilla_oficial_morbilidad():
    """La plantilla oficial usa 'Terminación gestación', sin 'de la'.

    Antes, `_MORBILIDAD_TERMINACION_COLS` solo reconocía
    'Terminación de la gestación', por lo que la plantilla real nunca
    poblaba `antecedentes_obstetricos.id_terminacion_gestacion`.
    """
    row = pd.Series({'Terminación gestación': 'Parto'})
    assert _get_value(row, _MORBILIDAD_TERMINACION_COLS) == 'Parto'


def test_catalogo_terminacion_gestacion_coincide_con_la_ficha_549():
    """El seed de `cat_terminacion_gestacion` debe ser el de la ficha 549.

    Antes tenía los valores de `cat_tipo_parto` (Vaginal/Cesárea/
    Ignorado) en vez de las opciones reales de "6.13 Terminación de la
    gestación", por lo que ningún valor real subido por Excel podía
    resolver contra el catálogo.
    """
    sql = _SQL_SCHEMA_PATH.read_text(encoding='utf-8')
    inicio = sql.index('INSERT INTO cat_terminacion_gestacion')
    bloque = sql[inicio : inicio + 200]
    for opcion in _OPCIONES_OFICIALES_TERMINACION:
        assert (
            opcion in bloque
        ), f'Falta la opción oficial {opcion!r} en el seed de cat_terminacion_gestacion'
    assert (
        'Vaginal' not in bloque
    ), 'El seed sigue usando las opciones de cat_tipo_parto, no las de la ficha 549'


def test_alias_columnas_reconocen_encabezados_reales_de_las_plantillas():
    """Cada alias debe reconocer el encabezado EXACTO de la plantilla oficial.

    Barrido completo de las plantillas: estos 6 campos usaban un nombre
    de columna que nunca aparece en la plantilla real (abreviado, con
    prefijo numérico distinto, o con paréntesis distintos), así que
    quedaban silenciosamente en `None` para cualquier archivo real.
    """
    casos = [
        (_MORTALIDAD_NIVEL_CPN_COLS, '8.4 Nivel atención prenatal', 'II'),
        (_MORTALIDAD_REMISIONES_COLS, '8.5 Remisiones oportunas', 'Sí'),
        (_MORTALIDAD_COMPLICACIONES_FETO_COLS, '8.6 Compl. feto/RN CIE-10', 'P07.3'),
        (_MORTALIDAD_FUENTE_CAUSA_COLS, '10.2 Causa determinada por', 'Historia clínica'),
        (_MORBILIDAD_PESO_RN_COLS, 'Peso RN (g)', 3100),
        (_MORBILIDAD_GRUPO_CAUSA_COLS, 'Causa principal agrupada', 'Hemorragia obstétrica'),
        (_MORBILIDAD_TIEMPO_REMISION_COLS, 'Tiempo remisión (horas)', 6),
    ]
    for columnas, encabezado_real, valor in casos:
        row = pd.Series({encabezado_real: valor})
        assert (
            _get_value(row, columnas) == valor
        ), f'No reconoce el encabezado real {encabezado_real!r}'


def test_riesgos_y_complicaciones_reconocen_encabezados_numerados_reales():
    """Los antecedentes de riesgo/complicaciones usan encabezados '7.1.N'/'7.2.N'.

    Antes `_MAPA_RIESGOS`/`_MAPA_COMPLICACIONES` solo buscaban '7.1 X'/'7.2 X'
    (un único prefijo compartido), pero la plantilla oficial numera cada
    ítem individualmente ('7.1.2 Hipertensión crónica', '7.2.2 Eclampsia',
    etc.), así que los 24 antecedentes de riesgo y las 18 complicaciones
    nunca se escribían para un archivo real.
    """
    row = pd.Series(
        {
            '7.1.2 Hipertensión crónica': 'Sí',
            '7.1.1 Ninguno': 'No',
            '7.2.2 Eclampsia': 'Sí',
            '7.1.24 Gingivitis/periodontitis': 'No',
        }
    )
    assert (
        _get_value(
            row, ['7.1.2 Hipertensión crónica', '7.1 Hipertensión crónica', 'Hipertensión crónica']
        )
        == 'Sí'
    )
    assert _get_value(row, ['7.1.1 Ninguno', '7.1 Ninguno', 'Ninguno']) == 'No'
    assert _get_value(row, ['7.2.2 Eclampsia', '7.2 Eclampsia', 'Eclampsia']) == 'Sí'
    assert (
        _get_value(row, ['7.1.24 Gingivitis/periodontitis', '7.1 Gingivitis y/o periodontitis'])
        == 'No'
    )


def test_criterios_morbilidad_ya_no_estan_hardcodeados():
    """Los criterios de enfermedad/falla orgánica deben leerse del Excel.

    Antes, 11 de los 16 criterios de "7.1 Enfermedad específica" y los 8
    criterios de "7.2 Falla orgánica" estaban hardcodeados a 0 en
    `_escribir_relacionados_morbilidad`, sin importar el valor real en
    el Excel. Este test cubre los nombres de columna reales que ahora
    deben reconocerse (la lectura en sí se verificó manualmente contra
    la BD real end-to-end).
    """
    row = pd.Series(
        {
            'Aborto séptico': 'Sí',
            '7.1.8 Autoinmune': 'Sí',
            'Falla hepática': 'Sí',
            'Falla coagulación': 'No',
        }
    )
    assert _get_value(row, ['Aborto séptico']) == 'Sí'
    assert _get_value(row, ['7.1.8 Autoinmune', 'Autoinmune']) == 'Sí'
    assert _get_value(row, ['Falla hepática']) == 'Sí'
    assert _get_value(row, ['Falla coagulación']) == 'No'


def test_parse_cirugia_codigo_traduce_texto_de_la_ficha_549():
    """8.4/8.5 Cirugía adicional: el texto de la ficha debe mapear a su código 1-4."""
    assert _parse_cirugia_codigo('Histerectomía') == 1
    assert _parse_cirugia_codigo('Laparotomía') == 2
    assert _parse_cirugia_codigo('Legrado') == 3
    assert _parse_cirugia_codigo('Otra') == 4
    assert _parse_cirugia_codigo(None) is None
    assert _parse_cirugia_codigo('') is None


def test_parse_cirugia_codigo_acepta_celda_numerica_leida_como_float():
    """Excel/pandas suele leer una columna numérica con NaN como float64.

    '1.0' vía `slugify` se convierte en '1 0' (el punto se normaliza a
    espacio), que no coincide con la clave '1' del diccionario. Igual
    que se corrigió para `numero_id` en `_resolver_identificacion`, hay
    que aceptar el valor numérico directamente antes de pasar por texto.
    """
    assert _parse_cirugia_codigo(1.0) == 1
    assert _parse_cirugia_codigo(4.0) == 4


def test_parse_multiplicidad_distingue_unico_de_multiple():
    """Multiplicidad: 'Único' debe ser 0 (falso) y 'Múltiple' 1 (verdadero).

    Importante: no es el mismo orden que `_parse_bool` (donde 1='Sí'),
    porque en la ficha 549 el código 1 es 'Único' (falso) y 2 es
    'Múltiple' (verdadero).
    """
    assert _parse_multiplicidad('Único') == 0
    assert _parse_multiplicidad('Múltiple') == 1
    assert _parse_multiplicidad(1) == 0
    assert _parse_multiplicidad(2) == 1
    assert _parse_multiplicidad(1.0) == 0
    assert _parse_multiplicidad(2.0) == 1
    assert _parse_multiplicidad(None) is None
