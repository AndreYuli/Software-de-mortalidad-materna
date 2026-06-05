"""Constantes de dominio SIVIGILA compartidas entre vistas y servicios.

Define los nombres de columna canónicos, los alias aceptados y los
mapeos de campos para los eventos 549 (morbilidad) y 550 (mortalidad).
"""

COLUMNA_MOMENTO_MUERTE = '9.1 Momento de la muerte'
COLUMNA_CAUSA_BASICA_CIE10 = '10.1 Causa básica CIE-10'
COLUMNA_TIPO_ID_MORTALIDAD = 'B. Tipo ID'
COLUMNA_NUMERO_ID_MORTALIDAD = 'C. Número ID'
COLUMNA_NUM_CPN_MORTALIDAD = '8.1 No. CPN'

# Columnas mínimas requeridas para el Evento 550 — Mortalidad Materna
COLUMNAS_MORTALIDAD = [
    'A. Nombres y Apellidos',
    COLUMNA_TIPO_ID_MORTALIDAD,
    COLUMNA_NUMERO_ID_MORTALIDAD,
    '5.1 Sitio de Defunción',
    '6.1 Convivencia',
    '6.3 Escolaridad',
    '6.4 Regulación Fecundidad',
    '6.5 Gestaciones',
    '6.6 Partos Vaginales',
    '6.7 Cesáreas',
    '6.8 Muertos',
    '6.9 Vivos',
    '6.10 Abortos',
    COLUMNA_NUM_CPN_MORTALIDAD,
    '8.2 Semana inicio CPN',
    COLUMNA_MOMENTO_MUERTE,
    '9.2 Semana gestación',
    '9.4 Tipo de parto',
    COLUMNA_CAUSA_BASICA_CIE10,
    '10.3.1 Demora 1',
    '10.3.2 Demora 2',
    '10.3.3 Demora 3',
    '10.3.4 Demora 4',
    'Fecha de Nacimiento',
]

# Columnas mínimas requeridas para el Evento 549 — Morbilidad Materna Extrema
COLUMNAS_MORBILIDAD = [
    'Nombres y apellidos',
    'Tipo de ID',
    'N° identificación',
    'N° gestaciones',
    'Partos vaginales',
    'Cesáreas',
    'Abortos',
    'N° controles prenatales',
    'Semanas inicio CPN',
    'Edad gestacional ocurrencia (sem)',
    'Momento ocurrencia',
    'Eclampsia',
    'Sepsis sistémica severa',
    'Hemorragia obstétrica severa',
    'Preeclampsia',
    'Ruptura uterina',
    'Ingreso UCI',
    'Cirugía adicional',
    'Transfusión',
    'Total criterios',
    'Causa principal CIE-10',
    'Días estancia hospitalaria',
    'Días estancia UCI',
    'Fecha de Nacimiento',
    'Fecha de egreso',
]

COLUMNAS_REQUERIDAS = {
    'mortalidad': COLUMNAS_MORTALIDAD,
    'morbilidad': COLUMNAS_MORBILIDAD,
}

# Alias aceptados por columna para tolerar variaciones en archivos de campo.
# Los operadores de campo suelen exportar con nombres ligeramente distintos
# dependiendo de la versión del formulario SIVIGILA que usen.
ALIAS_COLUMNAS = {
    'morbilidad': {
        'Nombres y apellidos': ['Nombre y apellidos', 'Nombres y Apellidos'],
        'Tipo de ID': [
            'Tipo ID', 'Tipo identificación', 'Tipo de identificación',
        ],
        'N° identificación': [
            'No identificación', 'Nro identificación', 'Nº identificación',
            'Número identificación', 'Numero identificacion',
        ],
        'N° gestaciones': [
            'No gestaciones', 'Nro gestaciones',
            'Nº gestaciones', 'Numero gestaciones',
        ],
        'Partos vaginales': ['Partos Vaginales'],
        'Cesáreas': ['Cesareas'],
        'N° controles prenatales': [
            'No controles prenatales', 'Nro controles prenatales',
            'Nº controles prenatales', 'Numero controles prenatales',
        ],
        'Causa principal CIE-10': [
            'Causa principal cie10', 'Causa principal CIE10',
        ],
        'Días estancia hospitalaria': ['Dias estancia hospitalaria'],
        'Días estancia UCI': ['Dias estancia UCI'],
        'Fecha de Nacimiento': ['Fecha de nacimiento', 'Fecha nacimiento'],
        'Fecha de egreso': [
            'Fecha egreso',
            'Fecha de egreso (dd/mm/aaaa)',
            'Fecha egreso (dd/mm/aaaa)',
            'Fecha de egreso (dd/mm/yyyy)',
            'Fecha egreso (dd/mm/yyyy)',
        ],
    },
    'mortalidad': {
        COLUMNA_TIPO_ID_MORTALIDAD: ['B. Tipo de ID', 'B Tipo ID'],
        COLUMNA_NUMERO_ID_MORTALIDAD: ['C. Numero ID', 'C Número ID'],
        COLUMNA_NUM_CPN_MORTALIDAD: [
            '8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN',
        ],
        'Fecha de Nacimiento': [
            'Fecha de nacimiento', 'Fecha nacimiento',
            'Fecha de Nacimiento (dd/mm/aaaa)',
            'Fecha nacimiento (dd/mm/aaaa)',
        ],
        '5.2 Fecha de defunción': [
            '5.2 Fecha defunción', 'Fecha de defunción', 'Fecha defunción',
            '5.2 Fecha de defunción (dd/mm/aaaa)',
            '5.2 Fecha de defuncion (dd/mm/aaaa)',
            '5.2 Fecha de defuncion', '5.2 Fecha defuncion',
            'Fecha de defuncion', 'Fecha defuncion',
        ],
    },
}

# Mapeo campo_bd → columna_excel para reconstruir DataFrame desde
# VMortalidadCompleta. Se usa al construir el archivo autoritativo
# después de persistir nuevos registros.
MORTALIDAD_ANALISIS_MAPPING = {
    'nombres_apellidos': 'A. Nombres y Apellidos',
    'tipo_id': 'B. Tipo ID',
    'numero_id': 'C. Número ID',
    'sitio_defuncion': '5.1 Sitio de Defunción',
    'fecha_defuncion': '5.2 Fecha de defunción',
    'fecha_parto': '9.3 Fecha parto (dd/mm/aaaa)',
    'fecha_nacimiento': 'Fecha de Nacimiento',
    'edad': 'Edad',
    'convivencia': '6.1 Convivencia',
    'escolaridad': '6.3 Escolaridad',
    'regulacion_fecundidad': '6.4 Regulación Fecundidad',
    'gestaciones': '6.5 Gestaciones',
    'partos_vaginales': '6.6 Partos Vaginales',
    'cesareas': '6.7 Cesáreas',
    'nacidos_muertos': '6.8 Muertos',
    'hijos_vivos': '6.9 Vivos',
    'abortos': '6.10 Abortos',
    'num_cpn': '8.1 No. CPN',
    'semana_inicio_cpn': '8.2 Semana inicio CPN',
    'momento_muerte': '9.1 Momento de la muerte',
    'semana_gestacion_muerte': '9.2 Semana gestación',
    'tipo_parto': '9.4 Tipo de parto',
    'causa_basica_cie10': '10.1 Causa básica CIE-10',
    'demora_1': '10.3.1 Demora 1',
    'demora_2': '10.3.2 Demora 2',
    'demora_3': '10.3.3 Demora 3',
    'demora_4': '10.3.4 Demora 4',
}
