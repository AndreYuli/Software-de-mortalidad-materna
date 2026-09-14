"""Tests de regresión: identificar pacientes por numero_id aunque cambie el tipo de ID."""

from datetime import date, datetime, timezone

from db.models_sqlalchemy import CasoMorbilidad, CatTipoId, Paciente
from services._sivigila_helpers import _DatosPasada1, _precargar_caches_sivigila
from services.sivigila_service import _fase2_upsert_pacientes, _fase3_upsert_casos


def _resumen_vacio() -> dict:
    return {
        "registros_procesados": 0,
        "filas_omitidas_duplicadas": 0,
        "pacientes_nuevos": 0,
        "pacientes_existentes": 0,
        "casos_creados": 0,
        "casos_actualizados": 0,
    }


def test_cambio_tipo_documento_no_duplica_paciente_y_asocia_el_caso(db_session):
    """Debe actualizar el tipo de documento sin duplicar a la paciente.

    Una paciente ya registrada con TI que ahora llega como CC (mismo
    numero_id) debe actualizarse en lugar de duplicarse, y su nuevo
    caso debe asociarse a ella.
    """
    tipo_ti = CatTipoId(id=5, codigo="TI", descripcion="Tarjeta de identidad")
    tipo_cc = CatTipoId(id=1, codigo="CC", descripcion="Cédula de ciudadanía")
    db_session.add_all([tipo_ti, tipo_cc])
    db_session.flush()

    existente = Paciente(
        id_tipo_id=tipo_ti.id,
        numero_id="102030",
        nombres_apellidos="MARIA LOPEZ",
        creado_en=datetime.now(timezone.utc),
    )
    db_session.add(existente)
    db_session.flush()

    caches = _precargar_caches_sivigila(db_session, "morbilidad", {"102030"}, [])

    ident = {
        "tipo_obj": tipo_cc,
        "tipo_codigo": tipo_cc.codigo,
        "numero_id": "102030",
        "nombres": "MARIA LOPEZ",
        "fecha_nacimiento": None,
    }
    pass1_data = {
        0: _DatosPasada1(
            ident=ident,
            event_hash="hash-evento-1",
            row_hash="hash-fila-1",
            causa="O141",
            fecha_egreso=date(2026, 1, 15),
        )
    }
    resumen = _resumen_vacio()

    _fase2_upsert_pacientes([0], pass1_data, caches, db_session, resumen)
    db_session.flush()

    assert resumen["pacientes_nuevos"] == 0
    assert resumen["pacientes_existentes"] == 1
    assert db_session.query(Paciente).count() == 1

    paciente_bd = db_session.query(Paciente).one()
    assert paciente_bd.id_tipo_id == tipo_cc.id
    assert paciente_bd.id_paciente == existente.id_paciente

    row_cases = _fase3_upsert_casos("morbilidad", [0], pass1_data, caches, db_session, resumen)
    db_session.flush()

    caso, caso_creado = row_cases[0]
    assert caso_creado is True
    assert caso.id_paciente == paciente_bd.id_paciente
    assert db_session.query(CasoMorbilidad).count() == 1
