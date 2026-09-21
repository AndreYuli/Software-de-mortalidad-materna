"""Genera Excels de prueba con proporciones creíbles para revisar el dashboard.

A diferencia de `generar_excels_prueba.py` (elecciones uniformes, pensado para probar la carga),
aquí las causas, edades, zona, etnia y afiliación siguen distribuciones sesgadas y la relación
entre morbilidad materna extrema y muertes maternas es de 50 a 1, del orden de lo que reportan
las cifras oficiales. Los valores sociodemográficos son los de los catálogos de la base.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/generar_excels_realistas.py
Escribe data/pruebas/realista_mortalidad_550.xlsx y data/pruebas/realista_morbilidad_549.xlsx.
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generar_excels_prueba as base  # noqa: E402

N_MORTALIDAD_DEFECTO = 60
N_MORBILIDAD_DEFECTO = 3000
FECHA_INICIO = date(2025, 1, 1)
FECHA_FIN = date(2026, 8, 31)
SEMILLA = 2026

_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'

CATALOGO_ZONA = ['Urbana', 'Rural']
CATALOGO_ETNIA = ['Ninguna', 'Indígena', 'Afrocolombiana', 'Rrom', 'Raizal', 'Otra']
CATALOGO_POBLACION_VULNERABLE = [
    'Ninguna',
    'Migrante',
    'Indígena',
    'Afro',
    'Discapacidad',
    'Víctima de conflicto',
    'Desplazada',
]
CATALOGO_AFILIACION = ['Contributivo', 'Subsidiado', 'No afiliada']

# Pesos relativos (no hace falta que sumen 100).
_PESOS_ZONA = [72, 28]
_PESOS_ETNIA = [78, 9, 10, 0.5, 1, 1.5]
_PESOS_POBLACION_VULNERABLE = [70, 10, 4, 3, 3, 4, 6]
_PESOS_AFILIACION = [43, 52, 5]

# O14.1 preeclampsia severa, O15.0 eclampsia, O85 sepsis puerperal, O08.1 hemorragia tras aborto.
_CAUSAS_MORTALIDAD = {
    'O14.1': 24,
    'O15.0': 14,
    'O85': 14,
    'O08.1': 12,
    'O41.1': 9,
    'O99.3': 6,
    'O26.6': 6,
    'O98.0': 5,
    'O94': 5,
    'O44.0': 5,
}
_CAUSAS_MORBILIDAD = {
    'O14.1': 26,
    'O14.0': 14,
    'O46.0': 12,
    'O15.0': 10,
    'O85': 8,
    'O20.0': 8,
    'O34.2': 8,
    'O41.1': 6,
    'O10.0': 4,
    'O36.4': 4,
}
_EDADES_MORTALIDAD = {
    16: 5,
    17: 5,
    18: 6,
    22: 8,
    25: 9,
    27: 9,
    29: 9,
    31: 9,
    33: 9,
    36: 11,
    38: 10,
    41: 10,
}
_EDADES_MORBILIDAD = {
    16: 4,
    18: 6,
    20: 8,
    23: 10,
    26: 12,
    28: 12,
    30: 12,
    32: 11,
    34: 10,
    37: 8,
    39: 7,
}
# Semanas de gestación: más casos a término (37-41) que en el resto.
_SEMANAS = list(range(20, 43))
_PESOS_SEMANAS = [1 if s < 28 else 2 if s < 37 else 4 if s < 42 else 1 for s in _SEMANAS]


def _fechas(rng: random.Random, n: int) -> list[date]:
    dias = (FECHA_FIN - FECHA_INICIO).days
    return [FECHA_INICIO + timedelta(days=rng.randint(0, dias)) for _ in range(n)]


def _aplicar_sociodemografia(df: pd.DataFrame, rng: random.Random) -> None:
    n = len(df)
    df['Zona de residencia'] = rng.choices(CATALOGO_ZONA, weights=_PESOS_ZONA, k=n)
    df['Población vulnerable'] = rng.choices(
        CATALOGO_POBLACION_VULNERABLE, weights=_PESOS_POBLACION_VULNERABLE, k=n
    )
    df['Etnia'] = rng.choices(CATALOGO_ETNIA, weights=_PESOS_ETNIA, k=n)
    df['Tipo de afiliación'] = rng.choices(CATALOGO_AFILIACION, weights=_PESOS_AFILIACION, k=n)


def _aplicar_fechas_y_edades(
    df: pd.DataFrame, rng: random.Random, columna_fecha: str, pesos_edad: dict[int, int]
) -> None:
    n = len(df)
    fechas = _fechas(rng, n)
    edades = rng.choices(list(pesos_edad.keys()), weights=list(pesos_edad.values()), k=n)
    df[columna_fecha] = [base._fmt(f) for f in fechas]
    df['Fecha de Nacimiento'] = [
        base._fmt(base._fecha_nacimiento_para_edad(f, e)) for f, e in zip(fechas, edades)
    ]


def generar_mortalidad_realista(n: int, rng: random.Random) -> pd.DataFrame:
    """N muertes maternas con causas, edades y sociodemografía sesgadas."""
    random.seed(
        rng.getrandbits(32)
    )  # las funciones base usan el generador global: se fija desde `rng`
    df = base.generar_mortalidad(n)
    df['10.1 Causa básica CIE-10'] = rng.choices(
        list(_CAUSAS_MORTALIDAD), weights=list(_CAUSAS_MORTALIDAD.values()), k=n
    )
    df['9.2 Semana gestación'] = rng.choices(_SEMANAS, weights=_PESOS_SEMANAS, k=n)
    _aplicar_fechas_y_edades(df, rng, '5.2 Fecha de defunción', _EDADES_MORTALIDAD)
    _aplicar_sociodemografia(df, rng)
    return df


def generar_morbilidad_realista(n: int, rng: random.Random) -> pd.DataFrame:
    """N casos de morbilidad materna extrema con causas, edades y sociodemografía sesgadas."""
    random.seed(
        rng.getrandbits(32)
    )  # las funciones base usan el generador global: se fija desde `rng`
    df = base.generar_morbilidad(n)
    df['Causa principal CIE-10'] = rng.choices(
        list(_CAUSAS_MORBILIDAD), weights=list(_CAUSAS_MORBILIDAD.values()), k=n
    )
    df['Edad gestacional ocurrencia (sem)'] = rng.choices(_SEMANAS, weights=_PESOS_SEMANAS, k=n)
    _aplicar_fechas_y_edades(df, rng, 'Fecha de egreso', _EDADES_MORBILIDAD)
    _aplicar_sociodemografia(df, rng)
    return df


def main() -> None:
    """Genera y escribe los dos Excels realistas."""
    rng = random.Random(SEMILLA)
    df_mort = generar_mortalidad_realista(N_MORTALIDAD_DEFECTO, rng)
    df_morb = generar_morbilidad_realista(N_MORBILIDAD_DEFECTO, rng)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ruta_mort = _OUTPUT_DIR / 'realista_mortalidad_550.xlsx'
    ruta_morb = _OUTPUT_DIR / 'realista_morbilidad_549.xlsx'
    df_mort.to_excel(ruta_mort, index=False)
    df_morb.to_excel(ruta_morb, index=False)
    print(f'Escrito {ruta_mort} ({len(df_mort)} filas)')
    print(f'Escrito {ruta_morb} ({len(df_morb)} filas)')
    print(f'Relación MME/MM: {len(df_morb) / len(df_mort):.0f}:1')


if __name__ == '__main__':
    main()
