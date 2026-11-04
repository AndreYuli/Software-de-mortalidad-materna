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
        ('Puerperio > 24h', 'Puerperio > 24 horas'),
        ('Puerperio < 24h', 'Puerperio < 24 horas'),
        ('Quirúrgico', 'Quirúrgico'),
    ],
)
def test_valor_del_excel_coincide_con_el_catalogo(excel, catalogo):
    """Variantes habituales del Excel (sin 'métodos', DIU, 24h) resuelven al catálogo de la BD."""
    assert _normalizar_catalogo_slug(excel) == _normalizar_catalogo_slug(catalogo)


# --- Revisión de uso, parte 3: reglas de valor con número de fila (no SQL crudo) ---


def _df(columnas: dict) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.DataFrame(columnas)
    return df, pd.Series([f'h{i}' for i in range(len(df))], index=df.index)


def test_causa_perinatal_p07_se_rechaza_con_fila_y_explicacion():
    """P07.3 (código perinatal) no es causa de muerte materna: error claro con la fila."""
    from services.sivigila_service import _verificar_reglas_de_valor

    df, hashes = _df({'10.1 Causa básica CIE-10': ['O14.1', 'P07.3', '8888']})
    with pytest.raises(ValueError) as exc:
        _verificar_reglas_de_valor('mortalidad', df, hashes, set())
    mensaje = str(exc.value)
    assert 'Fila 3' in mensaje and 'P07.3' in mensaje and '8888' in mensaje
    assert 'INSERT' not in mensaje and 'psycopg2' not in mensaje


def test_gestaciones_fuera_de_rango_lista_todas_las_filas():
    """Gestaciones = 99 se reporta con fila y rango permitido; se agrupan los errores."""
    from services.sivigila_service import _verificar_reglas_de_valor

    df, hashes = _df({'10.1 Causa básica CIE-10': ['O14.1'] * 3, '6.5 Gestaciones': [2, 99, 0]})
    with pytest.raises(ValueError) as exc:
        _verificar_reglas_de_valor('mortalidad', df, hashes, set())
    mensaje = str(exc.value)
    assert 'Fila 3' in mensaje and '1 y 20' in mensaje and 'Fila 4' in mensaje


def test_uci_si_sin_dias_se_rechaza_en_morbilidad():
    """Ingreso UCI = Sí exige 'Días estancia UCI' (lo dice la plantilla)."""
    from services.sivigila_service import _verificar_reglas_de_valor

    df, hashes = _df(
        {
            'Causa principal CIE-10': ['O141', 'O141'],
            'Ingreso UCI': ['Sí', 'No'],
            'Días estancia UCI': [None, None],
        }
    )
    with pytest.raises(ValueError, match='Fila 2.*UCI'):
        _verificar_reglas_de_valor('morbilidad', df, hashes, set())


def test_filas_duplicadas_ya_guardadas_no_se_validan_y_datos_validos_pasan():
    """Las filas ya guardadas se omiten; un archivo correcto no lanza error."""
    from services.sivigila_service import _verificar_reglas_de_valor

    df, hashes = _df({'10.1 Causa básica CIE-10': ['P07.3', 'O14.1'], '6.5 Gestaciones': [99, 2]})
    _verificar_reglas_de_valor('mortalidad', df, hashes, {'h0'})


@pytest.mark.parametrize(
    ('pgcode', 'constraint', 'esperado'),
    [
        ('23514', 'chk_am_gest', 'entre 1 y 20'),
        ('23514', 'chk_causa_cie10_valida', 'CIE-10'),
        ('23514', 'chk_desconocido', 'no cumple una regla'),
        ('23505', None, 'ya existe'),
        ('23503', None, 'catálogo'),
        ('22001', None, 'demasiado largo'),
    ],
)
def test_errores_de_restriccion_de_bd_se_traducen_sin_sql(pgcode, constraint, esperado):
    """CHECK, UNIQUE, FK y longitud se explican en español sin volcar el INSERT."""

    class _Diag:
        constraint_name = constraint
        table_name = 'causa_muerte'
        column_name = None

    class _OrigError(Exception):
        pass

    orig = _OrigError('INSERT INTO causa_muerte (...) VALUES (...)')
    orig.pgcode = pgcode
    orig.diag = _Diag()

    class _ErrorSAError(Exception):
        pass

    err = _ErrorSAError('(psycopg2.errors...) [SQL: INSERT INTO causa_muerte ...]')
    err.orig = orig
    mensaje = _mensaje_error_bd(err)
    assert esperado in mensaje
    assert 'INSERT' not in mensaje and 'psycopg2' not in mensaje
