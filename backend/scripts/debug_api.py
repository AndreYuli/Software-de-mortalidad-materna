"""Script de depuración: consulta el listado de análisis de la API local."""

import json
import urllib.request


def main() -> None:
    """Ejecuta la consulta a la API local."""
    try:
        req = urllib.request.Request("http://localhost:8000/api/analisis/")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("Analisis List:", data)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()
