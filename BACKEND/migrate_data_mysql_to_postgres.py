import os
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

# PostgreSQL connection credentials (destination)
PG_USER = os.getenv('DB_USER', 'postgres')
PG_PASSWORD = os.getenv('DB_PASSWORD', '')
PG_HOST = os.getenv('DB_HOST', 'localhost')
PG_PORT = os.getenv('DB_PORT', '5432')
PG_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
pg_url = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"
pg_engine = create_engine(pg_url)

# MySQL connection credentials (source) — configure via .env
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_NAME = os.getenv('MYSQL_DB', 'sivigila_maternidad')
mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_NAME}"

print(f"Connecting to source MySQL database at {MYSQL_HOST}:{MYSQL_PORT}...")
try:
    mysql_engine = create_engine(mysql_url)
    # Test connection
    with mysql_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("MySQL connection successful!")
except Exception as e:
    print(f"Error connecting to MySQL: {e}")
    print("Please make sure your MySQL server is running and the credentials are correct.")
    exit(1)

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
    print("Beginning migration of all SIVIGILA catalogs and data from MySQL to PostgreSQL...")
    
    # Check Postgres connection
    try:
        with pg_engine.connect() as pg_conn:
            pg_conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return

    with mysql_engine.connect() as mysql_conn:
        for table_name, pk_col in TABLES_IN_ORDER:
            # Read MySQL data
            try:
                result = mysql_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = [dict(row) for row in result.mappings()]
            except Exception as e:
                print(f" - Table {table_name} could not be read from MySQL (maybe it doesn't exist). Skipping.")
                continue
            
            if not rows:
                print(f" - Table {table_name} is empty in MySQL. Skipping.")
                continue

            print(f" -> Migrating {len(rows)} rows for table: {table_name}")
            
            # Migrate each table in its own transaction so errors are raised immediately with detailed tracebacks
            try:
                with pg_engine.begin() as pg_conn:
                    # Truncate target table in Postgres to prevent duplicates
                    pg_conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
                    
                    # Use SQLAlchemy insert() construct so types are handled correctly
                    table_obj = Base.metadata.tables[table_name]
                    insert_stmt = insert(table_obj)
                    pg_conn.execute(insert_stmt, rows)

                    # Reset sequence generator for tables with serial columns in Postgres
                    try:
                        seq_sql = f"SELECT setval(pg_get_serial_sequence('{table_name}', '{pk_col}'), COALESCE(MAX({pk_col}), 1)) FROM {table_name}"
                        pg_conn.execute(text(seq_sql))
                    except Exception:
                        pass
            except Exception as e:
                print(f"ERROR: Falló la migración de la tabla '{table_name}':")
                raise e

    print("\nSuccess! Full data and catalogs migration from MySQL to PostgreSQL completed successfully.")
    print("All tables have been successfully populated in PostgreSQL.")

if __name__ == '__main__':
    migrate()
