"""Tests de los mensajes de error de la carga de archivos Excel."""

import pandas as pd
import pytest

from services._sivigila_catalog import _normalizar_catalogo_slug
from services.analisis_service import _mensaje_error_bd
from services.sivigila_service import _verificar_causa_completa


def _registros(causas: list[str | None]) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.DataFrame({'10.1 Causa básica CIE-10': causas})
    return df, pd.Series([f'h{i}' for i in range(len(df))], index=df.index)


def test_causa_vacia_lista_todas_las_filas_del_excel():
    """Reporta todas las filas vacías (numeración de Excel) en un solo error."""
    df, hashes = _registros(['O14.1', None, 'O72.1', '  ', 'O99.4'])

    with pytest.raises(ValueError) as exc:
        _verificar_causa_completa('mortalidad', df, hashes, set())

    mensaje = str(exc.value)
    assert '2 fila(s)' in mensaje
    assert '3, 5' in mensaje  # índices 1 y 3 -> filas de Excel 3 y 5


def test_causa_vacia_en_fila_duplicada_ya_guardada_se_ignora():
    """Una fila vacía que se omitiría por duplicada no debe bloquear la carga."""
    df, hashes = _registros(['O14.1', None])

    _verificar_causa_completa('mortalidad', df, hashes, {'h1'})


def test_causa_vacia_trunca_la_lista_de_filas():
    """Con muchas filas vacías el mensaje muestra las primeras y cuenta el resto."""
    df, hashes = _registros([None] * 30)

    with pytest.raises(ValueError, match='30 fila') as exc:
        _verificar_causa_completa('mortalidad', df, hashes, set())

    assert '… y 10 más' in str(exc.value)


def test_error_de_permisos_de_postgres_se_traduce():
    """El error 42501 de PostgreSQL se explica en vez de mostrar el SQL crudo."""

    class _OrigPgError(Exception):
        pgcode = '42501'

    class _ErrorSqlAlchemyFalsoError(Exception):
        orig = _OrigPgError('permiso denegado a la tabla cat_tipo_id')

    mensaje = _mensaje_error_bd(_ErrorSqlAlchemyFalsoError())

    assert 'no tiene permisos' in mensaje
    assert 'cat_tipo_id' in mensaje


def test_otro_error_de_bd_conserva_el_detalle():
    """Un error de BD desconocido mantiene su texto original."""
    assert 'boom' in _mensaje_error_bd(RuntimeError('boom'))


def test_error_de_dato_obligatorio_nombra_tabla_y_columna():
    """El NOT NULL de PostgreSQL (23502) indica qué columna faltó, sin volcar el SQL."""

    class _DiagFalso:
        table_name = 'antecedente_materno'
        column_name = 'id_regulacion_fec'

    class _OrigNotNullError(Exception):
        pgcode = '23502'
        diag = _DiagFalso()

    class _ErrorSqlAlchemyNotNullError(Exception):
        orig = _OrigNotNullError('el valor null viola la restricción not null')

    mensaje = _mensaje_error_bd(_ErrorSqlAlchemyNotNullError())

    assert "'id_regulacion_fec'" in mensaje
    assert "'antecedente_materno'" in mensaje
    assert 'INSERT' not in mensaje


def test_error_de_bd_largo_se_recorta():
    """Un volcado enorme de SQL/parámetros no llega completo al usuario."""
    assert len(_mensaje_error_bd(RuntimeError('x' * 5000))) < 600


@pytest.mark.parametrize(
    ('excel', 'catalogo'),
    [
        ('No usó por acceso', 'No usó métodos por acceso'),
        ('No usó por desconocimiento', 'No usó métodos por desconocimiento'),
        ('No usó porque no deseaba', 'No usó métodos porque no deseaba'),
        ('DIU', 'Dispositivo intrauterino'),
        ('Quirúrgico', 'Quirúrgico'),
    ],
)
def test_regulacion_fecundidad_del_excel_coincide_con_el_catalogo(excel, catalogo):
    """Los valores del Excel de ejemplo se resuelven contra el catálogo de la BD."""
    assert _normalizar_catalogo_slug(excel) == _normalizar_catalogo_slug(catalogo)
