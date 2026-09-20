"""Script de depuración: inspecciona las columnas de las tablas SIVIGILA en PostgreSQL."""

import os

import psycopg2


def main() -> None:
    """Ejecuta la depuración de base de datos."""
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get("DB_NAME", "sivigila_maternidad"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", ""),
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
        )
        cur = conn.cursor()

        sql_columnas = "SELECT column_name FROM information_schema.columns WHERE table_name = %s"
        cur.execute(sql_columnas, ("caso_mortalidad",))
        print("Mortalidad columns:", cur.fetchall())

        cur.execute(sql_columnas, ("cat_momento_muerte",))
        print("Cat Momento Muerte columns:", cur.fetchall())

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")


if __name__ == "__main__":
    main()
