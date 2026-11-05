"""Migración desde la estructura de `main` (scripts/migrar_estructura_anterior.py).

Corre solo con `VM_PG_PRUEBAS` (bases desechables, ver tests/pg_desechable.py). Cada prueba crea
un ORIGEN con la estructura de main (tests/fixtures/esquema_main_legado.sql + datos sintéticos
con casos difíciles) y un DESTINO con el script actual, y los borra al terminar.
"""

import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from db.migrations import EstructuraAnteriorError, verificar_estructura_compatible
from scripts.migrar_estructura_anterior import ejecutar
from tests.pg_desechable import bases_desechables, conectar, parametros

_RAIZ = Path(__file__).resolve().parent.parent
_ESQUEMA_MAIN = _RAIZ / 'tests' / 'fixtures' / 'esquema_main_legado.sql'
_DATOS_MAIN = _RAIZ / 'tests' / 'fixtures' / 'datos_main_legado.sql'
_SCRIPT_NUEVO = _RAIZ / 'sivigila_maternidad_postgres.sql'


def _sumas(nombre: str) -> dict[str, tuple[int, str]]:
    """(filas, md5) de cada tabla: sirve para comprobar que el origen no cambió."""
    con = conectar(nombre)
    try:
        with con.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_type = 'BASE TABLE' ORDER BY 1"
            )
            tablas = [r[0] for r in cur.fetchall()]
            resultado = {}
            for tabla in tablas:
                cur.execute(
                    "SELECT count(*), md5(coalesce(string_agg(x::text, '|' ORDER BY x::text), ''))"
                    f' FROM {tabla} x'
                )
                resultado[tabla] = cur.fetchone()
            return resultado
    finally:
        con.close()


def _consulta(nombre: str, sql: str) -> list[tuple]:
    con = conectar(nombre)
    try:
        with con.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        con.close()


def _ejecutar_sql(nombre: str, *scripts: Path | str) -> None:
    con = conectar(nombre)
    try:
        with con.cursor() as cur:
            for script in scripts:
                cur.execute(
                    script.read_text(encoding='utf-8') if isinstance(script, Path) else script
                )
    finally:
        con.close()


@pytest.fixture
def bases(monkeypatch, tmp_path):
    """Origen (estructura de main con datos) y destino (script actual, vacío)."""
    params = parametros()
    monkeypatch.setenv('PGPASSWORD', params.get('password', ''))
    with bases_desechables('origen', 'destino') as creadas:
        nombres = dict(creadas)
        _ejecutar_sql(nombres['origen'], _ESQUEMA_MAIN, _DATOS_MAIN)
        _ejecutar_sql(nombres['destino'], _SCRIPT_NUEVO)
        nombres['args'] = [
            '--origen',
            nombres['origen'],
            '--destino',
            nombres['destino'],
            '--host',
            params.get('host', 'localhost'),
            '--port',
            params.get('port', '5432'),
            '--usuario',
            params.get('user', 'postgres'),
            '--reporte-dir',
            str(tmp_path / 'reportes'),
            '--respaldo-dir',
            str(tmp_path / 'respaldos'),
        ]
        yield nombres


def _pg_bin() -> str | None:
    carpeta = os.environ.get('VM_PG_BIN')
    if carpeta:
        return carpeta
    ruta = shutil.which('pg_dump')
    return str(Path(ruta).parent) if ruta else None


def test_simular_no_cambia_ni_el_origen_ni_el_destino(bases):
    """Simular no cambia ni el origen ni el destino."""
    antes = _sumas(bases['origen'])
    assert ejecutar([*bases['args'], '--simular']) == 0
    assert _sumas(bases['origen']) == antes
    assert _consulta(bases['destino'], 'SELECT count(*) FROM paciente') == [(0,)]
    assert _consulta(bases['destino'], "SELECT to_regclass('migracion_registro_pendiente')") == [
        (None,)
    ]


def test_confirmar_respalda_migra_y_conserva_el_origen(bases, tmp_path):
    """Confirmar respalda migra y conserva el origen."""
    pg_bin = _pg_bin()
    if not pg_bin:
        pytest.skip('requiere pg_dump/pg_restore (VM_PG_BIN o PATH)')
    antes = _sumas(bases['origen'])
    assert ejecutar([*bases['args'], '--confirmar', '--pg-bin', pg_bin]) == 0
    assert _sumas(bases['origen']) == antes  # el origen no cambió
    respaldos = list((tmp_path / 'respaldos').glob('*.dump'))
    assert len(respaldos) == 1 and respaldos[0].stat().st_size > 0

    d = bases['destino']
    # Conteos y relaciones con los mismos identificadores.
    assert _consulta(d, 'SELECT count(*) FROM paciente') == [(4,)]
    assert _consulta(d, 'SELECT id_caso FROM caso_morbilidad ORDER BY 1') == [(10,), (11,)]
    assert _consulta(d, 'SELECT id_caso FROM caso_mortalidad ORDER BY 1') == [(20,), (21,)]
    assert _consulta(d, 'SELECT count(*) FROM api_sivigilaimportacion') == [(4,)]
    assert _consulta(d, 'SELECT analisis_id FROM narrativa_ia') == [(5,)]

    # Antecedentes históricos de los dos eventos, visibles en las vistas del dashboard.
    assert _consulta(
        d,
        'SELECT id_caso, num_gestaciones, num_controles_prenatales, edad_gestacional_sem '
        'FROM v_morbilidad_completa ORDER BY 1',
    ) == [(10, 3, 6, 36), (11, 1, 0, 12)]
    assert _consulta(
        d,
        'SELECT id_caso, gestaciones, num_cpn, semana_inicio_cpn, convivencia '
        'FROM v_mortalidad_completa ORDER BY 1',
    ) == [(20, 4, 5, 11, 'Cónyuge'), (21, None, 2, None, None)]

    # CIE-10 normalizados; causas asociadas con su posición original.
    assert _consulta(d, 'SELECT causa_principal_cie10 FROM causas_morbilidad ORDER BY id_caso') == [
        ('O141',),
        ('O150',),
    ]
    assert _consulta(
        d,
        'SELECT causa_basica_cie10, compl_feto_rn_cie10 FROM causa_muerte '
        'JOIN control_prenatal USING (id_caso) ORDER BY id_caso',
    ) == [('O721', 'P000'), ('O85', None)]
    assert _consulta(
        d, 'SELECT id_caso, orden, cie10 FROM v_causa_asociada_morbilidad ORDER BY 1, 2'
    ) == [(10, 1, 'O721'), (11, 3, 'O721')]
    assert _consulta(
        d, 'SELECT id_referencia, orden, institucion FROM referencia_institucion ORDER BY 1, 2'
    ) == [(60, 1, 'Hospital A'), (61, 1, 'Clínica Uno'), (61, 2, 'Puesto Dos')]
    assert _consulta(
        d,
        'SELECT id_manejo, orden, id_tipo_cirugia FROM cirugia_adicional_morbilidad ORDER BY 1, 2',
    ) == [(70, 1, 1), (70, 2, 4), (71, 2, 3)]

    # Lo que no pudo guardarse no se pierde: queda identificado.
    assert sorted(
        _consulta(
            d,
            'SELECT motivo, id_caso, columna_origen, valor_original '
            'FROM migracion_registro_pendiente',
        )
    ) == [
        ('cie10_inexistente', 11, 'causa_asociada_2', 'Z99.99X'),
        ('cie10_inexistente', 21, 'compl_feto_rn_cie10', 'Ninguna'),
        ('repite_causa_principal', 10, 'causa_asociada_4', 'O141'),
        ('repite_institucion_1', 10, 'institucion_ref_2', ' hospital a '),
    ]

    # Las secuencias siguen al máximo id: un caso nuevo no choca con los migrados.
    assert _consulta(d, "SELECT nextval('caso_morbilidad_id_caso_seq')") == [(12,)]

    # La aplicación arranca sobre la base migrada y la bitácora identifica el caso.
    params = parametros()
    url = (
        f'postgresql+psycopg2://{params.get("user")}:{params.get("password", "")}@'
        f'{params.get("host")}:{params.get("port")}/{d}'
    )
    motor = create_engine(url)
    try:
        verificar_estructura_compatible(motor)  # no lanza
        with motor.connect() as con:
            n = con.execute(
                text(
                    "SELECT count(*) FROM auditoria_cambio WHERE tabla = 'referencia_institucion' "
                    "AND evento = 'morbilidad' AND id_caso IS NOT NULL"
                )
            ).scalar()
        assert n == 3
    finally:
        motor.dispose()


def test_cie10_obligatorio_inexistente_detiene_y_se_corrige_con_archivo(bases, tmp_path):
    """Cie10 obligatorio inexistente detiene y se corrige con archivo."""
    _ejecutar_sql(
        bases['origen'],
        "UPDATE causa_muerte SET causa_basica_cie10 = 'O99.99Z' WHERE id_caso = 21",
    )
    assert ejecutar([*bases['args'], '--simular']) == 2
    informe = max((tmp_path / 'reportes').glob('*.md')).read_text(encoding='utf-8')
    assert 'cie10_obligatorio_inexistente' in informe and 'O99.99Z' in informe
    assert _consulta(bases['destino'], 'SELECT count(*) FROM caso_mortalidad') == [(0,)]

    correcciones = tmp_path / 'correcciones_cie10.csv'
    correcciones.write_text(
        'tabla,columna,id_caso,valor_original,codigo_corregido\n'
        'causa_muerte,causa_basica_cie10,21,O99.99Z,O85\n',
        encoding='utf-8',
    )
    assert ejecutar([*bases['args'], '--simular', '--correcciones', str(correcciones)]) == 0
    informe = max((tmp_path / 'reportes').glob('*.md')).read_text(encoding='utf-8')
    assert 'codigo_corregido: O85' in informe


def test_correccion_a_un_codigo_que_tampoco_existe_sigue_bloqueando(bases, tmp_path):
    """Correccion a un codigo que tampoco existe sigue bloqueando."""
    _ejecutar_sql(
        bases['origen'],
        "UPDATE causas_morbilidad SET causa_principal_cie10 = 'XYZ' WHERE id_caso = 11",
    )
    correcciones = tmp_path / 'c.csv'
    correcciones.write_text(
        'tabla,columna,id_caso,valor_original,codigo_corregido\n'
        'causas_morbilidad,causa_principal_cie10,,XYZ,Q99.99\n',
        encoding='utf-8',
    )
    assert ejecutar([*bases['args'], '--simular', '--correcciones', str(correcciones)]) == 2


def test_duplicados_que_la_estructura_nueva_no_admite_detienen(bases, tmp_path):
    """Duplicados que la estructura nueva no admite detienen."""
    _ejecutar_sql(
        bases['origen'],
        'INSERT INTO antecedentes_obstetricos (id_caso, num_gestaciones) VALUES (10, 9)',
    )
    assert ejecutar([*bases['args'], '--simular']) == 2
    informe = max((tmp_path / 'reportes').glob('*.md')).read_text(encoding='utf-8')
    assert 'mas_de_una_fila_por_caso' in informe and 'antecedentes_obstetricos' in informe


def test_destino_con_datos_se_rechaza(bases):
    """Destino con datos se rechaza."""
    _ejecutar_sql(
        bases['destino'],
        "INSERT INTO paciente (nombres_apellidos, id_tipo_id, numero_id) VALUES ('X', 1, '9')",
    )
    assert ejecutar([*bases['args'], '--simular']) == 1


def test_el_arranque_se_niega_sobre_la_estructura_anterior(bases):
    """El arranque se niega sobre la estructura anterior."""
    params = parametros()
    url = (
        f'postgresql+psycopg2://{params.get("user")}:{params.get("password", "")}@'
        f'{params.get("host")}:{params.get("port")}/{bases["origen"]}'
    )
    motor = create_engine(url)
    try:
        antes = _sumas(bases['origen'])
        with pytest.raises(EstructuraAnteriorError, match='antecedentes_obstetricos'):
            verificar_estructura_compatible(motor)
        assert _sumas(bases['origen']) == antes
    finally:
        motor.dispose()
