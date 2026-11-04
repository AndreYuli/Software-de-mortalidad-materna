"""Causas asociadas en todas las capas: carga (validación), análisis, API y exporte.

Las causas asociadas viven en `causa_asociada_morbilidad` (una fila por causa). Estas pruebas
comprueban que la carga rechace lo que la base o la ficha no admiten, que el análisis y el API
las recuperen y que nunca vuelvan a aparecer como columnas de una tabla.
"""

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from db.models_sqlalchemy import CausasMorbilidad, VCausaAsociadaMorbilidad
from services._morbilidad_processor import MorbilidadProcessor
from services.sivigila_service import _verificar_reglas_de_valor


def _df(**cols) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.DataFrame(cols)
    return df, pd.Series([f'h{i}' for i in range(len(df))], index=df.index)


def _mensaje(tipo: str, **cols) -> str:
    df, hashes = _df(**cols)
    with pytest.raises(ValueError) as exc:
        _verificar_reglas_de_valor(tipo, df, hashes, set())
    return str(exc.value)


# --- Carga: reglas de la ficha 549 -----------------------------------------------------------


def test_causa_asociada_que_repite_la_principal_se_rechaza_con_fila_y_columna():
    """Causa asociada que repite la principal se rechaza con fila y columna."""
    mensaje = _mensaje(
        'morbilidad',
        **{
            'Causa principal CIE-10': ['O14.1', 'O15.0'],
            'Causa asociada CIE-10': ['O72.1', 'o150'],  # fila 3: repite la principal
            'Causa asociada CIE-10.1': [None, None],
            'Causa asociada CIE-10.2': [None, None],
        },
    )
    assert "Fila 3: la columna 'Causa asociada CIE-10' repite la causa principal" in mensaje
    assert 'Fila 2' not in mensaje


def test_causa_asociada_repetida_en_la_misma_fila_se_rechaza():
    """Causa asociada repetida en la misma fila se rechaza."""
    mensaje = _mensaje(
        'morbilidad',
        **{
            'Causa principal CIE-10': ['O14.1'],
            'Causa asociada CIE-10': ['O72.1'],
            'Causa asociada CIE-10.1': ['—'],
            'Causa asociada CIE-10.2': ['O721'],
        },
    )
    assert (
        "Fila 2: la columna 'Causa asociada CIE-10.2' repite la causa asociada 'O721' de la "
        "columna 'Causa asociada CIE-10'"
    ) in mensaje


def test_causas_asociadas_distintas_y_guiones_pasan():
    """Causas asociadas distintas y guiones pasan."""
    df, hashes = _df(
        **{
            'Causa principal CIE-10': ['O14.1'],
            'Causa asociada CIE-10': ['O72.1'],
            'Causa asociada CIE-10.1': ['—'],
            'Causa asociada CIE-10.2': ['O15.0'],
        }
    )
    _verificar_reglas_de_valor('morbilidad', df, hashes, set())


def test_institucion_2_igual_a_la_1_se_rechaza():
    """Institucion 2 igual a la 1 se rechaza."""
    mensaje = _mensaje(
        'morbilidad',
        **{
            'Causa principal CIE-10': ['O14.1'],
            'Institución referencia 1': ['Hospital A'],
            'Institución referencia 2': [' hospital a '],
        },
    )
    assert "Fila 2: la columna 'Institución referencia 2' repite la institución" in mensaje


# --- Carga: CIE-10 de mortalidad -------------------------------------------------------------


def test_causa_basica_inexistente_se_rechaza_con_fila():
    """Causa basica inexistente se rechaza con fila."""
    mensaje = _mensaje(
        'mortalidad',
        **{'10.1 Causa básica CIE-10': ['O72.1', 'O99.9'], '6.5 Gestaciones': [1, 1]},
    )
    assert "Fila 3: el código CIE-10 'O99.9' de la columna '10.1 Causa básica CIE-10'" in mensaje
    assert 'Fila 2' not in mensaje


def test_complicacion_del_feto_inexistente_se_rechaza_y_vacia_o_guion_pasa():
    """Complicacion del feto inexistente se rechaza y vacia o guion pasa."""
    columna = '8.6 Compl. feto/RN CIE-10'
    mensaje = _mensaje(
        'mortalidad',
        **{
            '10.1 Causa básica CIE-10': ['O72.1', 'O72.1', 'O72.1'],
            columna: ['P00.0', 'Ninguna', '—'],
        },
    )
    assert f"Fila 3: el código CIE-10 'Ninguna' de la columna '{columna}'" in mensaje
    assert 'Fila 2' not in mensaje and 'Fila 4' not in mensaje


# --- Análisis --------------------------------------------------------------------------------


def test_procesador_cuenta_causas_asociadas_una_vez_por_caso():
    """Procesador cuenta causas asociadas una vez por caso."""
    df = pd.DataFrame(
        {
            'Causa principal CIE-10': ['O141', 'O150', 'O141', 'O141'],
            'Causa asociada CIE-10': ['O72.1', 'O721', None, '—'],
            'Causa asociada CIE-10.1': [None, 'O15.0', None, None],
            'Causa asociada CIE-10.2': ['o721', None, None, None],  # el caso 1 repite O721
        }
    )
    resultado = MorbilidadProcessor(df).analizar_causas_asociadas(top_n=5)
    assert resultado['casos_con_causa_asociada'] == 2
    assert resultado['total_causas_unicas'] == 2
    top = {c['codigo']: (c['casos'], c['porcentaje']) for c in resultado['top_causas']}
    assert top == {'O721': (2, 50.0), 'O150': (1, 25.0)}
    assert all(c['nombre'] for c in resultado['top_causas'])


def test_procesador_sin_columnas_de_causas_asociadas_devuelve_vacio():
    """Procesador sin columnas de causas asociadas devuelve vacio."""
    assert MorbilidadProcessor(pd.DataFrame({'Edad': [20]})).analizar_causas_asociadas() == {}


def test_dataframe_de_analisis_proyecta_las_filas_hijas_en_memoria(monkeypatch):
    """Las filas de la tabla hija se ubican en las columnas de la plantilla según su orden."""
    from services import _analisis_persistencia as persistencia

    filas = [
        SimpleNamespace(id_caso=7, orden=1, cie10='O721'),
        SimpleNamespace(id_caso=7, orden=3, cie10='O150'),
        SimpleNamespace(id_caso=9, orden=2, cie10='O141'),
        SimpleNamespace(id_caso=99, orden=1, cie10='O990'),  # caso fuera del DataFrame
    ]

    class _Consulta:
        def filter(self, *_):
            return self

        def all(self):
            return filas

    db = SimpleNamespace(query=lambda modelo: _Consulta())
    df = pd.DataFrame({'Edad': [30, 25]}, index=[0, 1])
    salida = persistencia._agregar_causas_asociadas(db, df, [7, 9], 'bello')
    columnas = salida[list(persistencia.COLUMNAS_CAUSA_ASOCIADA)].fillna('')
    assert columnas.values.tolist() == [['O721', '', 'O150'], ['', 'O141', '']]


# --- Estructura -------------------------------------------------------------------------------


def test_no_reaparecen_columnas_de_causas_asociadas():
    """No reaparecen columnas de causas asociadas."""
    assert not {'causa_asociada_2', 'causa_asociada_3', 'causa_asociada_4'} & set(
        CausasMorbilidad.__table__.c.keys()
    )
    assert set(VCausaAsociadaMorbilidad.__table__.c.keys()) == {
        'id',
        'id_caso',
        'secretaria_codigo',
        'orden',
        'cie10',
        'descripcion',
    }


# --- API --------------------------------------------------------------------------------------


def test_api_morbilidad_devuelve_causas_asociadas_en_una_sola_consulta(monkeypatch):
    """GET /api/sivigila/morbilidad/ trae las causas de la página con UNA consulta adicional."""
    from api.routers import sivigila

    campos = set(sivigila.VMorbilidadResponse.model_fields) - {'causas_asociadas'}
    caso = SimpleNamespace(**{c: None for c in campos})
    caso.id_caso = 10
    caso.fecha_egreso = date(2026, 1, 5)
    consultas: list = []

    class _Consulta:
        def __init__(self, modelo):
            """Prepara los cursores de origen y destino."""
            self.modelo = modelo
            consultas.append(modelo)

        def filter(self, *_):
            return self

        def order_by(self, *_):
            return self

        def offset(self, *_):
            return self

        def limit(self, *_):
            return self

        def all(self):
            if self.modelo is sivigila.VCausaAsociadaMorbilidad:
                return [
                    SimpleNamespace(id_caso=10, orden=1, cie10='O721', descripcion='Hemorragia'),
                    SimpleNamespace(id_caso=10, orden=3, cie10='O150', descripcion='Eclampsia'),
                ]
            return [caso]

    db = SimpleNamespace(query=_Consulta)
    usuario = SimpleNamespace(secretaria_codigo='bello')
    respuesta = sivigila.listar_morbilidad(skip=0, limit=None, db=db, usuario=usuario)
    assert [(c.orden, c.cie10) for c in respuesta[0].causas_asociadas] == [(1, 'O721'), (3, 'O150')]
    assert consultas.count(sivigila.VCausaAsociadaMorbilidad) == 1
