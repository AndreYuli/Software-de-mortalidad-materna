import openpyxl
import pandas as pd
import re
import unicodedata
from io import BytesIO
from hashlib import sha256
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.contrib.auth.hashers import check_password, make_password

from .models import Analisis, CasoMorbilidad, CasoMortalidad, Paciente, Usuario, VMorbilidadCompleta, VMortalidadCompleta
from .serializers import (
    AnalisisSerializer,
    MorbilidadCompletaSerializer,
    MortalidadCompletaSerializer,
    PacienteSerializer,
    UploadSerializer,
)
from .processors import (
    MortalidadProcessor, 
    MorbilidadProcessor,
    es_valor_positivo,
    preparar_dataframe_analisis,
    procesar_archivo_analisis
)
from .sivigila_ingestion import persistir_dataframe_sivigila

ERROR_ANALISIS_NO_ENCONTRADO = 'Análisis no encontrado.'
COLUMNA_MOMENTO_MUERTE = '9.1 Momento de la muerte'
COLUMNA_CAUSA_BASICA_CIE10 = '10.1 Causa básica CIE-10'
COLUMNA_TIPO_ID_MORTALIDAD = 'B. Tipo ID'
COLUMNA_NUMERO_ID_MORTALIDAD = 'C. Número ID'
COLUMNA_NUM_CPN_MORTALIDAD = '8.1 No. CPN'

# Columnas requeridas por tipo de evento
COLUMNAS_MORTALIDAD = [
    'A. Nombres y Apellidos', COLUMNA_TIPO_ID_MORTALIDAD, COLUMNA_NUMERO_ID_MORTALIDAD,
    '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
    '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
    '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
    COLUMNA_NUM_CPN_MORTALIDAD, '8.2 Semana inicio CPN', COLUMNA_MOMENTO_MUERTE,
    '9.2 Semana gestación', '9.4 Tipo de parto', COLUMNA_CAUSA_BASICA_CIE10,
    '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
    'Fecha de Nacimiento',
]

# Columnas opcionales que se canonicalizan si están presentes (no bloquean la carga)
COLUMNAS_OPCIONALES_MORTALIDAD = ['5.2 Fecha de defunción']

COLUMNAS_MORBILIDAD = [
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

COLUMNAS_REQUERIDAS = {
    'mortalidad': COLUMNAS_MORTALIDAD,
    'morbilidad': COLUMNAS_MORBILIDAD,
}

ALIAS_COLUMNAS = {
    'morbilidad': {
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
        'Fecha de Nacimiento': ['Fecha de nacimiento', 'Fecha nacimiento'],
        'Fecha de egreso': ['Fecha egreso', 'Fecha de egreso (dd/mm/aaaa)', 'Fecha egreso (dd/mm/aaaa)', 'Fecha de egreso (dd/mm/yyyy)', 'Fecha egreso (dd/mm/yyyy)'],
    },
    'mortalidad': {
        COLUMNA_TIPO_ID_MORTALIDAD: ['B. Tipo de ID', 'B Tipo ID'],
        COLUMNA_NUMERO_ID_MORTALIDAD: ['C. Numero ID', 'C Número ID'],
        COLUMNA_NUM_CPN_MORTALIDAD: ['8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN'],
        'Fecha de Nacimiento': ['Fecha de nacimiento', 'Fecha nacimiento', 'Fecha de Nacimiento (dd/mm/aaaa)', 'Fecha nacimiento (dd/mm/aaaa)'],
        '5.2 Fecha de defunción': [
            '5.2 Fecha defunción', 'Fecha de defunción', 'Fecha defunción',
            '5.2 Fecha de defunción (dd/mm/aaaa)', '5.2 Fecha de defuncion (dd/mm/aaaa)',
            '5.2 Fecha de defuncion', '5.2 Fecha defuncion',
            'Fecha de defuncion', 'Fecha defuncion',
        ],
    },
}


def obtener_limite(request, default=100, maximo=500):
    try:
        limite = int(request.query_params.get('limit', default))
    except (TypeError, ValueError):
        limite = default
    return max(1, min(limite, maximo))


def _seleccionar_fila_encabezados(filas, tipo):
    mejor_fila = []
    mejor_puntaje = -1

    for fila in filas:
        columnas = [str(valor).strip() for valor in fila if valor is not None and str(valor).strip()]
        if not columnas:
            continue

        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, columnas))
        if puntaje > mejor_puntaje:
            mejor_fila = columnas
            mejor_puntaje = puntaje

    return mejor_fila


def _seleccionar_hoja_y_encabezados_openpyxl(workbook, tipo):
    mejor_fila = []
    mejor_puntaje = -1
    mejor_hoja = workbook.active.title

    for hoja in workbook.worksheets:
        filas = [
            [cell.value for cell in row]
            for row in hoja.iter_rows(min_row=1, max_row=5)
        ]
        fila = _seleccionar_fila_encabezados(filas, tipo)
        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, fila)) if fila else -1
        if puntaje > mejor_puntaje:
            mejor_fila = fila
            mejor_puntaje = puntaje
            mejor_hoja = hoja.title

    return mejor_hoja, mejor_fila


def leer_columnas_excel(archivo, tipo):
    """Lee las primeras filas de todas las hojas y retorna la que mejor coincide con las columnas esperadas."""
    try:
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        _, headers = _seleccionar_hoja_y_encabezados_openpyxl(wb, tipo)
        wb.close()
        return headers
    except Exception:
        return None


def _detectar_indice_encabezados_dataframe(df_sin_encabezado, tipo):
    mejor_indice = 0
    mejor_puntaje = -1

    for indice in range(min(5, len(df_sin_encabezado.index))):
        fila = df_sin_encabezado.iloc[indice].tolist()
        columnas = [str(valor).strip() for valor in fila if not pd.isna(valor) and str(valor).strip()]
        if not columnas:
            continue

        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, columnas))
        if puntaje > mejor_puntaje:
            mejor_indice = indice
            mejor_puntaje = puntaje

    return mejor_indice


def _seleccionar_hoja_y_encabezados_dataframe(sheets, tipo):
    mejor_hoja = None
    mejor_indice = 0
    mejor_puntaje = -1

    for nombre_hoja, dataframe in sheets.items():
        indice = _detectar_indice_encabezados_dataframe(dataframe, tipo)
        fila = dataframe.iloc[indice].tolist() if len(dataframe.index) > indice else []
        columnas = [str(valor).strip() for valor in fila if not pd.isna(valor) and str(valor).strip()]
        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, columnas)) if columnas else -1
        if puntaje > mejor_puntaje:
            mejor_hoja = nombre_hoja
            mejor_indice = indice
            mejor_puntaje = puntaje

    return mejor_hoja, mejor_indice


def _leer_dataframe_excel(archivo, tipo):
    archivo.seek(0)
    hojas = pd.read_excel(archivo, engine='openpyxl', header=None, sheet_name=None)
    nombre_hoja, indice_encabezados = _seleccionar_hoja_y_encabezados_dataframe(hojas, tipo)

    archivo.seek(0)
    df = pd.read_excel(archivo, engine='openpyxl', header=indice_encabezados, sheet_name=nombre_hoja)
    return _canonizar_columnas_dataframe(df, tipo)


def _normalizar_encabezado(valor):
    texto = str(valor or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = texto.replace('n°', 'n ').replace('nº', 'n ').replace('no.', 'n ').replace('no ', 'n ')
    texto = re.sub(r'[^a-z0-9]+', ' ', texto)
    return ' '.join(texto.split())


def _construir_mapa_alias(tipo):
    mapa = {}
    for canonical in COLUMNAS_REQUERIDAS[tipo]:
        mapa[_normalizar_encabezado(canonical)] = canonical
    for canonical, alias_list in ALIAS_COLUMNAS.get(tipo, {}).items():
        mapa[_normalizar_encabezado(canonical)] = canonical
        for alias in alias_list:
            mapa[_normalizar_encabezado(alias)] = canonical
    return mapa


def _obtener_columnas_faltantes(tipo, columnas_archivo):
    mapa_alias = _construir_mapa_alias(tipo)
    presentes = {
        mapa_alias[normalizada]
        for columna in columnas_archivo
        for normalizada in [_normalizar_encabezado(columna)]
        if normalizada in mapa_alias
    }
    return [columna for columna in COLUMNAS_REQUERIDAS[tipo] if columna not in presentes]


def _canonizar_columnas_dataframe(df, tipo):
    mapa_alias = _construir_mapa_alias(tipo)
    renames = {}
    for columna in df.columns:
        canonical = mapa_alias.get(_normalizar_encabezado(columna))
        if canonical and canonical != columna and canonical not in df.columns:
            renames[columna] = canonical
    return df.rename(columns=renames)


def calcular_resumen(archivo, tipo):
    """Lee el archivo Excel y calcula estadísticas básicas usando pandas."""
    try:
        df = pd.read_excel(archivo, engine='openpyxl')
        return calcular_resumen_desde_dataframe(df, tipo)
    except Exception:
        return {}


def calcular_resumen_desde_dataframe(df, tipo):
    try:
        df, limpieza = preparar_dataframe_analisis(df)
        resumen = {
            'total_registros': len(df),
            'total_registros_original': limpieza['total_original'],
            'filas_vacias_omitidas': limpieza['filas_vacias_omitidas'],
            'filas_duplicadas_omitidas': limpieza['filas_duplicadas_omitidas'],
        }

        if tipo == 'mortalidad':
            if COLUMNA_MOMENTO_MUERTE in df.columns:
                resumen['distribucion_momento'] = (
                    df[COLUMNA_MOMENTO_MUERTE].value_counts().to_dict()
                )
            if COLUMNA_CAUSA_BASICA_CIE10 in df.columns:
                top5 = df[COLUMNA_CAUSA_BASICA_CIE10].value_counts().head(5).to_dict()
                resumen['top5_causas'] = {str(k): int(v) for k, v in top5.items()}

        elif tipo == 'morbilidad':
            criterios_cols = ['Eclampsia', 'Sepsis sistémica severa',
                              'Hemorragia obstétrica severa', 'Preeclampsia', 'Ruptura uterina']
            presentes = [c for c in criterios_cols if c in df.columns]
            if presentes:
                resumen['criterios_frecuencia'] = {
                    c: int(df[c].apply(es_valor_positivo).sum()) for c in presentes
                }

        return resumen
    except Exception:
        return {}


def calcular_hash_archivo(archivo):
    archivo.seek(0)
    contenido = archivo.read()
    archivo.seek(0)
    return sha256(contenido).hexdigest()


MORTALIDAD_ANALISIS_MAPPING = {
    'nombres_apellidos': 'A. Nombres y Apellidos',
    'tipo_id': 'B. Tipo ID',
    'numero_id': 'C. Número ID',
    'sitio_defuncion': '5.1 Sitio de Defunción',
    'fecha_defuncion': '5.2 Fecha de defunción',
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


def construir_dataframe_analisis_desde_bd(tipo):
    if tipo != 'mortalidad':
        return None

    registros = list(
        VMortalidadCompleta.objects.order_by('id_caso').values(*MORTALIDAD_ANALISIS_MAPPING.keys())
    )
    if not registros:
        return pd.DataFrame(columns=MORTALIDAD_ANALISIS_MAPPING.values())

    dataframe = pd.DataFrame.from_records(registros)
    return dataframe.rename(columns=MORTALIDAD_ANALISIS_MAPPING)


def construir_archivo_analisis_desde_dataframe(df_fuente, tipo, nombre_archivo):
    df_analisis, _ = preparar_dataframe_analisis(df_fuente)
    resumen = calcular_resumen_desde_dataframe(df_analisis, tipo)
    total_registros = resumen.pop('total_registros', len(df_analisis))

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_analisis.to_excel(writer, index=False)

    contenido = buffer.getvalue()
    archivo = ContentFile(contenido, name=nombre_archivo)
    archivo_hash = sha256(contenido).hexdigest()

    return archivo, archivo_hash, resumen, total_registros


def construir_archivo_analisis_acumulado(analisis_existente, df_nuevo, tipo, nombre_archivo):
    dataframes = []

    if analisis_existente is not None and analisis_existente.archivo:
        try:
            analisis_existente.archivo.open('rb')
            df_anterior = pd.read_excel(analisis_existente.archivo, engine='openpyxl')
            dataframes.append(df_anterior)
        except Exception:
            pass
        finally:
            try:
                analisis_existente.archivo.close()
            except Exception:
                pass

    dataframes.append(df_nuevo.copy())
    df_acumulado = pd.concat(dataframes, ignore_index=True) if len(dataframes) > 1 else dataframes[0]
    return construir_archivo_analisis_desde_dataframe(df_acumulado, tipo, nombre_archivo)


def obtener_analisis_unicos(lista):
    unicos = {}
    for analisis in lista:
        clave = analisis.tipo
        existente = unicos.get(clave)
        if existente is None or analisis.fecha_carga > existente.fecha_carga:
            unicos[clave] = analisis
    return sorted(unicos.values(), key=lambda analisis: analisis.fecha_carga, reverse=True)


def procesar_carga_archivo(request):
    serializer = UploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tipo = serializer.validated_data['tipo']
    archivo = serializer.validated_data['archivo']

    columnas_archivo = leer_columnas_excel(archivo, tipo)
    if columnas_archivo is None:
        return Response(
            {'error': 'No se pudo leer el archivo. Verifica que sea un Excel válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    faltantes = _obtener_columnas_faltantes(tipo, columnas_archivo)

    if faltantes:
        return Response(
            {'error': 'Faltan columnas requeridas.', 'columnas_faltantes': faltantes},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        df = _leer_dataframe_excel(archivo, tipo)
    except Exception:
        return Response(
            {'error': 'No se pudo leer el contenido del Excel.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    df, _ = preparar_dataframe_analisis(df)

    try:
        with transaction.atomic():
            analisis_existente = Analisis.objects.filter(tipo=tipo).order_by('-fecha_carga', '-id').first()
            persistencia = persistir_dataframe_sivigila(df, tipo)

            df_autoritativo = construir_dataframe_analisis_desde_bd(tipo)
            if df_autoritativo is not None:
                archivo_analisis, archivo_hash, resumen, total_registros = construir_archivo_analisis_desde_dataframe(
                    df_autoritativo,
                    tipo,
                    archivo.name,
                )
            else:
                archivo_analisis, archivo_hash, resumen, total_registros = construir_archivo_analisis_acumulado(
                    analisis_existente,
                    df,
                    tipo,
                    archivo.name,
                )

            if analisis_existente is None:
                analisis = Analisis.objects.create(
                    tipo=tipo,
                    nombre_archivo=archivo.name,
                    archivo_hash=archivo_hash,
                    archivo=archivo_analisis,
                    total_registros=total_registros,
                    resumen=resumen,
                )
            else:
                analisis_existente.nombre_archivo = archivo.name
                analisis_existente.archivo_hash = archivo_hash
                analisis_existente.archivo = archivo_analisis
                analisis_existente.total_registros = total_registros
                analisis_existente.resumen = resumen
                analisis_existente.fecha_carga = timezone.now()
                analisis_existente.save(update_fields=['nombre_archivo', 'archivo_hash', 'archivo', 'total_registros', 'resumen', 'fecha_carga'])
                analisis = analisis_existente
    except ValueError as error:
        return Response({'error': str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as error:
        return Response(
            {'error': f'No se pudo persistir el archivo en SIVIGILA: {str(error)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = AnalisisSerializer(analisis).data
    data['sivigila'] = persistencia
    return Response(data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def subir_archivo(request):
    """
    POST /api/subir/
    Recibe un archivo Excel (mortalidad o morbilidad), valida columnas
    y guarda el análisis en base de datos.
    """
    return procesar_carga_archivo(request)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def listar_analisis(request):
    """
    GET /api/analisis/
    Retorna todos los análisis guardados (sin el archivo).
    
    POST /api/analisis/
    Recibe un archivo Excel (mortalidad o morbilidad), valida columnas
    y guarda el análisis en base de datos.
    """
    if request.method == 'GET':
        analisis = obtener_analisis_unicos(Analisis.objects.all())
        serializer = AnalisisSerializer(analisis, many=True)
        return Response(serializer.data)

    return procesar_carga_archivo(request)


@api_view(['GET'])
@permission_classes([AllowAny])
def detalle_analisis(request, pk):
    """
    GET /api/analisis/<id>/
    Retorna el detalle de un análisis específico.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': ERROR_ANALISIS_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

    return Response(AnalisisSerializer(analisis).data)


_EXCEL_ORIGIN = pd.Timestamp('1899-12-30')


def _parse_valor_fecha(v):
    """Parsea un valor individual: datetime nativo, serial Excel o string DD/MM/YYYY."""
    if v is None:
        return pd.NaT
    try:
        if pd.isna(v):
            return pd.NaT
    except (TypeError, ValueError):
        pass
    # Ya es un objeto fecha/datetime
    if hasattr(v, 'date') or hasattr(v, 'year'):
        try:
            return pd.Timestamp(v)
        except Exception:
            pass
    # Serial numérico de Excel (rango ~1902-2173 equivale a 1000-100000)
    try:
        n = float(v)
        if 1000 < n < 100000:
            return _EXCEL_ORIGIN + pd.Timedelta(days=int(n))
    except (ValueError, TypeError):
        pass
    # String con formato DD/MM/YYYY (colombiano)
    try:
        ts = pd.to_datetime(str(v), dayfirst=True, errors='coerce')
        if not pd.isna(ts):
            return ts
    except Exception:
        pass
    return pd.NaT


def _parse_serie_fechas(serie):
    """Parsea una serie de fechas: datetime, serial Excel o string DD/MM/YYYY."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    parsed = [_parse_valor_fecha(v) for v in serie]
    return pd.Series(parsed, index=serie.index, dtype='datetime64[ns]')


def _candidatos_fecha(tipo):
    if tipo == 'mortalidad':
        return [
            '9.3 Fecha parto (dd/mm/aaaa)', '9.3 Fecha parto',
            'Fecha parto (dd/mm/aaaa)', 'Fecha parto',
            '5.2 Fecha de defunción', '5.2 Fecha de defuncion',
            'Fecha de defunción', 'Fecha de defuncion',
        ]
    return [
        'Fecha de egreso', 'Fecha egreso',
        'Fecha de egreso (dd/mm/aaaa)', 'Fecha egreso (dd/mm/aaaa)',
        'Fecha de egreso (dd/mm/yyyy)', 'Fecha egreso (dd/mm/yyyy)',
    ]


def _detectar_col_fecha(df, tipo):
    candidatos = _candidatos_fecha(tipo)
    candidatos_norm = {_normalizar_encabezado(c) for c in candidatos}
    for col in df.columns:
        if col in candidatos or _normalizar_encabezado(col) in candidatos_norm:
            return col
    return None


def _extraer_anos_disponibles(df, tipo):
    col = _detectar_col_fecha(df, tipo)
    if col is not None:
        fechas = _parse_serie_fechas(df[col])
        anos = sorted(fechas.dropna().dt.year.unique().astype(int).tolist())
        if anos:
            return anos
    return []


def _enriquecer_df_con_fecha(df, tipo):
    """No-op: la detección ahora cubre todos los formatos de columna conocidos."""
    return df


def _filtrar_dataframe_por_fecha(df, tipo, year, month):
    if not (year or month):
        return df
    col = _detectar_col_fecha(df, tipo)
    if col is None:
        return df
    fechas = _parse_serie_fechas(df[col])
    mask = pd.Series([True] * len(df), index=df.index)
    if year:
        mask &= fechas.dt.year == int(year)
    if month:
        mask &= fechas.dt.month == int(month)
    return df[mask].reset_index(drop=True)


@api_view(['GET'])
@permission_classes([AllowAny])
def analisis_completo(request, pk):
    """
    GET /api/analisis/<id>/completo/
    Genera análisis completo con estadísticas, clustering y visualizaciones.
    Acepta query params: year, month para filtrar por fecha.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': ERROR_ANALISIS_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

    year = request.query_params.get('year', '').strip() or None
    month = request.query_params.get('month', '').strip() or None

    # Leer archivo y procesar
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df = _canonizar_columnas_dataframe(df, analisis.tipo)
        df, limpieza = preparar_dataframe_analisis(df)

        # Si el Excel no tiene columna de fecha, la enriquecemos desde la BD
        df = _enriquecer_df_con_fecha(df, analisis.tipo)

        anos_disponibles = _extraer_anos_disponibles(df, analisis.tipo)

        df = _filtrar_dataframe_por_fecha(df, analisis.tipo, year, month)

        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = {
                'tipo': 'mortalidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'momento_muerte': processor.analizar_momento_muerte(),
                'demoras': processor.analizar_demoras(),
                'causas_cie10': processor.analizar_causas_cie10(top_n=15),
                'obstetrico_edad': processor.analizar_obstetrico_por_edad(),
                'anos_disponibles': anos_disponibles,
                'filtros_activos': {'year': year, 'month': month},
            }
        else:  # morbilidad
            processor = MorbilidadProcessor(df)
            resultado = {
                'tipo': 'morbilidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'criterios_inclusion': processor.analizar_criterios_inclusion(),
                'momento_ocurrencia': processor.analizar_momento_ocurrencia(),
                'institucion_referencia': processor.analizar_institucion_referencia(),
                'tiempo_remision': processor.analizar_tiempo_remision(),
                'obstetrico_edad': processor.analizar_obstetrico_por_edad(),
                'anos_disponibles': anos_disponibles,
                'filtros_activos': {'year': year, 'month': month},
            }

        return Response(resultado)

    except Exception as e:
        return Response(
            {'error': f'Error al procesar el análisis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def clustering_analisis(request, pk):
    """
    POST /api/analisis/<id>/clustering/
    Realiza análisis de clustering sobre los datos.
    
    Body:
        {
            "tipo_clustering": "kmeans" | "jerarquico",
            "n_clusters": 3  (opcional, default 3)
        }
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': ERROR_ANALISIS_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)
    
    tipo_clustering = request.data.get('tipo_clustering', 'kmeans')
    n_clusters = request.data.get('n_clusters', 3)
    
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df)
        
        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            
            if tipo_clustering == 'jerarquico':
                resultado = processor.clustering_jerarquico()
            else:  # kmeans por defecto
                resultado = processor.clustering_factores_riesgo(n_clusters=n_clusters)
        
        else:  # morbilidad
            processor = MorbilidadProcessor(df)
            resultado = processor.clustering_perfiles_morbilidad(n_clusters=n_clusters)
        
        resultado['analisis_id'] = analisis.id
        resultado['tipo_analisis'] = analisis.tipo
        resultado['tipo_clustering'] = tipo_clustering
        resultado['limpieza_datos'] = limpieza
        
        return Response(resultado)
    
    except Exception as e:
        return Response(
            {'error': f'Error en clustering: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_correlacion(request, pk):
    """
    GET /api/analisis/<id>/heatmap/
    Genera matriz de correlación para heatmap.
    Solo disponible para morbilidad.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': ERROR_ANALISIS_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)
    
    if analisis.tipo != 'morbilidad':
        return Response(
            {'error': 'Heatmap solo disponible para análisis de morbilidad'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df)
        processor = MorbilidadProcessor(df)
        resultado = processor.heatmap_correlacion()
        
        resultado['analisis_id'] = analisis.id
        resultado['limpieza_datos'] = limpieza
        
        return Response(resultado)
    
    except Exception as e:
        return Response(
            {'error': f'Error al generar heatmap: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def resumen_sivigila(request):
    return Response({
        'pacientes': Paciente.objects.count(),
        'casos_morbilidad': CasoMorbilidad.objects.count(),
        'casos_mortalidad': CasoMortalidad.objects.count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_pacientes(request):
    limite = obtener_limite(request)
    pacientes = Paciente.objects.select_related('id_tipo').order_by('id_paciente')[:limite]
    return Response(PacienteSerializer(pacientes, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_morbilidad_sivigila(request):
    limite = obtener_limite(request)
    casos = VMorbilidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MorbilidadCompletaSerializer(casos, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_mortalidad_sivigila(request):
    limite = obtener_limite(request)
    casos = VMortalidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MortalidadCompletaSerializer(casos, many=True).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_usuario(request):
    nombre = request.data.get('nombre', '').strip()
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not nombre or not email or not password:
        return Response({'error': 'Todos los campos son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({'error': 'La contraseña debe tener al menos 6 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)

    if Usuario.objects.filter(email=email).exists():
        return Response({'error': 'Ya existe una cuenta con este correo electrónico.'}, status=status.HTTP_400_BAD_REQUEST)

    usuario = Usuario.objects.create(
        nombre=nombre,
        email=email,
        password_hash=make_password(password),
    )
    return Response({'id': usuario.id, 'nombre': usuario.nombre, 'email': usuario.email}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'error': 'Correo y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return Response({'error': 'Correo o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

    if not check_password(password, usuario.password_hash):
        return Response({'error': 'Correo o contraseña incorrectos.'}, status=status.HTTP_401_UNAUTHORIZED)

    localStorage_nombre = usuario.nombre
    return Response({'id': usuario.id, 'nombre': localStorage_nombre, 'email': usuario.email})


