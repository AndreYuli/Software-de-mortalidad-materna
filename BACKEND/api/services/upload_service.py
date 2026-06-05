"""Servicio de carga y validación de archivos Excel SIVIGILA.

Orquesta la validación de columnas, la lectura del DataFrame,
la persistencia en SIVIGILA y la creación o actualización del
registro Analisis en base de datos.
"""
import re
import unicodedata
from functools import lru_cache
from hashlib import sha256
from io import BytesIO

import openpyxl
import pandas as pd
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from ..models import Analisis
from ..processors import es_valor_positivo, preparar_dataframe_analisis
from ..serializers import UploadSerializer
from ..sivigila_ingestion import persistir_dataframe_sivigila
from ..views_constants import (
    ALIAS_COLUMNAS,
    COLUMNA_CAUSA_BASICA_CIE10,
    COLUMNA_MOMENTO_MUERTE,
    COLUMNAS_REQUERIDAS,
    MORTALIDAD_ANALISIS_MAPPING,
)


# ---------------------------------------------------------------------------
# Normalización de encabezados
# ---------------------------------------------------------------------------

def _normalizar_encabezado(valor):
    """Normaliza un encabezado de columna para comparación robusta.

    Convierte a minúsculas, elimina acentos, reemplaza variantes de
    'N°'/'Nº'/'No.' y colapsa espacios múltiples.

    Args:
        valor: Valor de celda (cualquier tipo); se convierte a str.

    Returns:
        Cadena normalizada lista para comparar.
    """
    texto = str(valor or '').strip().lower()
    texto = (
        unicodedata.normalize('NFKD', texto)
        .encode('ascii', 'ignore')
        .decode('ascii')
    )
    texto = (
        texto
        .replace('n°', 'n ')
        .replace('nº', 'n ')
        .replace('no.', 'n ')
        .replace('no ', 'n ')
    )
    texto = re.sub(r'[^a-z0-9]+', ' ', texto)
    return ' '.join(texto.split())


@lru_cache(maxsize=4)
def _construir_mapa_alias(tipo):
    """Construye el mapa alias → nombre canónico para un tipo de evento.

    Se cachea con lru_cache porque el mapa es constante durante la vida
    del proceso; reconstruirlo en cada request sería innecesario.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Dict {encabezado_normalizado: nombre_canonico}.
    """
    mapa = {}
    for canonical in COLUMNAS_REQUERIDAS[tipo]:
        mapa[_normalizar_encabezado(canonical)] = canonical
    for canonical, alias_list in ALIAS_COLUMNAS.get(tipo, {}).items():
        mapa[_normalizar_encabezado(canonical)] = canonical
        for alias in alias_list:
            mapa[_normalizar_encabezado(alias)] = canonical
    return mapa


def _obtener_columnas_faltantes(tipo, columnas_archivo):
    """Retorna las columnas requeridas que no están en el archivo.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.
        columnas_archivo: Lista de nombres de columna tal como están en el Excel.

    Returns:
        Lista de nombres canónicos de columnas faltantes.
    """
    mapa_alias = _construir_mapa_alias(tipo)
    presentes = {
        mapa_alias[normalizada]
        for columna in columnas_archivo
        for normalizada in [_normalizar_encabezado(columna)]
        if normalizada in mapa_alias
    }
    return [col for col in COLUMNAS_REQUERIDAS[tipo] if col not in presentes]


def _canonizar_columnas_dataframe(df, tipo):
    """Renombra las columnas del DataFrame a sus nombres canónicos.

    Args:
        df: DataFrame con columnas tal como vienen del Excel.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        DataFrame con columnas renombradas.
    """
    mapa_alias = _construir_mapa_alias(tipo)
    renames = {}
    for columna in df.columns:
        canonical = mapa_alias.get(_normalizar_encabezado(columna))
        if canonical and canonical != columna and canonical not in df.columns:
            renames[columna] = canonical
    return df.rename(columns=renames)


# ---------------------------------------------------------------------------
# Lectura de Excel
# ---------------------------------------------------------------------------

def _seleccionar_fila_encabezados(filas, tipo):
    """Elige la fila con mayor coincidencia con las columnas requeridas.

    Necesario porque algunos archivos SIVIGILA tienen filas de título
    o metadatos antes de los encabezados reales de la tabla.

    Args:
        filas: Lista de filas (cada fila es una lista de valores de celda).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de strings con los encabezados de la mejor fila encontrada.
    """
    mejor_fila = []
    mejor_puntaje = -1
    for fila in filas:
        columnas = [
            str(v).strip()
            for v in fila
            if v is not None and str(v).strip()
        ]
        if not columnas:
            continue
        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(
            _obtener_columnas_faltantes(tipo, columnas)
        )
        if puntaje > mejor_puntaje:
            mejor_fila = columnas
            mejor_puntaje = puntaje
    return mejor_fila


def _seleccionar_hoja_y_encabezados_openpyxl(workbook, tipo):
    """Encuentra la hoja y fila de encabezados con mejor coincidencia.

    Args:
        workbook: Workbook de openpyxl ya abierto.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Tupla (nombre_hoja, lista_encabezados).
    """
    mejor_fila = []
    mejor_puntaje = -1
    mejor_hoja = workbook.active.title

    for hoja in workbook.worksheets:
        filas = [
            [cell.value for cell in row]
            for row in hoja.iter_rows(min_row=1, max_row=5)
        ]
        fila = _seleccionar_fila_encabezados(filas, tipo)
        puntaje = (
            len(COLUMNAS_REQUERIDAS[tipo])
            - len(_obtener_columnas_faltantes(tipo, fila))
            if fila else -1
        )
        if puntaje > mejor_puntaje:
            mejor_fila = fila
            mejor_puntaje = puntaje
            mejor_hoja = hoja.title

    return mejor_hoja, mejor_fila


def leer_columnas_excel(archivo, tipo):
    """Lee solo los encabezados del Excel para validación rápida.

    Usa read_only=True para no cargar el archivo completo en memoria
    cuando solo se necesita verificar que las columnas requeridas existan.

    Args:
        archivo: Objeto de archivo Django (InMemoryUploadedFile).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de strings con los encabezados encontrados, o None si falla.
    """
    try:
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        _, headers = _seleccionar_hoja_y_encabezados_openpyxl(wb, tipo)
        wb.close()
        return headers
    except Exception:
        return None


def _detectar_indice_encabezados_dataframe(df_sin_encabezado, tipo):
    """Detecta en qué fila están los encabezados dentro de un DataFrame sin header.

    Args:
        df_sin_encabezado: DataFrame leído con header=None.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Índice (int) de la fila con mayor coincidencia de columnas requeridas.
    """
    mejor_indice = 0
    mejor_puntaje = -1
    for indice in range(min(5, len(df_sin_encabezado.index))):
        fila = df_sin_encabezado.iloc[indice].tolist()
        columnas = [
            str(v).strip()
            for v in fila
            if not pd.isna(v) and str(v).strip()
        ]
        if not columnas:
            continue
        puntaje = len(COLUMNAS_REQUERIDAS[tipo]) - len(
            _obtener_columnas_faltantes(tipo, columnas)
        )
        if puntaje > mejor_puntaje:
            mejor_indice = indice
            mejor_puntaje = puntaje
    return mejor_indice


def _seleccionar_hoja_y_encabezados_dataframe(sheets, tipo):
    """Selecciona hoja e índice de encabezados con mejor coincidencia.

    Args:
        sheets: Dict {nombre_hoja: DataFrame} de pd.read_excel con sheet_name=None.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Tupla (nombre_hoja, indice_encabezados).
    """
    mejor_hoja = None
    mejor_indice = 0
    mejor_puntaje = -1

    for nombre_hoja, dataframe in sheets.items():
        indice = _detectar_indice_encabezados_dataframe(dataframe, tipo)
        fila = (
            dataframe.iloc[indice].tolist()
            if len(dataframe.index) > indice
            else []
        )
        columnas = [
            str(v).strip() for v in fila
            if not pd.isna(v) and str(v).strip()
        ]
        puntaje = (
            len(COLUMNAS_REQUERIDAS[tipo])
            - len(_obtener_columnas_faltantes(tipo, columnas))
            if columnas else -1
        )
        if puntaje > mejor_puntaje:
            mejor_hoja = nombre_hoja
            mejor_indice = indice
            mejor_puntaje = puntaje

    return mejor_hoja, mejor_indice


def _leer_dataframe_excel(archivo, tipo):
    """Lee el Excel completo y canoniza los nombres de columna.

    Args:
        archivo: Objeto de archivo Django.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        DataFrame con columnas canónicas listo para procesar.
    """
    archivo.seek(0)
    hojas = pd.read_excel(
        archivo, engine='openpyxl', header=None, sheet_name=None,
    )
    nombre_hoja, indice_encabezados = _seleccionar_hoja_y_encabezados_dataframe(
        hojas, tipo,
    )

    archivo.seek(0)
    df = pd.read_excel(
        archivo,
        engine='openpyxl',
        header=indice_encabezados,
        sheet_name=nombre_hoja,
    )
    return _canonizar_columnas_dataframe(df, tipo)


# ---------------------------------------------------------------------------
# Construcción del archivo de análisis
# ---------------------------------------------------------------------------

def _calcular_resumen_desde_dataframe(df, tipo):
    """Calcula estadísticas de resumen sobre un DataFrame ya limpio.

    Args:
        df: DataFrame procesado (sin filas vacías ni duplicados).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Dict con total_registros y estadísticas específicas del tipo.
    """
    try:
        resumen = {'total_registros': len(df)}

        if tipo == 'mortalidad':
            if COLUMNA_MOMENTO_MUERTE in df.columns:
                resumen['distribucion_momento'] = (
                    df[COLUMNA_MOMENTO_MUERTE].value_counts().to_dict()
                )
            if COLUMNA_CAUSA_BASICA_CIE10 in df.columns:
                top5 = (
                    df[COLUMNA_CAUSA_BASICA_CIE10]
                    .value_counts()
                    .head(5)
                    .to_dict()
                )
                resumen['top5_causas'] = {
                    str(k): int(v) for k, v in top5.items()
                }

        elif tipo == 'morbilidad':
            criterios_cols = [
                'Eclampsia',
                'Sepsis sistémica severa',
                'Hemorragia obstétrica severa',
                'Preeclampsia',
                'Ruptura uterina',
            ]
            presentes = [c for c in criterios_cols if c in df.columns]
            if presentes:
                resumen['criterios_frecuencia'] = {
                    c: int(df[c].apply(es_valor_positivo).sum())
                    for c in presentes
                }
        return resumen
    except Exception:
        return {}


def _construir_dataframe_analisis_desde_bd(tipo):
    """Reconstruye el DataFrame autoritativo desde la base de datos SIVIGILA.

    Se usa después de persistir un nuevo archivo para garantizar que el
    análisis refleje todos los registros acumulados, no solo el archivo
    recién cargado.

    Args:
        tipo: 'mortalidad' o 'morbilidad'. Solo mortalidad implementado.

    Returns:
        DataFrame con registros de la BD, o None si el tipo no aplica.
    """
    from ..models import VMortalidadCompleta

    if tipo != 'mortalidad':
        return None

    registros = list(
        VMortalidadCompleta.objects.order_by('id_caso').values(
            *MORTALIDAD_ANALISIS_MAPPING.keys()
        )
    )
    if not registros:
        return pd.DataFrame(columns=list(MORTALIDAD_ANALISIS_MAPPING.values()))

    dataframe = pd.DataFrame.from_records(registros)
    return dataframe.rename(columns=MORTALIDAD_ANALISIS_MAPPING)


def _construir_archivo_analisis_desde_dataframe(df_fuente, tipo, nombre_archivo):
    """Serializa un DataFrame limpio a un archivo Excel en memoria.

    Args:
        df_fuente: DataFrame ya procesado con preparar_dataframe_analisis.
        tipo: 'mortalidad' o 'morbilidad'.
        nombre_archivo: Nombre que tendrá el archivo guardado en media.

    Returns:
        Tupla (archivo_content_file, archivo_hash, resumen, total_registros).
    """
    resumen = _calcular_resumen_desde_dataframe(df_fuente, tipo)
    total_registros = resumen.pop('total_registros', len(df_fuente))

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_fuente.to_excel(writer, index=False)

    contenido = buffer.getvalue()
    archivo = ContentFile(contenido, name=nombre_archivo)
    archivo_hash = sha256(contenido).hexdigest()
    return archivo, archivo_hash, resumen, total_registros


def _construir_archivo_analisis_acumulado(
    analisis_existente, df_nuevo, tipo, nombre_archivo,
):
    """Combina el archivo previo con el nuevo DataFrame para análisis acumulado.

    Cuando no hay datos en la BD (ej. morbilidad), se acumulan los
    archivos históricos para que el análisis no pierda registros anteriores.

    Args:
        analisis_existente: Instancia Analisis previa, o None.
        df_nuevo: DataFrame del archivo recién cargado.
        tipo: 'mortalidad' o 'morbilidad'.
        nombre_archivo: Nombre del archivo resultante.

    Returns:
        Tupla (archivo_content_file, archivo_hash, resumen, total_registros).
    """
    dataframes = []

    if analisis_existente is not None and analisis_existente.archivo:
        try:
            analisis_existente.archivo.open('rb')
            df_anterior = pd.read_excel(
                analisis_existente.archivo, engine='openpyxl',
            )
            dataframes.append(df_anterior)
        except Exception:
            pass
        finally:
            try:
                analisis_existente.archivo.close()
            except Exception:
                pass

    dataframes.append(df_nuevo.copy())
    df_acumulado = (
        pd.concat(dataframes, ignore_index=True)
        if len(dataframes) > 1
        else dataframes[0]
    )
    return _construir_archivo_analisis_desde_dataframe(
        df_acumulado, tipo, nombre_archivo,
    )


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def procesar_carga_archivo(request_data, request_files):
    """Orquesta la carga completa de un archivo Excel SIVIGILA.

    Flujo:
        1. Validar campos del formulario (tipo + archivo).
        2. Leer encabezados del Excel y verificar columnas requeridas.
        3. Leer el DataFrame completo y limpiarlo.
        4. Persistir en tablas SIVIGILA dentro de una transacción atómica.
        5. Construir o actualizar el registro Analisis.

    Args:
        request_data: request.data de DRF (contiene 'tipo').
        request_files: request.FILES de DRF (contiene 'archivo').

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    data_combinada = {**request_data.dict(), **{
        k: v for k, v in request_files.items()
    }}
    serializer = UploadSerializer(data=data_combinada)
    if not serializer.is_valid():
        return serializer.errors, status.HTTP_400_BAD_REQUEST

    tipo = serializer.validated_data['tipo']
    archivo = serializer.validated_data['archivo']

    columnas_archivo = leer_columnas_excel(archivo, tipo)
    if columnas_archivo is None:
        return (
            {'error': 'No se pudo leer el archivo. Verifica que sea un Excel válido.'},
            status.HTTP_400_BAD_REQUEST,
        )

    faltantes = _obtener_columnas_faltantes(tipo, columnas_archivo)
    if faltantes:
        return (
            {'error': 'Faltan columnas requeridas.', 'columnas_faltantes': faltantes},
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    try:
        df = _leer_dataframe_excel(archivo, tipo)
    except Exception:
        return (
            {'error': 'No se pudo leer el contenido del Excel.'},
            status.HTTP_400_BAD_REQUEST,
        )

    df, _ = preparar_dataframe_analisis(df)

    try:
        with transaction.atomic():
            analisis_existente = (
                Analisis.objects
                .filter(tipo=tipo)
                .order_by('-fecha_carga', '-id')
                .first()
            )
            persistencia = persistir_dataframe_sivigila(df, tipo)

            df_autoritativo = _construir_dataframe_analisis_desde_bd(tipo)
            if df_autoritativo is not None:
                archivo_analisis, archivo_hash, resumen, total_registros = (
                    _construir_archivo_analisis_desde_dataframe(
                        df_autoritativo, tipo, archivo.name,
                    )
                )
            else:
                archivo_analisis, archivo_hash, resumen, total_registros = (
                    _construir_archivo_analisis_acumulado(
                        analisis_existente, df, tipo, archivo.name,
                    )
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
                analisis_existente.save(
                    update_fields=[
                        'nombre_archivo', 'archivo_hash', 'archivo',
                        'total_registros', 'resumen', 'fecha_carga',
                    ]
                )
                analisis = analisis_existente

    except ValueError as error:
        return {'error': str(error)}, status.HTTP_422_UNPROCESSABLE_ENTITY
    except Exception as error:
        return (
            {
                'error': (
                    f'No se pudo persistir el archivo en SIVIGILA: {str(error)}'
                ),
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    from ..serializers import AnalisisSerializer
    data = AnalisisSerializer(analisis).data
    data['sivigila'] = persistencia
    return data, status.HTTP_201_CREATED
