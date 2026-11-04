"""Genera `sivigila_maternidad_postgres.sql` desde los modelos: una sola fuente de verdad.

El script resultante reconstruye la base de datos COMPLETA en una base vacía:
tablas, llaves, restricciones e índices (de `db/models_sqlalchemy.py`), datos de los
catálogos (`db/semillas_catalogos.sql`), tablas maestras y CIE-10, funciones y triggers
(`db/auditoria.py`) y las vistas del dashboard (`db/database_views.py`).

Uso (desde `backend/`):
    python scripts/generar_esquema_sql.py            # reescribe el .sql
    python scripts/generar_esquema_sql.py --check    # falla si el .sql está desactualizado

Para reconstruir: crear una base vacía y ejecutar el script sobre ella. El script no
contiene DROP DATABASE ni CREATE DATABASE.
"""

import sys
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from db import models_sqlalchemy  # noqa: E402,F401  (registra los modelos)
from db.auditoria import (  # noqa: E402
    SQL_FUNCIONES,
    sentencia_cie10_por_lotes,
    sentencias_maestras,
    sentencias_triggers,
)
from db.database import Base  # noqa: E402
from db.database_views import VISTAS, sentencias_vistas  # noqa: E402

DESTINO = RAIZ / 'sivigila_maternidad_postgres.sql'
SEMILLAS = RAIZ / 'db' / 'semillas_catalogos.sql'

ENCABEZADO = """\
-- =====================================================================
--  VidaMaterna (MaternAnalytics) - esquema de la base de datos PostgreSQL 14+
--  ARCHIVO GENERADO: no se edita a mano. Fuente: db/models_sqlalchemy.py,
--  db/auditoria.py, db/database_views.py y db/semillas_catalogos.sql.
--  Regenerar:  python scripts/generar_esquema_sql.py   (desde backend/)
--
--  Reconstruir la base:
--    1) Crear una base VACÍA (por ejemplo, desde DBeaver).
--    2) Conectarse a ella y ejecutar este script completo.
--  Este script no borra ni crea bases de datos.
-- =====================================================================

-- El archivo está en UTF-8. Sin esta línea, psql en Windows lo lee con la página de códigos
-- de la consola (WIN1252) y las tildes de los catálogos quedan corruptas ('SÃ­' en vez de 'Sí').
SET client_encoding = 'UTF8';
"""


def generar() -> str:
    """Devuelve el texto completo del script SQL."""
    dialecto = postgresql.dialect()
    partes: list[str] = [ENCABEZADO]

    partes.append('-- SECCIÓN 1 · TABLAS, LLAVES Y RESTRICCIONES\n')
    # Las vistas viven en VistaBase.metadata (db/database.py): aquí solo hay tablas.
    tablas = list(Base.metadata.sorted_tables)
    for tabla in tablas:
        ddl = str(CreateTable(tabla).compile(dialect=dialecto)).strip().replace('%%', '%')
        partes.append(ddl + ';\n')

    partes.append('-- SECCIÓN 2 · ÍNDICES\n')
    for tabla in tablas:
        for indice in sorted(tabla.indexes, key=lambda i: i.name or ''):
            ddl = str(CreateIndex(indice).compile(dialect=dialecto)).strip()
            partes.append(ddl + ';')
    partes.append('')

    partes.append('-- SECCIÓN 3 · DATOS DE LOS CATÁLOGOS (tablas maestras)\n')
    partes.append(SEMILLAS.read_text(encoding='utf-8').split('\n\n', 1)[1].strip() + '\n')

    partes.append('-- SECCIÓN 4 · TABLAS MAESTRAS DE AFILIACIÓN Y EVENTOS\n')
    partes.extend(s + ';' for s in sentencias_maestras())
    partes.append('')

    partes.append('-- SECCIÓN 5 · REFERENCIA CIE-10\n')
    partes.extend(s + ';' for s in sentencia_cie10_por_lotes())
    partes.append('')

    partes.append('-- SECCIÓN 6 · FUNCIONES Y TRIGGERS DE AUDITORÍA\n')
    partes.extend(f.strip() + ';\n' for f in SQL_FUNCIONES)
    partes.extend(s + ';' for s in sentencias_triggers())
    partes.append('')

    partes.append('-- SECCIÓN 7 · VISTAS DEL DASHBOARD\n')
    partes.extend(f'DROP VIEW IF EXISTS {v};' for v in VISTAS)
    partes.extend(s.rstrip(';') + ';\n' for s in sentencias_vistas())
    return '\n'.join(partes).rstrip() + '\n'


def main() -> int:
    """Escribe el script (o, con --check, verifica que no esté desactualizado)."""
    texto = generar()
    if '--check' in sys.argv:
        actual = DESTINO.read_text(encoding='utf-8') if DESTINO.exists() else ''
        if actual != texto:
            print('sivigila_maternidad_postgres.sql está desactualizado: regenéralo.')
            return 1
        print('El script SQL coincide con los modelos.')
        return 0
    DESTINO.write_text(texto, encoding='utf-8', newline='\n')
    print(
        f'Escrito {DESTINO} ({len(texto.splitlines())} líneas, {len(Base.metadata.tables)} tablas)'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
