"""Script para limpiar o completar el archivo dummy_mortalidad.xlsx.

Por defecto, elimina las filas que no tienen causa básica CIE-10 (las 9,984 filas incompletas),
dejando las 19,989 filas que están 100% completas y listas para importar en SIVIGILA.
Crea un respaldo (.bak) del archivo original antes de realizar cualquier cambio.

Uso:
    python backend/scripts/limpiar_mortalidad_incompleta.py
    python backend/scripts/limpiar_mortalidad_incompleta.py --rellenar  # Rellena en vez de eliminar
"""

import argparse
import random
import shutil
from pathlib import Path

import pandas as pd

DEFAULT_EXCEL_PATH = (
    Path(__file__).resolve().parent.parent
    / 'media'
    / 'uploads'
    / '2026'
    / '08'
    / 'dummy_mortalidad.xlsx'
)

COL_CAUSA = '10.1 Causa básica CIE-10'

# Catálogos para rellenar si se usa --rellenar
CAT_CONVIVENCIA = ['Unión libre', 'Casada', 'Soltera', 'Separada / Divorciada', 'Viuda']
CAT_ESCOLARIDAD = ['Secundaria', 'Primaria', 'Técnico / Tecnológico', 'Profesional', 'Ninguna']
CAT_REG_FECUNDIDAD = [
    'No usó métodos porque no deseaba',
    'Barrera (preservativo)',
    'Hormonales orales',
    'Dispositivo intrauterino',
    'No usó métodos por desconocimiento',
    'Quirúrgico',
]
CAT_MOMENTO_MUERTE = [
    'Durante el embarazo',
    'Durante el parto',
    'Puerperio < 24 horas',
    'Puerperio > 24 horas',
]
CAUSAS_CIE10 = ['O14.1', 'O15.0', 'O85', 'O08.1', 'O41.1', 'O99.3', 'O26.6', 'O98.0']


def procesar_archivo(file_path: Path, modo_rellenar: bool = False) -> None:
    """Procesa el archivo Excel eliminando o rellenando las filas sin CIE-10.

    Args:
        file_path: Ruta al archivo Excel a limpiar.
        modo_rellenar: Si es True, rellena valores con sintéticos; si es False, elimina filas.
    """
    if not file_path.exists():
        raise FileNotFoundError(f'No se encontró el archivo: {file_path}')

    backup_path = file_path.with_suffix('.xlsx.bak')
    if not backup_path.exists():
        print(f'Creando copia de respaldo en: {backup_path.name} ...')
        shutil.copyfile(file_path, backup_path)
    else:
        print(f'Respaldo existente encontrado en: {backup_path.name}')

    print(f'Leyendo {file_path.name}...')
    df = pd.read_excel(file_path)
    total_inicial = len(df)
    print(f'Total de registros iniciales: {total_inicial}')

    if COL_CAUSA not in df.columns:
        raise ValueError(f"No se encontró la columna '{COL_CAUSA}' en el Excel.")

    mascara_vacias = df[COL_CAUSA].isna()
    n_vacias = mascara_vacias.sum()
    print(f"Filas con '{COL_CAUSA}' vacía: {n_vacias}")

    if n_vacias == 0:
        print('El archivo ya tiene todas las filas completas. No se requieren cambios.')
        return

    if modo_rellenar:
        print('Modo: RELLENAR datos incompletos con valores válidos...')
        rng = random.Random(2026)
        for idx in df[mascara_vacias].index:
            df.at[idx, COL_CAUSA] = rng.choice(CAUSAS_CIE10)
            df.at[idx, '6.1 Convivencia'] = rng.choice(CAT_CONVIVENCIA)
            df.at[idx, '6.3 Escolaridad'] = rng.choice(CAT_ESCOLARIDAD)
            df.at[idx, '6.4 Regulación Fecundidad'] = rng.choice(CAT_REG_FECUNDIDAD)
            df.at[idx, '9.1 Momento de la muerte'] = rng.choice(CAT_MOMENTO_MUERTE)
            df.at[idx, '6.5 Gestaciones'] = rng.randint(1, 4)
            df.at[idx, '6.6 Partos Vaginales'] = rng.randint(0, 2)
            df.at[idx, '6.7 Cesáreas'] = rng.randint(0, 1)
            df.at[idx, '6.8 Muertos'] = 0
            df.at[idx, '6.9 Vivos'] = rng.randint(0, 2)
            df.at[idx, '6.10 Abortos'] = 0
            df.at[idx, '8.1 No. CPN'] = rng.randint(2, 6)
            df.at[idx, '8.2 Semana inicio CPN'] = rng.randint(8, 20)
            df.at[idx, '9.2 Semana gestación'] = rng.randint(24, 40)
        df_resultado = df
        print(f'Se rellenaron {n_vacias} registros.')
    else:
        print('Modo: DEJAR SOLO FILAS COMPLETAS (eliminando las incompletas)...')
        df_resultado = df[~mascara_vacias].copy()
        print(f'Registros conservados (completos): {len(df_resultado)}')
        print(f'Registros incompletos eliminados: {n_vacias}')

    print(f'Guardando cambios en {file_path.name}...')
    df_resultado.to_excel(file_path, index=False)
    print(
        f'¡Listo! El archivo {file_path.name} ahora tiene {len(df_resultado)} filas 100% completas.'
    )


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Limpia o completa filas en dummy_mortalidad.xlsx.'
    )
    parser.add_argument(
        '--path',
        type=Path,
        default=DEFAULT_EXCEL_PATH,
        help='Ruta al archivo Excel (por defecto dummy_mortalidad.xlsx)',
    )
    parser.add_argument(
        '--rellenar',
        action='store_true',
        help='Rellena los registros vacíos con datos sintéticos válidos en vez de borrarlos.',
    )
    args = parser.parse_args()
    procesar_archivo(args.path, modo_rellenar=args.rellenar)


if __name__ == '__main__':
    main()
