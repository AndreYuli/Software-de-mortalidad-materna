"""Genera Excels de prueba realistas para probar la carga de Mortalidad y Morbilidad.

Crea 4 archivos en data/pruebas/: uno completo y uno con columnas faltantes para
cada evento (549 Morbilidad, 550 Mortalidad), usando exactamente las
columnas requeridas por `_analisis_excel.py` (mismas que valida el backend
y el frontend). Se usa para probar manualmente la carga end-to-end, incluido
el caso de subir el archivo del evento equivocado en el slot contrario.

Uso:
    backend/venv/Scripts/python.exe scripts/generar_excels_prueba.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'

_CAUSAS_MORTALIDAD = [
    'O14.1',
    'O85',
    'O94',
    'O15.0',
    'O98.0',
    'O08.1',
    'O41.1',
    'O44.0',
    'O99.3',
    'O26.6',
]
_CAUSAS_MORBILIDAD = [
    'O14.0',
    'O41.1',
    'O15.0',
    'O34.2',
    'O20.0',
    'O14.1',
    'O10.0',
    'O85',
    'O46.0',
    'O36.4',
]

# Valores tal cual seedeados en cat_sitio_defuncion (sivigila_maternidad_postgres.sql);
# el resolvedor de catálogo es estricto y rechaza cualquier texto que no matchee.
_SITIOS_DEFUNCION = [
    'IPS (hospital/clínica)',
    'IPS (centro/puesto salud)',
    'Lugar de trabajo',
    'Vía pública',
    'Durante traslado',
    'Domicilio',
    'Otro',
]
_CONVIVENCIA = ['Unión libre', 'Casada', 'Soltera', 'Separada', 'Unión libre']
_ESCOLARIDAD = ['Primaria', 'Secundaria', 'Ninguna', 'Técnica', 'Universitaria']
_REGULACION_FECUNDIDAD = ['Ninguno', 'Preservativo', 'DIU', 'Ninguno', 'Inyectable']
_NIVEL_ATENCION = ['Nivel 1', 'Nivel 2', 'Nivel 3']
_TIPO_PARTO = ['Vaginal', 'Cesárea']
_TIPO_ID = ['CC', 'CE', 'TI', 'RC', 'PPT']


def _fecha_aleatoria(inicio: date, fin: date) -> date:
    """Devuelve una fecha aleatoria uniforme entre inicio y fin (inclusive)."""
    dias = (fin - inicio).days
    return inicio + timedelta(days=random.randint(0, dias))


def _fmt(d: date) -> str:
    """Formatea una fecha al formato dd/mm/aaaa usado en los archivos SIVIGILA."""
    return d.strftime('%d/%m/%Y')


def _fecha_nacimiento_para_edad(fecha_evento: date, edad: int) -> date:
    """Calcula una fecha de nacimiento consistente con la edad y la fecha del evento."""
    return fecha_evento.replace(year=fecha_evento.year - edad) - timedelta(
        days=random.randint(0, 300)
    )


def generar_mortalidad(n: int) -> pd.DataFrame:
    """Genera un DataFrame de N casos de mortalidad con todas las columnas requeridas."""
    filas = []
    for i in range(1, n + 1):
        fecha_evento = _fecha_aleatoria(date(2023, 1, 1), date(2025, 12, 31))
        edad = random.choice([16, 17, 18, 22, 25, 27, 29, 31, 33, 36, 38, 41])
        fecha_nac = _fecha_nacimiento_para_edad(fecha_evento, edad)
        semana_gest = random.randint(20, 42)
        filas.append(
            {
                'A. Nombres y Apellidos': f'Paciente Prueba Mortalidad {i:03d}',
                'B. Tipo ID': random.choice(_TIPO_ID),
                'C. Número ID': 1000000000 + i,
                'Fecha de Nacimiento': _fmt(fecha_nac),
                '5.1 Sitio de Defunción': random.choice(_SITIOS_DEFUNCION),
                '5.2 Fecha de defunción': _fmt(fecha_evento),
                '6.1 Convivencia': random.choice(_CONVIVENCIA),
                '6.3 Escolaridad': random.choice(_ESCOLARIDAD),
                '6.4 Regulación Fecundidad': random.choice(_REGULACION_FECUNDIDAD),
                '6.5 Gestaciones': random.randint(1, 5),
                '6.6 Partos Vaginales': random.randint(0, 3),
                '6.7 Cesáreas': random.randint(0, 2),
                '6.8 Muertos': random.randint(0, 1),
                '6.9 Vivos': random.randint(0, 4),
                '6.10 Abortos': random.randint(0, 2),
                '8.1 No. CPN': random.randint(0, 10),
                '8.2 Semana inicio CPN': random.randint(4, 20),
                '9.1 Momento de la muerte': random.randint(1, 4),
                '9.2 Semana gestación': semana_gest,
                '9.4 Tipo de parto': random.choice(_TIPO_PARTO),
                '9.6 Nivel atención parto': random.choice(_NIVEL_ATENCION),
                '10.1 Causa básica CIE-10': random.choice(_CAUSAS_MORTALIDAD),
                '10.3.1 Demora 1': random.choice([1, 1, 2]),
                '10.3.2 Demora 2': random.choice([1, 2, 2]),
                '10.3.3 Demora 3': random.choice([1, 2, 2]),
                '10.3.4 Demora 4': random.choice([1, 2, 2]),
            }
        )
    return pd.DataFrame(filas)


def generar_morbilidad(n: int) -> pd.DataFrame:
    """Genera un DataFrame de N casos de morbilidad con todas las columnas requeridas."""
    filas = []
    for i in range(1, n + 1):
        fecha_evento = _fecha_aleatoria(date(2023, 1, 1), date(2025, 12, 31))
        edad = random.choice([16, 18, 20, 23, 26, 28, 30, 32, 34, 37, 39])
        fecha_nac = _fecha_nacimiento_para_edad(fecha_evento, edad)
        semana_gest = random.randint(20, 42)
        filas.append(
            {
                'Nombres y apellidos': f'Paciente Prueba Morbilidad {i:03d}',
                'Tipo de ID': random.choice(_TIPO_ID),
                'N° identificación': 2000000000 + i,
                'Fecha de Nacimiento': _fmt(fecha_nac),
                'Fecha de egreso': _fmt(fecha_evento),
                'N° gestaciones': random.randint(1, 5),
                'Partos vaginales': random.randint(0, 3),
                'Cesáreas': random.randint(0, 2),
                'Abortos': random.randint(0, 2),
                'N° controles prenatales': random.randint(0, 10),
                'Semanas inicio CPN': random.randint(4, 20),
                'Edad gestacional ocurrencia (sem)': semana_gest,
                'Momento ocurrencia': random.randint(1, 4),
                'Eclampsia': random.choice([1, 2, 2, 2]),
                'Sepsis sistémica severa': random.choice([1, 2, 2, 2]),
                'Hemorragia obstétrica severa': random.choice([1, 2, 2, 2]),
                'Preeclampsia': random.choice([1, 1, 2, 2]),
                'Ruptura uterina': random.choice([1, 2, 2, 2, 2]),
                'Ingreso UCI': random.choice([1, 2, 2]),
                'Cirugía adicional': random.choice([1, 2, 2]),
                'Transfusión': random.choice([1, 2, 2]),
                'Total criterios': random.randint(1, 4),
                'Causa principal CIE-10': random.choice(_CAUSAS_MORBILIDAD),
                'Días estancia hospitalaria': random.randint(1, 15),
                'Días estancia UCI': random.randint(0, 8),
            }
        )
    return pd.DataFrame(filas)


def main() -> None:
    """Genera y escribe los 4 archivos de prueba en data/pruebas/."""
    df_mort = generar_mortalidad(40)
    df_morb = generar_morbilidad(50)

    ruta_mort = _OUTPUT_DIR / 'prueba_mortalidad_550.xlsx'
    ruta_morb = _OUTPUT_DIR / 'prueba_morbilidad_549.xlsx'
    df_mort.to_excel(ruta_mort, index=False)
    df_morb.to_excel(ruta_morb, index=False)
    print(f'Escrito {ruta_mort} ({len(df_mort)} filas, {len(df_mort.columns)} columnas)')
    print(f'Escrito {ruta_morb} ({len(df_morb)} filas, {len(df_morb.columns)} columnas)')

    # Variante incompleta: quita las columnas de demoras y la causa CIE-10 de
    # mortalidad, para probar el mensaje de "columnas faltantes".
    df_mort_incompleta = df_mort.drop(
        columns=[
            '10.1 Causa básica CIE-10',
            '10.3.1 Demora 1',
            '10.3.2 Demora 2',
            '10.3.3 Demora 3',
            '10.3.4 Demora 4',
        ]
    )
    ruta_mort_incompleta = _OUTPUT_DIR / 'prueba_mortalidad_550_incompleta.xlsx'
    df_mort_incompleta.to_excel(ruta_mort_incompleta, index=False)
    n_cols = len(df_mort_incompleta.columns)
    print(f'Escrito {ruta_mort_incompleta} ({n_cols} columnas, faltan 5 requeridas)')

    # Variante incompleta: quita los criterios de inclusión MME y la causa
    # principal CIE-10 de morbilidad.
    df_morb_incompleta = df_morb.drop(
        columns=[
            'Eclampsia',
            'Sepsis sistémica severa',
            'Hemorragia obstétrica severa',
            'Preeclampsia',
            'Causa principal CIE-10',
        ]
    )
    ruta_morb_incompleta = _OUTPUT_DIR / 'prueba_morbilidad_549_incompleta.xlsx'
    df_morb_incompleta.to_excel(ruta_morb_incompleta, index=False)
    n_cols = len(df_morb_incompleta.columns)
    print(f'Escrito {ruta_morb_incompleta} ({n_cols} columnas, faltan 5 requeridas)')


if __name__ == '__main__':
    main()
