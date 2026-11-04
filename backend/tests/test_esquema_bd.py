"""Esquema de la base de datos: el script SQL sigue a los modelos y PostgreSQL aplica las reglas.

* Las pruebas de coherencia corren siempre.
* Las pruebas de PostgreSQL usan bases DESECHABLES (tests/pg_desechable.py): solo corren con
  `VM_PG_PRUEBAS` definida y nunca tocan la base configurada para la aplicación.
"""

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from db.auditoria import TABLAS_AUDITADAS, TABLAS_CON_ACTUALIZADO_EN, TIPOS_CIRUGIA
from db.database import Base, VistaBase
from db.database_views import VISTAS, create_database_views
from db.migrations import run_migrations, verificar_estructura_compatible
from tests.pg_desechable import bases_desechables, conectar, parametros

_RAIZ = Path(__file__).resolve().parent.parent
_SCRIPT_SQL = _RAIZ / 'sivigila_maternidad_postgres.sql'


def _cargar_generador():
    spec = importlib.util.spec_from_file_location(
        'generar_esquema_sql', _RAIZ / 'scripts' / 'generar_esquema_sql.py'
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _url(nombre: str) -> str:
    params = parametros()
    return (
        f'postgresql+psycopg2://{params.get("user")}:{params.get("password", "")}@'
        f'{params.get("host")}:{params.get("port")}/{nombre}'
    )


def test_script_sql_coincide_con_los_modelos():
    """Si cambia un modelo, trigger o vista, hay que regenerar el .sql con el script."""
    generado = _cargar_generador().generar()
    assert _SCRIPT_SQL.read_text(encoding='utf-8') == generado


def test_script_sql_no_borra_ni_crea_bases_de_datos():
    """El script se ejecuta sobre una base vacía: no trae DROP ni CREATE DATABASE."""
    sql = _SCRIPT_SQL.read_text(encoding='utf-8').upper()
    assert 'DROP DATABASE' not in sql and 'CREATE DATABASE' not in sql


def test_script_sql_fija_la_codificacion():
    """Sin client_encoding, psql en Windows corrompe las tildes de los catálogos."""
    assert "SET client_encoding = 'UTF8';" in _SCRIPT_SQL.read_text(encoding='utf-8')


def test_todas_las_tablas_tienen_llave_primaria_y_las_fk_estan_indexadas():
    """Toda llave foránea es la primera columna de algún índice, llave primaria o único."""
    sin_indice = []
    for tabla in Base.metadata.tables.values():
        if tabla.name.startswith('cat_'):
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
    tablas = Base.metadata.tables
    for tabla, pk, _evento, modo, args in TABLAS_AUDITADAS:
        assert tabla in tablas
        assert pk in tablas[tabla].c
        if modo in ('directo', 'exclusivo'):
            assert all(a in tablas[tabla].c for a in args), tabla
        if modo == 'padre':
            fk, padre, pk_padre = args
            assert fk in tablas[tabla].c
            assert {pk_padre, 'id_caso'} <= set(tablas[padre].c.keys()), tabla
    for tabla in TABLAS_CON_ACTUALIZADO_EN:
        assert 'actualizado_en' in tablas[tabla].c


def test_las_tablas_hijas_estan_en_la_bitacora():
    """Las tablas hijas estan en la bitacora."""
    auditadas = {t[0] for t in TABLAS_AUDITADAS}
    assert {
        'causa_asociada_morbilidad',
        'referencia_institucion',
        'cirugia_adicional_morbilidad',
    } <= auditadas


def test_las_vistas_no_estan_en_el_metadata_de_las_tablas():
    """create_all no puede crear las vistas como tablas físicas vacías."""
    assert not [t for t in Base.metadata.tables if t.startswith('v_')]
    assert set(VistaBase.metadata.tables) == set(VISTAS)


def test_create_all_en_sqlite_no_crea_vistas():
    """Create all en sqlite no crea vistas."""
    motor = create_engine('sqlite://')
    Base.metadata.create_all(bind=motor)
    assert not [t for t in inspect(motor).get_table_names() if t.startswith('v_')]


# ---------------------------------------------------------------------------
# PostgreSQL real (base desechable)
# ---------------------------------------------------------------------------


@pytest.fixture(scope='module')
def pg():
    """Cursor sobre una base desechable con el script completo (se borra al terminar)."""
    with bases_desechables('esquema') as nombres:
        conexion = conectar(nombres['esquema'])
        cur = conexion.cursor()
        cur.execute(_SCRIPT_SQL.read_text(encoding='utf-8'))
        try:
            yield cur
        finally:
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


def _caso_mort(cur, id_paciente, secretaria='bello'):
    cur.execute(
        'INSERT INTO caso_mortalidad (id_paciente, id_sitio_defuncion, secretaria_codigo) '
        'VALUES (%s, 1, %s) RETURNING id_caso',
        (id_paciente, secretaria),
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
    """El script reconstruye triggers, CIE-10, catálogos con tildes y vistas en una base vacía."""
    pg.execute('SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal')
    assert pg.fetchone()[0] == len(TABLAS_CON_ACTUALIZADO_EN) + len(TABLAS_AUDITADAS) + 1
    pg.execute('SELECT count(*) FROM cie10')
    assert pg.fetchone()[0] > 12000
    pg.execute('SELECT descripcion FROM cat_remisiones WHERE id = 1')
    assert pg.fetchone()[0] == 'Sí'
    pg.execute("SELECT relname, relkind::text FROM pg_class WHERE relname LIKE 'v!_%' ESCAPE '!'")
    assert sorted(pg.fetchall()) == [(v, 'v') for v in sorted(VISTAS)]


def test_pg_antecedente_obstetrico_exige_exactamente_un_caso(pg):
    """La tabla común admite un solo caso (excluyente), una fila por caso y rangos válidos."""
    pg.execute('BEGIN')
    caso = _caso_morb(pg, _paciente(pg, '201'))
    mort = _caso_mort(pg, _paciente(pg, '202'))
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


def test_pg_causas_asociadas_varias_ordenadas_unicas_y_con_fk(pg):
    """Varias causas por caso sin columnas extra; el código existe y no se repite en el caso."""
    pg.execute('BEGIN')
    caso = _caso_morb(pg, _paciente(pg, '601'))
    insertar = 'INSERT INTO causa_asociada_morbilidad (id_caso, orden, cie10) VALUES (%s, %s, %s)'
    for orden, codigo in ((1, 'O721'), (2, 'O150'), (3, 'O141')):
        pg.execute(insertar, (caso, orden, codigo))
    pg.execute(
        'SELECT orden, cie10, descripcion IS NOT NULL FROM v_causa_asociada_morbilidad '
        'WHERE id_caso = %s ORDER BY orden',
        (caso,),
    )
    assert pg.fetchall() == [(1, 'O721', True), (2, 'O150', True), (3, 'O141', True)]
    otro = _caso_morb(pg, _paciente(pg, '602'), fecha='2026-02-01')
    _falla(pg, insertar, (otro, 1, 'ZZ99'))  # no existe en cie10
    _falla(pg, insertar, (otro, 4, 'O721'))  # orden fuera de 1..3
    pg.execute(insertar, (otro, 1, 'O721'))
    _falla(pg, insertar, (otro, 2, 'O721'))  # UNIQUE(id_caso, cie10)
    _falla(pg, insertar, (otro + 999, 1, 'O721'))  # caso inexistente
    pg.execute('DELETE FROM caso_morbilidad WHERE id_caso = %s', (otro,))  # ON DELETE CASCADE
    pg.execute('SELECT count(*) FROM causa_asociada_morbilidad WHERE id_caso = %s', (otro,))
    assert pg.fetchone()[0] == 0
    pg.execute('ROLLBACK')


def test_pg_cie10_de_mortalidad_con_llave_foranea(pg):
    """Causa básica y complicación del feto deben existir en cie10 (la segunda es opcional)."""
    pg.execute('BEGIN')
    caso = _caso_mort(pg, _paciente(pg, '701'))
    causa = (
        'INSERT INTO causa_muerte (id_caso, causa_basica_cie10, id_fuente_causa, demora_1, '
        'demora_2, demora_3, demora_4) VALUES (%s, %s, 1, false, false, false, false)'
    )
    _falla(pg, causa, (caso, 'O999Z'))
    pg.execute(causa, (caso, 'O721'))
    cpn = (
        'INSERT INTO control_prenatal (id_caso, id_remisiones, compl_feto_rn_cie10) '
        'VALUES (%s, 1, %s)'
    )
    _falla(pg, cpn, (caso, 'NINGUNA'))
    pg.execute(cpn, (caso, None))
    pg.execute(
        "UPDATE control_prenatal SET compl_feto_rn_cie10 = 'P000' WHERE id_caso = %s", (caso,)
    )
    pg.execute('ROLLBACK')


def test_pg_cirugia_usa_el_catalogo_y_la_institucion_no_se_repite(pg):
    """Pg cirugia usa el catalogo y la institucion no se repite."""
    pg.execute('BEGIN')
    pg.execute('SELECT id, descripcion FROM cat_tipo_cirugia ORDER BY id')
    assert pg.fetchall() == list(TIPOS_CIRUGIA)
    caso = _caso_morb(pg, _paciente(pg, '801'))
    pg.execute('INSERT INTO manejo_hospitalario (id_caso) VALUES (%s) RETURNING id_manejo', (caso,))
    manejo = pg.fetchone()[0]
    cirugia = (
        'INSERT INTO cirugia_adicional_morbilidad (id_manejo, orden, id_tipo_cirugia) '
        'VALUES (%s, %s, %s)'
    )
    _falla(pg, cirugia, (manejo, 1, 5))
    pg.execute(cirugia, (manejo, 1, 4))
    pg.execute(cirugia, (manejo, 2, 4))  # dos cirugías «Otra» son válidas
    pg.execute(
        'INSERT INTO referencia (id_caso, remitida) VALUES (%s, true) RETURNING id_referencia',
        (caso,),
    )
    ref = pg.fetchone()[0]
    inst = (
        'INSERT INTO referencia_institucion (id_referencia, orden, institucion) VALUES (%s, %s, %s)'
    )
    pg.execute(inst, (ref, 1, 'Hospital A'))
    _falla(pg, inst, (ref, 2, ' hospital a '))  # misma institución sin importar mayúsculas
    pg.execute(inst, (ref, 2, 'Hospital B'))
    pg.execute('ROLLBACK')


def test_pg_bitacora_registra_el_caso_de_las_tablas_hijas(pg):
    """Pg bitacora registra el caso de las tablas hijas."""
    pg.execute('BEGIN')
    caso = _caso_morb(pg, _paciente(pg, '901'))
    mort = _caso_mort(pg, _paciente(pg, '902'))
    pg.execute(
        "INSERT INTO causa_asociada_morbilidad (id_caso, orden, cie10) VALUES (%s, 1, 'O721') "
        'RETURNING id',
        (caso,),
    )
    id_asociada = pg.fetchone()[0]
    pg.execute(
        'INSERT INTO referencia (id_caso, remitida) VALUES (%s, true) RETURNING id_referencia',
        (caso,),
    )
    ref = pg.fetchone()[0]
    pg.execute(
        'INSERT INTO referencia_institucion (id_referencia, orden, institucion) '
        "VALUES (%s, 1, 'H')",
        (ref,),
    )
    pg.execute('INSERT INTO manejo_hospitalario (id_caso) VALUES (%s) RETURNING id_manejo', (caso,))
    manejo = pg.fetchone()[0]
    pg.execute(
        'INSERT INTO cirugia_adicional_morbilidad (id_manejo, orden, id_tipo_cirugia) '
        'VALUES (%s, 1, 1)',
        (manejo,),
    )
    pg.execute(
        'INSERT INTO antecedente_obstetrico (caso_mortalidad_id, gestaciones) VALUES (%s, 1)',
        (mort,),
    )
    pg.execute("UPDATE causa_asociada_morbilidad SET cie10 = 'O150' WHERE id = %s", (id_asociada,))
    pg.execute(
        'SELECT tabla, operacion, evento, id_caso FROM auditoria_cambio WHERE tabla IN '
        "('causa_asociada_morbilidad', 'referencia_institucion', 'cirugia_adicional_morbilidad', "
        "'antecedente_obstetrico') ORDER BY id"
    )
    assert pg.fetchall() == [
        ('causa_asociada_morbilidad', 'INSERT', 'morbilidad', caso),
        ('referencia_institucion', 'INSERT', 'morbilidad', caso),
        ('cirugia_adicional_morbilidad', 'INSERT', 'morbilidad', caso),
        ('antecedente_obstetrico', 'INSERT', 'mortalidad', mort),
        ('causa_asociada_morbilidad', 'UPDATE', 'morbilidad', caso),
    ]
    pg.execute('ROLLBACK')


def test_pg_arranque_sobre_base_vacia_crea_vistas_y_catalogos():
    """Sin ejecutar el script: el arranque deja vistas (no tablas), catálogos y triggers."""
    with bases_desechables('arranque') as nombres:
        motor = create_engine(_url(nombres['arranque']))
        try:
            for _ in range(2):  # idempotente
                verificar_estructura_compatible(motor)
                Base.metadata.create_all(bind=motor)
                run_migrations(motor)
        finally:
            motor.dispose()
        con = conectar(nombres['arranque'])
        try:
            cur = con.cursor()
            cur.execute(
                "SELECT relname, relkind::text FROM pg_class WHERE relname LIKE 'v!_%' ESCAPE '!'"
            )
            assert sorted(cur.fetchall()) == [(v, 'v') for v in sorted(VISTAS)]
            cur.execute('SELECT count(*) FROM cat_tipo_id')
            assert cur.fetchone()[0] == 8
            cur.execute('SELECT count(*) FROM cat_tipo_cirugia')
            assert cur.fetchone()[0] == len(TIPOS_CIRUGIA)
            cur.execute('SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal')
            assert cur.fetchone()[0] == len(TABLAS_CON_ACTUALIZADO_EN) + len(TABLAS_AUDITADAS) + 1
        finally:
            con.close()


def test_pg_tabla_vacia_con_nombre_de_vista_se_reemplaza_y_con_datos_no():
    """Rastro de versiones anteriores: una tabla v_* vacía se cambia por la vista."""
    with bases_desechables('vista') as nombres:
        con = conectar(nombres['vista'])
        cur = con.cursor()
        cur.execute(_SCRIPT_SQL.read_text(encoding='utf-8'))
        cur.execute('DROP VIEW v_mortalidad_completa')
        cur.execute('CREATE TABLE v_mortalidad_completa (id_caso integer)')
        motor = create_engine(_url(nombres['vista']))
        try:
            with Session(bind=motor) as sesion:
                create_database_views(sesion)
            cur.execute(
                "SELECT relkind::text FROM pg_class WHERE relname = 'v_mortalidad_completa'"
            )
            assert cur.fetchone()[0] == 'v'
            cur.execute('DROP VIEW v_mortalidad_completa')
            cur.execute('CREATE TABLE v_mortalidad_completa (id_caso integer)')
            cur.execute('INSERT INTO v_mortalidad_completa VALUES (1)')
            with Session(bind=motor) as sesion:
                create_database_views(sesion)
            cur.execute('SELECT count(*) FROM v_mortalidad_completa')
            assert cur.fetchone()[0] == 1  # la tabla con datos no se tocó
        finally:
            motor.dispose()
            con.close()
