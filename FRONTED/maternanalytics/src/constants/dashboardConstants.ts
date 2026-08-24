export const COLUMNAS_MORTALIDAD = [
  'A. Nombres y Apellidos', 'B. Tipo ID', 'C. Número ID',
  '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
  '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
  '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
  '8.1 No. CPN', '8.2 Semana inicio CPN', '9.1 Momento de la muerte',
  '9.2 Semana gestación', '9.4 Tipo de parto', '10.1 Causa básica CIE-10',
  '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
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
  },
  mortalidad: {
    'B. Tipo ID': ['B. Tipo de ID', 'B Tipo ID'],
    'C. Número ID': ['C. Numero ID', 'C Número ID'],
    '8.1 No. CPN': ['8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN'],
  },
}

export const MESES_ES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

export const CIE10_DESCRIPTIONS: Record<string, string> = {
  'O14': 'Hipertensión gestacional con preeclampsia',
  'O14.1': 'Hipertensión gestacional con preeclampsia severa',
  'O15': 'Eclampsia',
  'O15.0': 'Eclampsia en el embarazo',
  'O72': 'Hemorragia posparto',
  'O72.1': 'Hemorragia posparto inmediata',
  'O85': 'Sepsis puerperal',
  'O88': 'Embolia obstétrica',
  'O94': 'Secuelas de complicaciones obstétricas',
  'O98': 'Infecciones maternas que complican el embarazo',
  'O98.0': 'Tuberculosis en embarazo',
  'O41.1': 'Corioamnionitis (Infección de saco amniótico)',
  'O08.1': 'Hemorragia por aborto o ectópico',
  'O44.0': 'Placenta previa con hemorragia',
  'O99.3': 'Trastornos mentales o nerviosos en embarazo',
  'O26.6': 'Trastornos del hígado en embarazo',
  'O10.0': 'Hipertensión crónica preexistente',
  'O20.0': 'Amenaza de aborto',
  'O00.1': 'Embarazo ectópico tubárico',
  'O36.4': 'Muerte fetal intrauterina',
  'O62.1': 'Inercia uterina / fallo contracción',
  'O34.2': 'Cicatriz uterina por cesárea previa',
  'O11': 'Hipertensión crónica con preeclampsia sobreagregada',
  'O46.0': 'Hemorragia anteparto con coagulopatía',
  'O24.4': 'Diabetes gestacional',
}

export const CLUSTER_COLORS = ['#0066cc', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad']

export function getCie10Description(code: unknown): string {
  const normalized = String(code ?? '').trim().toUpperCase().replace(/\s+/g, '');
  if (!normalized) return 'Descripción no disponible';
  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized];
  const prefix3 = normalized.slice(0, 3);
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3];
  return 'Descripción no disponible';
}

export function getClusterColor(clusterId: number | string): string {
  const idx = typeof clusterId === 'number' ? clusterId : parseInt(String(clusterId), 10);
  if (isNaN(idx) || idx < 0) return '#95a5a6';
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
}
