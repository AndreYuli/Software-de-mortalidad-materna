"""Esquema de la base de datos: el script SQL sigue a los modelos y PostgreSQL aplica las reglas.

* Las pruebas de coherencia corren siempre.
* Las pruebas de PostgreSQL crean un esquema temporal con el script generado y lo borran al
  terminar; se omiten si no hay un PostgreSQL accesible con las variables DB_* del entorno.
"""

import importlib.util
import uuid
from pathlib import Path

import psycopg2
import pytest
from sqlalchemy.engine import make_url

from core.config import Config
from db.auditoria import TABLAS_AUDITADAS, TABLAS_CON_ACTUALIZADO_EN
from db.database import Base

_RAIZ = Path(__file__).resolve().parent.parent
_SCRIPT_SQL = _RAIZ / 'sivigila_maternidad_postgres.sql'


def _cargar_generador():
    spec = importlib.util.spec_from_file_location(
        'generar_esquema_sql', _RAIZ / 'scripts' / 'generar_esquema_sql.py'
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_script_sql_coincide_con_los_modelos():
    """Si cambia un modelo, trigger o vista, hay que regenerar el .sql con el script."""
    generado = _cargar_generador().generar()
    assert _SCRIPT_SQL.read_text(encoding='utf-8') == generado


def test_script_sql_no_borra_ni_crea_bases_de_datos():
    """El script se ejecuta sobre una base vacía: no trae DROP ni CREATE DATABASE."""
    sql = _SCRIPT_SQL.read_text(encoding='utf-8').upper()
    assert 'DROP DATABASE' not in sql and 'CREATE DATABASE' not in sql


def test_todas_las_tablas_tienen_llave_primaria_y_las_fk_estan_indexadas():
    """Toda llave foránea es la primera columna de algún índice, llave primaria o único."""
    sin_indice = []
    for tabla in Base.metadata.tables.values():
        if tabla.name.startswith(('v_', 'cat_')):
            continue
        assert tabla.primary_key.columns, f'{tabla.name} no tiene llave primaria'
        cubiertas = {c.name for c in tabla.primary_key.columns}
        for ind in tabla.indexes:
            cubiertas.add(next(iter(ind.columns)).name)
        for uq in tabla.constraints:
            if uq.__class__.__name__ == 'UniqueConstraint':
                cubiertas.add(next(iter(uq.columns)).name)
        for col in tabla.columns:
            if col.foreign_keys and col.name not in cubiertas and not col.primary_key:
                # El primer campo de la clave primaria/única compuesta ya la cubre.
                if col.unique:
                    continue
                sin_indice.append(f'{tabla.name}.{col.name}')
    assert not sin_indice, f'FK sin índice: {sin_indice}'


def test_tablas_auditadas_y_con_actualizado_en_existen_en_los_modelos():
    """Las tablas y columnas que usan los triggers existen en los modelos."""
    nombres = set(Base.metadata.tables)
    for tabla, pk in TABLAS_AUDITADAS:
        assert tabla in nombres
        assert pk in Base.metadata.tables[tabla].c
    for tabla in TABLAS_CON_ACTUALIZADO_EN:
        assert 'actualizado_en' in Base.metadata.tables[tabla].c


# ---------------------------------------------------------------------------
# PostgreSQL real (esquema temporal)
# ---------------------------------------------------------------------------


@pytest.fixture(scope='module')
def pg():
    """Conexión a PostgreSQL con un esquema temporal que contiene el script completo."""
    if not Config.database_url.startswith('postgresql'):
        pytest.skip('requiere PostgreSQL (variables DB_*)')
    nombre = f'prueba_{uuid.uuid4().hex[:10]}'
    url = make_url(Config.database_url)
    try:
        conexion = psycopg2.connect(
            dbname=url.database,
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port,
        )
    except Exception:  # noqa: BLE001 - sin servidor accesible: se omite
        pytest.skip('PostgreSQL no accesible')
    conexion.autocommit = True
    cur = conexion.cursor()
    cur.execute(f'CREATE SCHEMA {nombre}')
    cur.execute(f'SET search_path TO {nombre}')
    cur.execute(_SCRIPT_SQL.read_text(encoding='utf-8'))
    yield cur
    cur.execute('SET search_path TO public')
    cur.execute(f'DROP SCHEMA {nombre} CASCADE')
    conexion.close()


def _paciente(cur, numero='100'):
    cur.execute(
        "INSERT INTO paciente (nombres_apellidos, id_tipo_id, numero_id) VALUES ('Ana', 1, %s) "
        'RETURNING id_paciente',
        (numero,),
    )
    return cur.fetchone()[0]


def _caso_morb(cur, id_paciente, fecha='2026-01-05', secretaria='bello'):
    cur.execute(
        'INSERT INTO caso_morbilidad (id_paciente, fecha_egreso, secretaria_codigo) '
        'VALUES (%s, %s, %s) RETURNING id_caso',
        (id_paciente, fecha, secretaria),
    )
    return cur.fetchone()[0]


def _falla(cur, sql, args=()):
    """Ejecuta la sentencia y confirma que la base de datos la rechaza."""
    cur.execute('SAVEPOINT intento')
    with pytest.raises(Exception) as exc:  # noqa: PT011
        cur.execute(sql, args)
    cur.execute('ROLLBACK TO SAVEPOINT intento')
    return exc.value


def test_pg_reconstruye_todo(pg):
    """El script reconstruye triggers, CIE-10 y vistas en un esquema vacío."""
    pg.execute(
        'SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid '
        'WHERE NOT t.tgisinternal AND c.relnamespace = current_schema()::regnamespace'
    )
    assert pg.fetchone()[0] == len(TABLAS_CON_ACTUALIZADO_EN) + len(TABLAS_AUDITADAS) + 1
    pg.execute('SELECT count(*) FROM cie10')
    assert pg.fetchone()[0] > 12000
    pg.execute('SELECT count(*) FROM v_mortalidad_completa')  # las vistas se crean y consultan


def test_pg_antecedente_obstetrico_exige_exactamente_un_caso(pg):
    """La tabla común admite un solo caso (excluyente), una fila por caso y rangos válidos."""
    pg.execute('BEGIN')
    caso = _caso_morb(pg, _paciente(pg, '201'))
    pg.execute(
        'INSERT INTO caso_mortalidad (id_paciente, id_sitio_defuncion, secretaria_codigo) '
        'VALUES (%s, 1, %s) RETURNING id_caso',
        (_paciente(pg, '202'), 'bello'),
    )
    mort = pg.fetchone()[0]
    _falla(
        pg,
        'INSERT INTO antecedente_obstetrico (caso_morbilidad_id, caso_mortalidad_id) '
        'VALUES (%s, %s)',
        (caso, mort),
    )
    _falla(pg, 'INSERT INTO antecedente_obstetrico (gestaciones) VALUES (1)')
    pg.execute(
        'INSERT INTO antecedente_obstetrico (caso_morbilidad_id, gestaciones) VALUES (%s, 2)',
        (caso,),
    )
    _falla(
        pg,
        'INSERT INTO antecedente_obstetrico (caso_morbilidad_id, gestaciones) VALUES (%s, 3)',
        (caso,),
    )
    _falla(
        pg,
        'INSERT INTO antecedente_obstetrico (caso_mortalidad_id, gestaciones) VALUES (%s, 99)',
        (mort,),
    )
    pg.execute('ROLLBACK')


def test_pg_secretaria_cie10_y_caso_repetido_se_validan(pg):
    """Secretaría y CIE-10 deben existir en sus tablas maestras; un caso no se repite."""
    pg.execute('BEGIN')
    pac = _paciente(pg, '301')
    _falla(
        pg,
        'INSERT INTO caso_morbilidad (id_paciente, secretaria_codigo) VALUES (%s, %s)',
        (pac, 'inexistente'),
    )
    caso = _caso_morb(pg, pac)
    _falla(
        pg,
        'INSERT INTO caso_morbilidad (id_paciente, fecha_egreso, secretaria_codigo) '
        "VALUES (%s, '2026-01-05', 'bello')",
        (pac,),
    )
    _falla(
        pg,
        "INSERT INTO causas_morbilidad (id_caso, causa_principal_cie10) VALUES (%s, 'ZZZ9')",
        (caso,),
    )
    pg.execute(
        "INSERT INTO causas_morbilidad (id_caso, causa_principal_cie10) VALUES (%s, 'O141')",
        (caso,),
    )
    pg.execute('ROLLBACK')


def test_pg_triggers_de_tiempos_y_bitacora(pg):
    """Los triggers fijan actualizado_en y registran la operación sin copiar valores."""
    pg.execute('BEGIN')
    pac = _paciente(pg, '401')
    pg.execute('SELECT creado_en, actualizado_en FROM paciente WHERE id_paciente = %s', (pac,))
    creado, actualizado = pg.fetchone()
    assert creado is not None and actualizado is None
    pg.execute("UPDATE paciente SET nombres_apellidos = 'Ana María' WHERE id_paciente = %s", (pac,))
    pg.execute('SELECT creado_en, actualizado_en FROM paciente WHERE id_paciente = %s', (pac,))
    creado2, actualizado2 = pg.fetchone()
    assert actualizado2 is not None and creado2 == creado
    pg.execute(
        'SELECT operacion, columnas_modificadas::text FROM auditoria_cambio '
        "WHERE tabla = 'paciente' AND registro_id = %s ORDER BY id",
        (str(pac),),
    )
    filas = pg.fetchall()
    assert [f[0] for f in filas] == ['INSERT', 'UPDATE']
    assert (
        'nombres_apellidos' in filas[1][1] and 'Ana' not in filas[1][1]
    )  # nombres de columnas, no valores
    pg.execute('ROLLBACK')


def test_pg_importacion_solo_apunta_a_casos_existentes(pg):
    """Una importación apunta a un caso que existe en la tabla de su tipo de evento."""
    pg.execute('BEGIN')
    caso = _caso_morb(pg, _paciente(pg, '501'))
    insertar = (
        'INSERT INTO api_sivigilaimportacion (tipo, row_hash, event_hash, caso_id, numero_id, '
        "tipo_identificacion, secretaria_codigo) VALUES (%s, 'r', 'e', %s, '501', 'CC', 'bello')"
    )
    pg.execute(insertar, ('morbilidad', caso))
    _falla(pg, insertar, ('mortalidad', caso))  # ese id no existe en caso_mortalidad
    _falla(pg, insertar, ('morbilidad', caso + 999))
    _falla(pg, insertar, ('otro', caso))  # tipo fuera de cat_evento
    pg.execute('ROLLBACK')
