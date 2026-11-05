"""Validación de formato y existencia de códigos CIE-10 (causas asociadas de morbilidad)."""

import pandas as pd
import pytest

from services.sivigila_service import _verificar_reglas_de_valor
from utils.cie10 import es_codigo_cie10_valido, limpiar_causa_asociada


@pytest.mark.parametrize(
    'codigo',
    ['O14.1', 'O141', 'o14.1', ' O72.1 ', 'O85', 'O13', 'J81', 'D65', 'E11.9', 'N17.9'],
)
def test_codigos_validos(codigo):
    """Con y sin punto, en minúscula, con espacios y de 3 caracteres (O85 -> O85X)."""
    assert es_codigo_cie10_valido(codigo)


@pytest.mark.parametrize('codigo', ['', None, '123', 'O1', 'O14.12345', 'OO14', 'O14,1', 'ZZZ.9'])
def test_formato_invalido(codigo):
    """Vacío, sin letra inicial, demasiado corto o largo, coma decimal o letras de más."""
    assert not es_codigo_cie10_valido(codigo)


def test_codigo_con_formato_correcto_pero_inexistente_en_el_catalogo():
    """O99.9 y A00.7 respetan el formato pero no figuran en la tabla de referencia CIE-10."""
    assert not es_codigo_cie10_valido('O99.9')
    assert not es_codigo_cie10_valido('A00.7')
    assert es_codigo_cie10_valido('O99.8')  # este sí existe: el rechazo no es por la letra O


def _df(**cols) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.DataFrame(cols)
    return df, pd.Series([f'h{i}' for i in range(len(df))], index=df.index)


def test_causa_asociada_invalida_se_rechaza_con_fila_y_columna():
    """Una causa asociada mal escrita se reporta con la fila de Excel, no como error de BD."""
    df, hashes = _df(
        **{
            'Causa principal CIE-10': ['O14.1', 'O14.1'],
            'Causa asociada CIE-10': ['O72.1', 'XYZ'],
            'Causa asociada CIE-10.1': [None, 'O46.0'],
            'Causa asociada CIE-10.2': ['A00.7', None],
        }
    )
    with pytest.raises(ValueError) as exc:
        _verificar_reglas_de_valor('morbilidad', df, hashes, set())
    mensaje = str(exc.value)
    assert 'Fila 3' in mensaje and "'XYZ'" in mensaje and 'Causa asociada CIE-10' in mensaje
    assert 'Fila 2' in mensaje and "'A00.7'" in mensaje
    assert 'INSERT' not in mensaje


def test_causas_asociadas_validas_o_vacias_pasan():
    """Vacías y válidas no generan error; las filas duplicadas ya guardadas no se validan."""
    df, hashes = _df(
        **{
            'Causa principal CIE-10': ['O14.1', 'O14.1', 'O14.1'],
            'Causa asociada CIE-10': ['O72.1', None, 'XYZ'],
        }
    )
    _verificar_reglas_de_valor('morbilidad', df, hashes, {'h2'})


def test_causa_principal_de_morbilidad_inexistente_se_rechaza():
    """La causa principal de morbilidad también debe existir en el catálogo."""
    df, hashes = _df(**{'Causa principal CIE-10': ['O14.1', 'QQ9']})
    with pytest.raises(ValueError, match="Fila 3.*'QQ9'"):
        _verificar_reglas_de_valor('morbilidad', df, hashes, set())


@pytest.mark.parametrize('vacio', [None, '', '  ', '—', '–', '-', ' — ', float('nan')])
def test_marcadores_de_vacio_no_son_causas_asociadas(vacio):
    """Las plantillas de prueba usan '—' para 'sin causa asociada': no es un código ni se guarda."""
    assert limpiar_causa_asociada(vacio) is None


def test_limpiar_causa_asociada_conserva_el_codigo():
    """Un código con espacios alrededor se devuelve sin ellos."""
    assert limpiar_causa_asociada(' O72.1 ') == 'O72.1'


def test_guion_largo_en_causa_asociada_no_bloquea_la_carga():
    """'—' en una causa asociada significa vacío: la carga no debe rechazarla."""
    df, hashes = _df(
        **{
            'Causa principal CIE-10': ['O14.1'],
            'Causa asociada CIE-10': ['—'],
            'Causa asociada CIE-10.1': ['—'],
            'Causa asociada CIE-10.2': ['—'],
        }
    )
    _verificar_reglas_de_valor('morbilidad', df, hashes, set())


def test_guion_largo_como_causa_principal_si_se_rechaza():
    """La causa principal es obligatoria: '—' no vale."""
    df, hashes = _df(**{'Causa principal CIE-10': ['—']})
    with pytest.raises(ValueError, match="Fila 2.*'—'"):
        _verificar_reglas_de_valor('morbilidad', df, hashes, set())
