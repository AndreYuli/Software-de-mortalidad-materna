"""Generador de datos sintéticos para probar Fase 0 (columnas sociodemográficas).

Uso:
    cd backend
    python scripts/generar_datos_sinteticos_fase0.py

Genera dos archivos Excel en data/pruebas/:
    - prueba_mortalidad_550_con_sociodemo.xlsx
    - prueba_morbilidad_549_con_sociodemo.xlsx

Ambos incluyen las 4 columnas nuevas:
    Zona de residencia, Población vulnerable, Etnia, Tipo de afiliación
"""

import sys
from pathlib import Path

import pandas as pd

# Agregar el directorio padre al path para importar column_validators
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# -----------------------------------------------------------------------
# Constantes
# -----------------------------------------------------------------------

ZONA_RESIDENCIA = ['Urbana', 'Rural']
POBLACION_VULNERABLE = [
    'Ninguna',
    'Migrante',
    'Indígena',
    'Afro',
    'Discapacidad',
    'Víctima de conflicto',
    'Desplazada',
]
ETNIA = ['Ninguna', 'Indígena', 'Afrocolombiana', 'Rrom', 'Raizal', 'Otra']
TIPO_AFILIACION = ['Contributivo', 'Subsidiado', 'No afiliada']

DATOS_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'

# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------


def _valores_unicos(lista: list[str], n: int, seed: int = 0) -> list[str]:
    """Reparte valores de forma cíclica con ligera variación."""
    return [lista[(i + seed) % len(lista)] for i in range(n)]


def _valores_con_nulos(lista: list[str], n: int, pct_nulos: float = 0.1, seed: int = 0) -> list:
    """Como _valores_unicos pero con algunos None."""
    vals = _valores_unicos(lista, n, seed)
    import random

    random.seed(seed)
    indices_nulos = random.sample(range(n), int(n * pct_nulos))
    for idx in indices_nulos:
        vals[idx] = None
    return vals


# -----------------------------------------------------------------------
# Generador de morbilidad
# -----------------------------------------------------------------------


def generar_morbilidad(n: int = 20) -> pd.DataFrame:
    """Genera un DataFrame sintético de morbilidad con columnas sociodemo."""
    random_state = 42

    import numpy as np

    rng_np = np.random.default_rng(random_state)

    data = {
        'Nombres y apellidos': [f'Paciente MME {i+1}' for i in range(n)],
        'Tipo de ID': ['CC'] * n,
        'N° identificación': [f'1000{i:04d}' for i in range(n)],
        'Fecha de Nacimiento': pd.date_range('1990-01-01', periods=n, freq='YE'),
        'Fecha de egreso': pd.date_range('2025-06-01', periods=n, freq='3D'),
        'N° gestaciones': rng_np.integers(1, 6, size=n).tolist(),
        'Partos vaginales': rng_np.integers(0, 3, size=n).tolist(),
        'Cesáreas': rng_np.integers(0, 2, size=n).tolist(),
        'Abortos': [0] * n,
        'N° controles prenatales': rng_np.integers(2, 10, size=n).tolist(),
        'Semanas inicio CPN': rng_np.integers(6, 20, size=n).tolist(),
        'Edad gestacional ocurrencia (sem)': rng_np.integers(20, 42, size=n).tolist(),
        'Momento ocurrencia': rng_np.choice([1, 2, 3], size=n).tolist(),
        'Eclampsia': rng_np.choice([0, 1], size=n, p=[0.7, 0.3]).tolist(),
        'Sepsis sistémica severa': rng_np.choice([0, 1], size=n, p=[0.8, 0.2]).tolist(),
        'Hemorragia obstétrica severa': rng_np.choice([0, 1], size=n, p=[0.6, 0.4]).tolist(),
        'Preeclampsia': rng_np.choice([0, 1], size=n, p=[0.5, 0.5]).tolist(),
        'Ruptura uterina': [0] * n,
        'Ingreso UCI': rng_np.choice([0, 1], size=n, p=[0.4, 0.6]).tolist(),
        'Cirugía adicional': rng_np.choice([0, 1], size=n, p=[0.7, 0.3]).tolist(),
        'Transfusión': rng_np.choice([0, 1], size=n, p=[0.6, 0.4]).tolist(),
        'Total criterios': rng_np.integers(2, 8, size=n).tolist(),
        'Causa principal CIE-10': rng_np.choice(
            ['O14.1', 'O72.1', 'O08.0', 'O15.0', 'O67.9'], size=n
        ).tolist(),
        'Días estancia hospitalaria': rng_np.integers(3, 20, size=n).tolist(),
        'Días estancia UCI': rng_np.integers(1, 10, size=n).tolist(),
        # --- Columnas sociodemográficas Fase 0 ---
        'Zona de residencia': _valores_con_nulos(ZONA_RESIDENCIA, n, pct_nulos=0.05, seed=1),
        'Población vulnerable': _valores_con_nulos(POBLACION_VULNERABLE, n, pct_nulos=0.1, seed=2),
        'Etnia': _valores_con_nulos(ETNIA, n, pct_nulos=0.05, seed=3),
        'Tipo de afiliación': _valores_con_nulos(TIPO_AFILIACION, n, pct_nulos=0.05, seed=4),
    }

    return pd.DataFrame(data)


# -----------------------------------------------------------------------
# Generador de mortalidad
# -----------------------------------------------------------------------


def generar_mortalidad(n: int = 15) -> pd.DataFrame:
    """Genera un DataFrame sintético de mortalidad con columnas sociodemo."""
    import numpy as np

    rng_np = np.random.default_rng(99)

    data = {
        'A. Nombres y Apellidos': [f'Paciente MM {i+1}' for i in range(n)],
        'B. Tipo ID': ['CC'] * n,
        'C. Número ID': [f'2000{i:04d}' for i in range(n)],
        'Fecha de Nacimiento': pd.date_range('1988-01-01', periods=n, freq='YE'),
        '5.1 Sitio de Defunción': rng_np.choice(
            ['IPS (hospital/clínica)', 'Domicilio', 'Vía pública', 'Durante el traslado'], size=n
        ).tolist(),
        '5.2 Fecha de defunción': pd.date_range('2025-07-01', periods=n, freq='5D'),
        '6.1 Convivencia': rng_np.choice(['Cónyuge', 'Familia', 'Sola', 'Otro'], size=n).tolist(),
        '6.3 Escolaridad': rng_np.choice(
            ['Ninguna', 'Primaria', 'Secundaria', 'Superior'], size=n
        ).tolist(),
        '6.4 Regulación Fecundidad': rng_np.choice(
            ['No usó métodos por desconocimiento', 'Natural', 'Hormonal', 'Otro'], size=n
        ).tolist(),
        '6.5 Gestaciones': rng_np.integers(1, 8, size=n).tolist(),
        '6.6 Partos Vaginales': rng_np.integers(0, 4, size=n).tolist(),
        '6.7 Cesáreas': rng_np.integers(0, 3, size=n).tolist(),
        '6.8 Muertos': [0] * n,
        '6.9 Vivos': rng_np.integers(0, 4, size=n).tolist(),
        '6.10 Abortos': rng_np.integers(0, 2, size=n).tolist(),
        '8.1 No. CPN': rng_np.integers(0, 10, size=n).tolist(),
        '8.2 Semana inicio CPN': rng_np.integers(8, 28, size=n).tolist(),
        '9.1 Momento de la muerte': rng_np.choice([1, 2, 3, 4], size=n).tolist(),
        '9.2 Semana gestación': rng_np.integers(20, 42, size=n).tolist(),
        '9.4 Tipo de parto': rng_np.choice(
            ['Vaginal', 'Cesárea', 'Instrumentado'], size=n
        ).tolist(),
        '10.1 Causa básica CIE-10': rng_np.choice(
            ['O15.0', 'O72.0', 'O08.0', 'O14.0', 'O88.8'], size=n
        ).tolist(),
        '10.3.1 Demora 1': rng_np.choice([0, 1], size=n, p=[0.5, 0.5]).tolist(),
        '10.3.2 Demora 2': rng_np.choice([0, 1], size=n, p=[0.5, 0.5]).tolist(),
        '10.3.3 Demora 3': rng_np.choice([0, 1], size=n, p=[0.4, 0.6]).tolist(),
        '10.3.4 Demora 4': rng_np.choice([0, 1], size=n, p=[0.6, 0.4]).tolist(),
        # --- Columnas sociodemográficas Fase 0 ---
        'Zona de residencia': _valores_con_nulos(ZONA_RESIDENCIA, n, pct_nulos=0.0, seed=5),
        'Población vulnerable': _valores_con_nulos(POBLACION_VULNERABLE, n, pct_nulos=0.1, seed=6),
        'Etnia': _valores_con_nulos(ETNIA, n, pct_nulos=0.05, seed=7),
        'Tipo de afiliación': _valores_con_nulos(TIPO_AFILIACION, n, pct_nulos=0.05, seed=8),
    }

    return pd.DataFrame(data)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------


def main():
    """Genera los dos Excel sintéticos de prueba en `data/pruebas/`."""
    DATOS_DIR.mkdir(parents=True, exist_ok=True)

    df_morb = generar_morbilidad(n=20)
    out_morb = DATOS_DIR / 'prueba_morbilidad_549_con_sociodemo.xlsx'
    df_morb.to_excel(out_morb, index=False)
    print(f'Generado: {out_morb} ({len(df_morb)} registros)')
    print(
        f"  Columnas sociodemo: Zona={df_morb['Zona de residencia'].notna().sum()}, "
        f"PoblVuln={df_morb['Población vulnerable'].notna().sum()}, "
        f"Etnia={df_morb['Etnia'].notna().sum()}, "
        f"Afiliacion={df_morb['Tipo de afiliación'].notna().sum()}"
    )

    df_mort = generar_mortalidad(n=15)
    out_mort = DATOS_DIR / 'prueba_mortalidad_550_con_sociodemo.xlsx'
    df_mort.to_excel(out_mort, index=False)
    print(f'Generado: {out_mort} ({len(df_mort)} registros)')
    print(
        f"  Columnas sociodemo: Zona={df_mort['Zona de residencia'].notna().sum()}, "
        f"PoblVuln={df_mort['Población vulnerable'].notna().sum()}, "
        f"Etnia={df_mort['Etnia'].notna().sum()}, "
        f"Afiliacion={df_mort['Tipo de afiliación'].notna().sum()}"
    )

    print('\nListo para subir a la plataforma y verificar /completo/.')


if __name__ == '__main__':
    main()
