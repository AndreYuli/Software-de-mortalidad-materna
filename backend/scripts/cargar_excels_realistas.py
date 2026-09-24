"""Sube por la API los Excels realistas de data/pruebas (requiere el backend en marcha).

Usa el usuario de pruebas del helper e2e (constantes públicas del repo); lo crea si no existe.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/cargar_excels_realistas.py
"""

import sys
from pathlib import Path

import httpx

API_URL = 'http://localhost:8000/api'
EMAIL = 'e2e@vidamaterna.co'
PASSWORD = 'e2e-clave-segura'
_DATOS = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'
_ARCHIVOS = [
    ('mortalidad', _DATOS / 'realista_mortalidad_550.xlsx'),
    ('morbilidad', _DATOS / 'realista_morbilidad_549.xlsx'),
]
_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def main() -> int:
    """Registra (si hace falta) al usuario de pruebas y sube los dos Excels."""
    # 201 si se crea; 400 si ya existía: ambos valen.
    httpx.post(
        f'{API_URL}/auth/register/',
        json={'nombre': 'Usuario E2E', 'email': EMAIL, 'password': PASSWORD},
        timeout=30,
    )
    login = httpx.post(
        f'{API_URL}/auth/login/', json={'email': EMAIL, 'password': PASSWORD}, timeout=30
    )
    login.raise_for_status()
    cabeceras = {'Authorization': f'Bearer {login.json()["access_token"]}'}

    for tipo, ruta in _ARCHIVOS:
        with open(ruta, 'rb') as fh:
            respuesta = httpx.post(
                f'{API_URL}/analisis/',
                data={'tipo': tipo},
                files={'archivo': (ruta.name, fh, _XLSX)},
                headers=cabeceras,
                timeout=900,
            )
        print(f'{tipo}: HTTP {respuesta.status_code}')
        if respuesta.status_code >= 400:
            print(respuesta.text[:500])
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
