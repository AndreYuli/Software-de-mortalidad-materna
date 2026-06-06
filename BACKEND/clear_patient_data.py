import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

# PostgreSQL connection
pg_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(pg_url)

# Tables containing transaction, patient, and application data
# Note: Catalogs (like cat_*) must NOT be truncated because they are static reference tables
TABLES_TO_CLEAR = [
    "paciente",
    "api_analisis",
    "api_sivigilaimportacion",
]

def clear_data():
    confirm = input("¿Estás seguro de que deseas vaciar todos los datos de pacientes, casos y análisis? (s/n): ")
    if confirm.lower() not in ('s', 'si', 'y', 'yes'):
        print("Operación cancelada.")
        return

    try:
        with engine.begin() as conn:
            # We use TRUNCATE ... RESTART IDENTITY CASCADE to empty the tables,
            # reset auto-increment counters, and cascade deletions to all child tables
            tables_str = ", ".join(TABLES_TO_CLEAR)
            sql = f"TRUNCATE TABLE {tables_str} RESTART IDENTITY CASCADE;"
            conn.execute(text(sql))
            print("¡Éxito! Todas las tablas de pacientes, casos, análisis y usuarios han sido vaciadas.")
            print("Los contadores de IDs incrementales han sido reiniciados a 1.")
            print("Los catálogos de referencia SIVIGILA se han mantenido intactos.")
    except Exception as e:
        print(f"Error al vaciar los datos: {e}")

if __name__ == '__main__':
    clear_data()
