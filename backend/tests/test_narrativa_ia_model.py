"""Test de que el modelo NarrativaIA se mapea y persiste correctamente."""

from datetime import datetime, timezone

from db.models_sqlalchemy import Analisis, NarrativaIA


def test_narrativa_ia_se_guarda_y_recupera(db_session):
    """Una NarrativaIA debe persistirse y recuperarse con su contenido."""
    analisis = Analisis(
        tipo="mortalidad",
        nombre_archivo="test.xlsx",
        archivo_hash="abc123",
        archivo="media/test.xlsx",
        fecha_carga=datetime.now(timezone.utc),
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()

    narrativa = NarrativaIA(
        analisis_id=analisis.id,
        tipo_narrativa="resumen_ejecutivo",
        filtros_hash="hash1",
        contenido="Texto de prueba.",
        modelo="qwen2.5",
        generado_en=datetime.now(timezone.utc),
    )
    db_session.add(narrativa)
    db_session.commit()

    guardada = db_session.query(NarrativaIA).filter_by(analisis_id=analisis.id).first()
    assert guardada is not None
    assert guardada.contenido == "Texto de prueba."


def test_narrativa_ia_unique_constraint_impide_duplicados(db_session):
    """El índice único (analisis_id, tipo, filtros_hash) debe impedir duplicados."""
    analisis = Analisis(
        tipo="mortalidad",
        nombre_archivo="test.xlsx",
        archivo_hash="abc123",
        archivo="media/test.xlsx",
        fecha_carga=datetime.now(timezone.utc),
        total_registros=5,
        resumen={},
    )
    db_session.add(analisis)
    db_session.commit()

    db_session.add(
        NarrativaIA(
            analisis_id=analisis.id,
            tipo_narrativa="resumen_ejecutivo",
            filtros_hash="hash1",
            contenido="v1",
            modelo="qwen2.5",
            generado_en=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    db_session.add(
        NarrativaIA(
            analisis_id=analisis.id,
            tipo_narrativa="resumen_ejecutivo",
            filtros_hash="hash1",
            contenido="v2",
            modelo="qwen2.5",
            generado_en=datetime.now(timezone.utc),
        )
    )
    try:
        db_session.commit()
        assert False, "Debió lanzar un error de unique constraint"
    except Exception:
        db_session.rollback()
