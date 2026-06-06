import os
import sqlite3
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, insert
from api_fastapi.models_sqlalchemy import Base

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

if DB_ENGINE not in ('postgresql', 'postgres'):
    print("Error: DB_ENGINE is not set to 'postgresql' or 'postgres' in .env.")
    print("Please configure .env first to connect to your PostgreSQL database.")
    exit(1)

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')

# Connect to target Postgres
pg_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
pg_engine = create_engine(pg_url)

# Connect to source SQLite
sqlite_path = BASE_DIR / 'db.sqlite3'
if not sqlite_path.exists():
    print(f"Error: Source SQLite database not found at {sqlite_path}")
    exit(1)

print(f"Connecting to SQLite database: {sqlite_path}")
sqlite_conn = sqlite3.connect(sqlite_path)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# Tables in topological order to respect foreign key constraints
TABLES_IN_ORDER = [
    # 1. Catalogs (No foreign keys)
    ('cat_convivencia', 'id'),
    ('cat_escolaridad', 'id'),
    ('cat_fuente_causa_muerte', 'id'),
    ('cat_grupo_causa', 'id'),
    ('cat_momento_muerte', 'id'),
    ('cat_nivel_atencion', 'id'),
    ('cat_personal_salud', 'id'),
    ('cat_regulacion_fecundidad', 'id'),
    ('cat_remisiones', 'id'),
    ('cat_sitio_defuncion', 'id'),
    ('cat_terminacion_gestacion', 'id'),
    ('cat_tipo_id', 'id'),
    ('cat_tipo_parto', 'id'),
    
    # 2. Patients (References cat_tipo_id)
    ('paciente', 'id_paciente'),
    
    # 3. Cases (References paciente)
    ('caso_morbilidad', 'id_caso'),
    ('caso_mortalidad', 'id_caso'),
    
    # 4. Related (References cases and catalogs)
    ('referencia', 'id_referencia'),
    ('antecedentes_obstetricos', 'id_antecedente'),
    ('criterios_enfermedad', 'id_criterio_enf'),
    ('criterios_falla_organica', 'id_criterio_falla'),
    ('criterios_manejo', 'id_criterio_man'),
    ('manejo_hospitalario', 'id_manejo'),
    ('causas_morbilidad', 'id_causa'),
    ('antecedente_materno', 'id_antecedente'),
    ('antecedente_riesgo', 'id_antecedente'),
    ('complicacion_embarazo', 'id_complicacion'),
    ('control_prenatal', 'id_control'),
    ('antecedente_parto_puerperio', 'id_antecedente'),
    ('causa_muerte', 'id_causa'),
    
    # 5. Core application metadata and auth
    ('api_analisis', 'id'),
    ('api_sivigilaimportacion', 'id'),
    ('api_usuario', 'id')
]

def migrate():
    # First check if destination has tables
    # (FastAPI server should be started once before running this script to execute create_all)
    try:
        with pg_engine.connect() as pg_conn:
            # Test a query
            pg_conn.execute(text("SELECT 1 FROM cat_tipo_id LIMIT 1"))
    except Exception as e:
        print("Error connecting to PostgreSQL or target tables do not exist yet.")
        print("Please start the FastAPI server first once to create all the database tables:")
        print("  venv\\Scripts\\uvicorn api_fastapi.main:app --reload")
        print(f"Details: {e}")
        return

    print("Beginning migration of data from SQLite to PostgreSQL...")
    
    with pg_engine.begin() as pg_conn:
        # Disable all constraints temporarily for import
        try:
            pg_conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        except Exception:
            pass

        for table_name, pk_col in TABLES_IN_ORDER:
            # Check if table exists in SQLite
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            if not sqlite_cursor.fetchone():
                print(f" - Table {table_name} does not exist in SQLite source. Skipping.")
                continue

            # Read SQLite data
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f" - Table {table_name} is empty. Skipping.")
                continue

            print(f" -> Migrating {len(rows)} rows for table: {table_name}")
            
            # Truncate target table in Postgres to prevent duplicates
            pg_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            
            # Convert sqlite.Row objects to dicts, parse JSON fields, and populate missing columns
            table_obj = Base.metadata.tables[table_name]
            data_to_insert = []
            
            for row in rows:
                r_dict = dict(row)
                if table_name == 'api_analisis' and 'resumen' in r_dict:
                    val = r_dict['resumen']
                    if isinstance(val, str):
                        try:
                            r_dict['resumen'] = json.loads(val)
                        except Exception:
                            pass
                
                # Check for columns defined in Postgres but missing in SQLite
                for col in table_obj.columns:
                    col_name = col.name
                    if col_name not in r_dict:
                        if col.nullable:
                            r_dict[col_name] = None
                        else:
                            # It is NOT NULL, so we must supply a default value
                            from sqlalchemy import String, Integer, BigInteger, SmallInteger, Numeric, Boolean
                            if isinstance(col.type, String):
                                r_dict[col_name] = ""
                            elif isinstance(col.type, (Integer, BigInteger, SmallInteger, Numeric)):
                                r_dict[col_name] = 0
                            elif isinstance(col.type, Boolean):
                                r_dict[col_name] = False
                            else:
                                r_dict[col_name] = None
                
                data_to_insert.append(r_dict)
            
            # Use SQLAlchemy insert() construct so types (like JSON) are handled correctly by the dialect/driver
            insert_stmt = insert(table_obj)
            pg_conn.execute(insert_stmt, data_to_insert)

            # Reset sequence generator for tables with serial columns in Postgres
            # Only for tables where PK is an autoincrement integer
            try:
                seq_sql = f"SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_col}'), COALESCE(MAX({pk_col}), 1)) FROM {table_name}"
                pg_conn.execute(text(seq_sql))
            except Exception as e:
                # Some tables might not have serial PKs (e.g. static catalogs with fixed SmallInteger IDs)
                pass

    print("\nSuccess! Data migration completed successfully.")
    print("All catalogs, patients, cases, and analysis metadata have been copied to PostgreSQL.")

if __name__ == '__main__':
    migrate()
    sqlite_conn.close()
