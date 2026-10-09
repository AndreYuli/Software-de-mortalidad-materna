import cie10Nombres from './cie10Nombres.json'

export const COLUMNAS_MORTALIDAD = [
  'A. Nombres y Apellidos', 'B. Tipo ID', 'C. Número ID',
  '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
  '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
  '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
  '8.1 No. CPN', '8.2 Semana inicio CPN', '9.1 Momento de la muerte',
  '9.2 Semana gestación', '9.4 Tipo de parto', '10.1 Causa básica CIE-10',
  '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
  'Fecha de Nacimiento',
]

export const COLUMNAS_MORBILIDAD = [
  'Nombres y apellidos', 'Tipo de ID', 'N° identificación',
  'N° gestaciones', 'Partos vaginales', 'Cesáreas', 'Abortos',
  'N° controles prenatales', 'Semanas inicio CPN',
  'Edad gestacional ocurrencia (sem)', 'Momento ocurrencia',
  'Eclampsia', 'Sepsis sistémica severa', 'Hemorragia obstétrica severa',
  'Preeclampsia', 'Ruptura uterina', 'Ingreso UCI', 'Cirugía adicional',
  'Transfusión', 'Total criterios', 'Causa principal CIE-10',
  'Días estancia hospitalaria', 'Días estancia UCI',
  'Fecha de Nacimiento', 'Fecha de egreso',
]

export const ALIAS_COLUMNAS: Record<'morbilidad' | 'mortalidad', Record<string, string[]>> = {
  morbilidad: {
    'Nombres y apellidos': ['Nombre y apellidos', 'Nombres y Apellidos'],
    'Tipo de ID': ['Tipo ID', 'Tipo identificación', 'Tipo de identificación'],
    'N° identificación': ['No identificación', 'Nro identificación', 'Nº identificación', 'Número identificación', 'Numero identificacion'],
    'N° gestaciones': ['No gestaciones', 'Nro gestaciones', 'Nº gestaciones', 'Numero gestaciones'],
    'Partos vaginales': ['Partos Vaginales'],
    'Cesáreas': ['Cesareas'],
    'N° controles prenatales': ['No controles prenatales', 'Nro controles prenatales', 'Nº controles prenatales', 'Numero controles prenatales'],
    'Causa principal CIE-10': ['Causa principal cie10', 'Causa principal CIE10'],
    'Días estancia hospitalaria': ['Dias estancia hospitalaria'],
    'Días estancia UCI': ['Dias estancia UCI'],
    'Fecha de Nacimiento': [
      'Fecha de nacimiento',
      'Fecha nacimiento',
      'Fecha de nacimiento (dd/mm/aaaa)',
      'Fecha nacimiento (dd/mm/aaaa)',
    ],
    'Fecha de egreso': [
      'Fecha egreso',
      'Fecha de egreso (dd/mm/aaaa)',
      'Fecha egreso (dd/mm/aaaa)',
    ],
  },
  mortalidad: {
    'B. Tipo ID': ['B. Tipo de ID', 'B Tipo ID'],
    'C. Número ID': ['C. Numero ID', 'C Número ID'],
    '8.1 No. CPN': ['8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN'],
    'Fecha de Nacimiento': [
      'Fecha de nacimiento',
      'Fecha nacimiento',
      'Fecha de nacimiento (dd/mm/aaaa)',
      'Fecha nacimiento (dd/mm/aaaa)',
    ],
  },
}

// Plantilla oficial descargable (archivos en public/plantillas).
export const PLANTILLAS: Record<'morbilidad' | 'mortalidad', { archivo: string; nombre: string }> = {
  mortalidad: { archivo: 'plantilla_mortalidad_550.xlsx', nombre: 'Ficha 550 · Mortalidad Materna' },
  morbilidad: { archivo: 'plantilla_morbilidad_549.xlsx', nombre: 'Ficha 549 · Morbilidad Materna Extrema' },
}

// Tipo de dato y opciones de cada campo requerido, según la hoja DICCIONARIO de la ficha oficial.
export type InfoCampo = { tipo: string; opciones?: string }
export const TIPOS_CAMPO: Record<'morbilidad' | 'mortalidad', Record<string, InfoCampo>> = {
  mortalidad: {
    'A. Nombres y Apellidos': { tipo: 'Texto' },
    'B. Tipo ID': { tipo: 'Categórica', opciones: 'CC / CE / P / PA / PPT' },
    'C. Número ID': { tipo: 'Texto', opciones: 'sin espacios ni caracteres especiales' },
    'Fecha de Nacimiento': { tipo: 'Fecha', opciones: 'dd/mm/aaaa' },
    '5.1 Sitio de Defunción': { tipo: 'Categórica', opciones: 'IPS (hospital/clínica) · IPS (centro/puesto salud) · Lugar de trabajo · Vía pública · Durante traslado · Domicilio · Otro' },
    '6.1 Convivencia': { tipo: 'Categórica', opciones: 'Cónyuge · Familia · Sola · Otro' },
    '6.3 Escolaridad': { tipo: 'Categórica', opciones: 'Ninguna · Primaria · Secundaria · Superior · Sin información' },
    '6.4 Regulación Fecundidad': { tipo: 'Categórica', opciones: 'No usó (desconocimiento/acceso/no deseaba) · Natural · DIU · Hormonal · Barrera · Quirúrgico · Otro' },
    '6.5 Gestaciones': { tipo: 'Número entero', opciones: '1 – 20' },
    '6.6 Partos Vaginales': { tipo: 'Número entero', opciones: '0 – 20' },
    '6.7 Cesáreas': { tipo: 'Número entero', opciones: '0 – 20' },
    '6.8 Muertos': { tipo: 'Número entero', opciones: '0 – 20' },
    '6.9 Vivos': { tipo: 'Número entero', opciones: '0 – 20' },
    '6.10 Abortos': { tipo: 'Número entero', opciones: '0 – 20' },
    '8.1 No. CPN': { tipo: 'Número entero', opciones: '1 – 45' },
    '8.2 Semana inicio CPN': { tipo: 'Número entero', opciones: '1 – 45' },
    '9.1 Momento de la muerte': { tipo: 'Categórica', opciones: 'Gestación · Parto · Puerperio <24h · Puerperio >24h' },
    '9.2 Semana gestación': { tipo: 'Número entero' },
    '9.4 Tipo de parto': { tipo: 'Categórica', opciones: 'Vaginal · Cesárea · Instrumentado · Ignorado' },
    '10.1 Causa básica CIE-10': { tipo: 'Código CIE-10', opciones: 'no acepta códigos que inicien en P' },
    '10.3.1 Demora 1': { tipo: 'Booleana', opciones: 'Sí / No' },
    '10.3.2 Demora 2': { tipo: 'Booleana', opciones: 'Sí / No' },
    '10.3.3 Demora 3': { tipo: 'Booleana', opciones: 'Sí / No' },
    '10.3.4 Demora 4': { tipo: 'Booleana', opciones: 'Sí / No' },
  },
  morbilidad: {
    'Nombres y apellidos': { tipo: 'Texto' },
    'Tipo de ID': { tipo: 'Categórica', opciones: 'CC / CE / P / PPT' },
    'N° identificación': { tipo: 'Número', opciones: 'sin puntos ni espacios' },
    'Fecha de Nacimiento': { tipo: 'Fecha', opciones: 'dd/mm/aaaa' },
    'N° gestaciones': { tipo: 'Número entero', opciones: '0 – 19' },
    'Partos vaginales': { tipo: 'Número entero', opciones: '0 – 19' },
    'Cesáreas': { tipo: 'Número entero', opciones: '0 – 19' },
    'Abortos': { tipo: 'Número entero', opciones: '0 – 19' },
    'N° controles prenatales': { tipo: 'Número entero', opciones: '0 – 50' },
    'Semanas inicio CPN': { tipo: 'Número entero', opciones: '0 – 40' },
    'Edad gestacional ocurrencia (sem)': { tipo: 'Número entero', opciones: '1 – 50' },
    'Momento ocurrencia': { tipo: 'Categórica', opciones: 'Antes · Durante · Después' },
    'Eclampsia': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Sepsis sistémica severa': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Hemorragia obstétrica severa': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Preeclampsia': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Ruptura uterina': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Ingreso UCI': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Cirugía adicional': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Transfusión': { tipo: 'Booleana', opciones: 'Sí / No' },
    'Total criterios': { tipo: 'Número entero', opciones: '1 – 14 (suma de criterios en Sí)' },
    'Causa principal CIE-10': { tipo: 'Código CIE-10' },
    'Días estancia hospitalaria': { tipo: 'Número entero', opciones: '≥ 1' },
    'Días estancia UCI': { tipo: 'Número entero', opciones: '≥ 1 (obligatorio si Ingreso UCI = Sí)' },
    'Fecha de egreso': { tipo: 'Fecha', opciones: 'dd/mm/aaaa' },
  },
}

export const MESES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

export const CIE10_DESCRIPTIONS: Record<string, string> = cie10Nombres

export const CLUSTER_COLORS = ['#662d90', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad']

export function getCie10Description(code: unknown): string {
  const normalized = String(code ?? '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (!normalized) return 'Descripción no disponible';
  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized];
  const prefix3 = normalized.slice(0, 3);
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3];
  // El catálogo oficial marca las categorías de 3 caracteres sin subdivisión
  // con una "X" de relleno (p. ej. 'O85X'), mientras que los datos de origen
  // suelen traer el código sin ese relleno (p. ej. 'O85').
  if (normalized.length === 3 && CIE10_DESCRIPTIONS[`${prefix3}X`]) return CIE10_DESCRIPTIONS[`${prefix3}X`];
  return 'Descripción no disponible';
}

export function getClusterColor(clusterId: number | string): string {
  const idx = typeof clusterId === 'number' ? clusterId : parseInt(String(clusterId), 10);
  if (isNaN(idx) || idx < 0) return '#95a5a6';
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
}
