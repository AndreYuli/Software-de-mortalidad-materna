"""Script to list all tables in the database."""

from sqlalchemy import text

from db.database import SessionLocal

db = SessionLocal()
try:
    print("Obteniendo tablas del sistema...")
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """)
    tables = [r[0] for r in db.execute(query).fetchall()]
    print("Tablas encontradas:", tables)
finally:
    db.close()
