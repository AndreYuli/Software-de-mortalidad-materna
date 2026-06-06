import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

if DB_ENGINE not in ('postgresql', 'postgres'):
    print("El motor DB_ENGINE en tu archivo .env no es 'postgresql'.")
    print("Asegúrate de cambiar DB_ENGINE=postgresql en el archivo .env primero.")
    exit(1)

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')

# Conectarse a la base de datos default de Postgres para poder crear la base de datos destino
postgres_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"

try:
    # PostgreSQL requiere ejecutar CREATE DATABASE fuera de una transacción (autocommit)
    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # Verificar si existe la base de datos
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
        exists = result.scalar()
        
        if not exists:
            print(f"La base de datos '{DB_NAME}' no existe. Creándola ahora...")
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"¡Base de datos '{DB_NAME}' creada con éxito!")
        else:
            print(f"La base de datos '{DB_NAME}' ya existe. No es necesario crearla.")
            
except Exception as e:
    print("Error al conectar con PostgreSQL:")
    print(e)
    print("\nPor favor, verifica que:")
    print("1. Tu servidor de PostgreSQL esté encendido.")
    print("2. Tu usuario y contraseña en BACKEND/.env sean correctos.")
