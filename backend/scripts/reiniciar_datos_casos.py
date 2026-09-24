"""Vacía los casos y análisis de la base para poder probar el dashboard con datos nuevos.

NO toca usuarios (api_usuario), catálogos (cat_*) ni las tablas de Django/auth. Antes de borrar
exporta cada tabla afectada a CSV en data/local/backup_<fecha>/ (carpeta ignorada por git),
porque en esta máquina no hay pg_dump. Sin --confirmar solo muestra lo que haría.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/reiniciar_datos_casos.py              # simulación
    venv/Scripts/python.exe scripts/reiniciar_datos_casos.py --confirmar  # borra
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import engine  # noqa: E402

# Tablas de partida; el resto (hijas por clave foránea) se calcula solo.
SEMILLAS = [
    'paciente',
    'caso_mortalidad',
    'caso_morbilidad',
    'api_analisis',
    'api_sivigilaimportacion',
    'narrativa_ia',
]
PROTEGIDAS_EXACTAS = {'api_usuario'}
PROTEGIDAS_PREFIJOS = ('cat_', 'django_', 'auth_')

_SQL_DEPENDIENTES = """
WITH RECURSIVE arbol AS (
    SELECT c.oid AS rel
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname = ANY(:semillas)
  UNION
    SELECT f.conrelid
    FROM pg_constraint f
    JOIN arbol a ON f.confrelid = a.rel
    WHERE f.contype = 'f'
)
SELECT DISTINCT c.relname FROM arbol a JOIN pg_class c ON c.oid = a.rel ORDER BY 1
"""


def _es_protegida(tabla: str) -> bool:
    return tabla in PROTEGIDAS_EXACTAS or tabla.startswith(PROTEGIDAS_PREFIJOS)


def main() -> int:
    """Simula o ejecuta el vaciado de casos y devuelve el código de salida."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--confirmar', action='store_true', help='Borra de verdad (sin esto es una simulación).'
    )
    args = parser.parse_args()

    with engine.connect() as conn:
        tablas = [r[0] for r in conn.execute(text(_SQL_DEPENDIENTES), {'semillas': SEMILLAS})]
        protegidas = [t for t in tablas if _es_protegida(t)]
        if protegidas:
            print(f'ABORTADO: dependen de los casos y son protegidas: {protegidas}')
            return 1
        conteos = {t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in tablas}
        usuarios_antes = conn.execute(text('SELECT count(*) FROM api_usuario')).scalar()

    print('Tablas que se vaciarán:')
    for tabla, filas in conteos.items():
        print(f'  {tabla:<40}{filas:>10}')
    print(f'Usuarios (api_usuario), NO se tocan: {usuarios_antes}')

    if not args.confirmar:
        print('\nSimulación: no se borró nada. Repite con --confirmar para borrar.')
        return 0

    carpeta = (
        Path(__file__).resolve().parents[2]
        / 'data'
        / 'local'
        / f'backup_{datetime.now():%Y%m%d_%H%M%S}'
    )
    carpeta.mkdir(parents=True, exist_ok=False)
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        for tabla in tablas:
            with open(carpeta / f'{tabla}.csv', 'w', encoding='utf-8', newline='') as fh:
                cur.copy_expert(f'COPY "{tabla}" TO STDOUT WITH CSV HEADER', fh)
        print(f'\nCopia de seguridad en {carpeta}')
        lista = ', '.join(f'"{t}"' for t in tablas)
        cur.execute(f'TRUNCATE TABLE {lista} RESTART IDENTITY')
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()

    with engine.connect() as conn:
        restantes = {t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in tablas}
        usuarios_despues = conn.execute(text('SELECT count(*) FROM api_usuario')).scalar()
    print(f'Filas restantes en las tablas vaciadas: {sum(restantes.values())}')
    print(f'Usuarios: {usuarios_antes} -> {usuarios_despues}')
    return 0 if sum(restantes.values()) == 0 and usuarios_antes == usuarios_despues else 1


if __name__ == '__main__':
    sys.exit(main())
