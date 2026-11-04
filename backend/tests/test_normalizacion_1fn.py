"""Pruebas de la normalización a 1FN de los grupos repetidos de morbilidad.

Observación 8 de la asesora: `causas_morbilidad.causa_asociada_2/3/4` (y, por el mismo
motivo, `referencia.institucion_ref_1/2` y `manejo_hospitalario.cirugia_1/2`) eran grupos
de columnas repetidas, lo que incumple la primera forma normal (Codd, 1970). Ahora cada
valor es una fila de una tabla hija con su posición (`orden`).
"""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError

from db.models_sqlalchemy import (
    CasoMorbilidad,
    CausaAsociadaMorbilidad,
    CausasMorbilidad,
    CirugiaAdicionalMorbilidad,
    ManejoHospitalario,
    Paciente,
    Referencia,
    ReferenciaInstitucion,
)
from services._sivigila_helpers import _DatosPasada1
from services._sivigila_morbilidad import _escribir_relacionados_morbilidad

_SQL = Path(__file__).resolve().parent.parent / 'sivigila_maternidad_postgres.sql'
_COLUMNAS_PROHIBIDAS = (
    'causa_asociada_2',
    'causa_asociada_3',
    'causa_asociada_4',
    'institucion_ref_1',
    'institucion_ref_2',
    'cirugia_1',
    'cirugia_1_cual',
    'cirugia_2',
    'cirugia_2_cual',
)


def _caso(db):
    """Crea un paciente y un caso de morbilidad mínimos."""
    pac = Paciente(nombres_apellidos='Ana Prueba', numero_id='1')
    db.add(pac)
    db.flush()
    caso = CasoMorbilidad(id_paciente=pac.id_paciente, fecha_egreso=date(2026, 1, 5))
    db.add(caso)
    db.flush()
    return caso


def _escribir(db, caso, fila, creado=True):
    """Ejecuta la escritura real de relacionados con la fila indicada."""
    pdata = _DatosPasada1(ident={}, event_hash='e', row_hash='r', causa='O141')
    _escribir_relacionados_morbilidad(db, pd.Series(fila), pdata, caso, creado, {}, {})
    db.flush()


FILA = {
    'Causa asociada CIE-10': 'O150',
    'Causa asociada CIE-10.1': 'O721',
    'Causa asociada CIE-10.2': None,
    'Remitida': 'Sí',
    'Institución referencia 1': 'Hospital A',
    'Cirugía adicional 1': 'Histerectomía',
    '¿Cuál otra cirugía 1?': 'Total',
    'Cirugía adicional 2': 'Legrado',
}


def test_causas_asociadas_son_filas_con_orden(db_session):
    """Cada causa asociada con valor es una fila con su posición; la vacía no genera fila."""
    caso = _caso(db_session)
    _escribir(db_session, caso, FILA)
    filas = (
        db_session.query(CausaAsociadaMorbilidad)
        .filter_by(id_caso=caso.id_caso)
        .order_by('orden')
        .all()
    )
    assert [(f.orden, f.cie10) for f in filas] == [(1, 'O150'), (2, 'O721')]


def test_cirugias_adicionales_son_filas_con_orden(db_session):
    """Cada cirugía adicional es una fila con tipo (1-4), posición y descripción."""
    caso = _caso(db_session)
    _escribir(db_session, caso, FILA)
    filas = db_session.query(CirugiaAdicionalMorbilidad).order_by('orden').all()
    assert [(f.orden, f.id_tipo_cirugia, f.cual) for f in filas] == [(1, 1, 'Total'), (2, 3, None)]


def test_instituciones_de_referencia_son_filas_con_orden(db_session):
    """Cada institución de referencia es una fila con su posición."""
    caso = _caso(db_session)
    _escribir(db_session, caso, FILA)
    filas = db_session.query(ReferenciaInstitucion).order_by('orden').all()
    assert [(f.orden, f.institucion) for f in filas] == [(1, 'Hospital A')]


def test_reenvio_reemplaza_en_vez_de_duplicar(db_session):
    """Volver a cargar un caso existente reemplaza las hijas y no las duplica."""
    caso = _caso(db_session)
    _escribir(db_session, caso, FILA)
    nueva = {**FILA, 'Causa asociada CIE-10': 'O990', 'Causa asociada CIE-10.1': None}
    _escribir(db_session, caso, nueva, creado=False)
    filas = db_session.query(CausaAsociadaMorbilidad).order_by('orden').all()
    assert [(f.orden, f.cie10) for f in filas] == [(1, 'O990')]


def test_no_se_permite_orden_repetido_ni_fuera_de_rango(db_session):
    """La BD impide posiciones repetidas o fuera de rango (UNIQUE y CHECK)."""
    caso = _caso(db_session)
    db_session.add_all(
        [
            CausaAsociadaMorbilidad(id_caso=caso.id_caso, orden=1, cie10='O150'),
            CausaAsociadaMorbilidad(id_caso=caso.id_caso, orden=1, cie10='O721'),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
    caso = _caso(db_session)
    db_session.add(CausaAsociadaMorbilidad(id_caso=caso.id_caso, orden=4, cie10='O150'))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_modelos_ya_no_tienen_columnas_repetidas():
    """Los modelos base ya no declaran los grupos de columnas repetidas."""
    for modelo in (CausasMorbilidad, Referencia, ManejoHospitalario):
        assert not set(_COLUMNAS_PROHIBIDAS) & set(modelo.__table__.c.keys())


def test_script_sql_ya_no_declara_columnas_repetidas_en_las_tablas_base():
    """El script SQL crea las tablas hijas y quita las columnas repetidas."""
    sql = _SQL.read_text(encoding='utf-8')
    for tabla in ('referencia', 'manejo_hospitalario', 'causas_morbilidad'):
        ini = sql.index(f'CREATE TABLE {tabla} (')
        cuerpo = sql[ini : sql.index(');', ini)]
        for col in _COLUMNAS_PROHIBIDAS:
            assert col not in cuerpo, f'{col} sigue en {tabla}'
    for t in (
        'causa_asociada_morbilidad',
        'referencia_institucion',
        'cirugia_adicional_morbilidad',
    ):
        assert f'CREATE TABLE {t}' in sql


def test_marcador_de_vacio_no_se_guarda_como_causa_asociada(db_session):
    """'—' en la plantilla significa "sin causa": no debe quedar como código en la tabla hija."""
    caso = _caso(db_session)
    fila = {**FILA, 'Causa asociada CIE-10': '—', 'Causa asociada CIE-10.1': '—'}
    _escribir(db_session, caso, fila)
    assert db_session.query(CausaAsociadaMorbilidad).filter_by(id_caso=caso.id_caso).count() == 0


def test_migracion_elimina_marcadores_de_vacio_ya_guardados(db_session):
    """Los '—' que dejó la primera versión de la carga se borran en el arranque."""
    from sqlalchemy import text

    from db.migrations import SQL_LIMPIAR_MARCADORES_DE_VACIO

    caso = _caso(db_session)
    db_session.add_all(
        [
            CausaAsociadaMorbilidad(id_caso=caso.id_caso, orden=1, cie10='—'),
            CausaAsociadaMorbilidad(id_caso=caso.id_caso, orden=2, cie10='O721'),
        ]
    )
    db_session.flush()
    db_session.execute(text(SQL_LIMPIAR_MARCADORES_DE_VACIO))
    filas = db_session.query(CausaAsociadaMorbilidad).filter_by(id_caso=caso.id_caso).all()
    assert [f.cie10 for f in filas] == ['O721']
