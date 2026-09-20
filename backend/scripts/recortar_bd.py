"""Script to truncate the database to keep the top 50 cases."""

from sqlalchemy import text

from db.database import SessionLocal

db = SessionLocal()
try:
    print('Recortando base de datos a 50 casos de morbilidad y 50 de mortalidad...')

    # 1. Limpiar análisis, importaciones y narrativas IA
    db.execute(text('TRUNCATE TABLE narrativa_ia, api_analisis, api_sivigilaimportacion CASCADE;'))

    # 2. Seleccionar los IDs de los 50 casos a conservar
    morb_ids = [
        r[0]
        for r in db.execute(
            text('SELECT id_caso FROM caso_morbilidad ORDER BY id_caso LIMIT 50')
        ).fetchall()
    ]
    mort_ids = [
        r[0]
        for r in db.execute(
            text('SELECT id_caso FROM caso_mortalidad ORDER BY id_caso LIMIT 50')
        ).fetchall()
    ]

    morb_str = ','.join(map(str, morb_ids))
    mort_str = ','.join(map(str, mort_ids))

    # 3. Eliminar registros dependientes de morbilidad fuera del top 50
    db.execute(text(f'DELETE FROM causas_morbilidad WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM manejo_hospitalario WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM criterios_manejo WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM criterios_enfermedad WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM criterios_falla_organica WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM referencia WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM antecedentes_obstetricos WHERE id_caso NOT IN ({morb_str})'))
    db.execute(text(f'DELETE FROM caso_morbilidad WHERE id_caso NOT IN ({morb_str})'))

    # 4. Eliminar registros dependientes de mortalidad fuera del top 50
    db.execute(text(f'DELETE FROM causa_muerte WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM antecedente_materno WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM antecedente_riesgo WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM complicacion_embarazo WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM control_prenatal WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM antecedente_parto_puerperio WHERE id_caso NOT IN ({mort_str})'))
    db.execute(text(f'DELETE FROM caso_mortalidad WHERE id_caso NOT IN ({mort_str})'))

    # 5. Limpiar pacientes sin casos
    db.execute(
        text("""
        DELETE FROM paciente
        WHERE id_paciente NOT IN (SELECT id_paciente FROM caso_morbilidad)
          AND id_paciente NOT IN (SELECT id_paciente FROM caso_mortalidad)
    """)
    )

    db.commit()
    print('¡Base de datos recortada con éxito!')
    print('Total Morbilidad:', db.execute(text('SELECT COUNT(*) FROM caso_morbilidad')).scalar())
    print('Total Mortalidad:', db.execute(text('SELECT COUNT(*) FROM caso_mortalidad')).scalar())
    print('Total Pacientes:', db.execute(text('SELECT COUNT(*) FROM paciente')).scalar())

except Exception as e:
    db.rollback()
    print('Error al recortar la base de datos:', e)
finally:
    db.close()
