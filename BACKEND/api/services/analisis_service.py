"""Servicio de análisis de datos SIVIGILA.

Encapsula la carga del DataFrame desde disco, el filtrado por fecha,
el cálculo de estadísticas, el clustering y la detección de columnas
opcionales. Utiliza LocMemCache para evitar re-procesar el Excel en
cada petición HTTP.
"""
import re
import unicodedata
import warnings

import pandas as pd
from django.core.cache import cache
from rest_framework import status

from ..processors import (
    MorbilidadProcessor,
    MortalidadProcessor,
    preparar_dataframe_analisis,
)
from .upload_service import _canonizar_columnas_dataframe, _normalizar_encabezado


# ---------------------------------------------------------------------------
# Patrones para detección de columna opcional (edad, municipio, etc.)
# ---------------------------------------------------------------------------

# Columnas opcionales que SIVIGILA puede incluir según la versión del formulario
_EXTRA_COL_PATTERNS = {
    'edad': ['edad', 'edad (anos)', 'edad (años)', 'edad anos', 'edad años'],
    'departamento': ['departamento', 'depto', 'dpto'],
    'municipio': ['municipio'],
    'regimen': ['regimen', 'régimen', 'afiliacion', 'afiliación'],
    'eps': ['eps', 'entidad promotora', 'aseguradora'],
}

# Orden de prioridad: se muestra la primera columna opcional que se encuentre
_EXTRA_COL_PRIORITY = ['municipio', 'departamento', 'edad', 'regimen', 'eps']


def _normalizar_extra(valor):
    """Normaliza un valor para comparación de columnas opcionales.

    Args:
        valor: Valor de cualquier tipo a normalizar.

    Returns:
        Cadena ASCII en minúsculas sin caracteres especiales.
    """
    texto = str(valor or '').strip().lower()
    texto = (
        unicodedata.normalize('NFKD', texto)
        .encode('ascii', 'ignore')
        .decode('ascii')
    )
    return re.sub(r'[^a-z0-9]+', ' ', texto).strip()


def _detectar_extra_columna(headers):
    """Detecta la primera columna opcional presente en la lista de headers.

    Args:
        headers: Lista de nombres de columna del Excel.

    Returns:
        Tupla (kind, indice, nombre_columna) donde kind es el tipo
        ('edad', 'municipio', etc.), o (None, -1, None) si no hay ninguna.
    """
    headers_norm = [_normalizar_extra(h) for h in headers]
    for kind in _EXTRA_COL_PRIORITY:
        for pattern in _EXTRA_COL_PATTERNS[kind]:
            pat_norm = _normalizar_extra(pattern)
            for i, hn in enumerate(headers_norm):
                if hn == pat_norm or pat_norm in hn:
                    return kind, i, headers[i]
    return None, -1, None


# ---------------------------------------------------------------------------
# Parseo de fechas
# ---------------------------------------------------------------------------

def _parse_serie_fechas(serie):
    """Parsea una Serie pandas con fechas en múltiples formatos.

    Maneja tres casos comunes en exportaciones SIVIGILA:
    - Objetos datetime nativos de Python/pandas.
    - Seriales numéricos de Excel (días desde 1899-12-30).
    - Cadenas en formato DD/MM/YYYY o variantes.

    Args:
        serie: pd.Series con valores de fecha en cualquier formato.

    Returns:
        pd.Series de tipo datetime64 con NaT donde no se pudo parsear.
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie

    s_numeric = pd.to_numeric(serie, errors='coerce')

    # SIVIGILA exporta fechas como seriales Excel (días desde 1899-12-30)
    # en versiones anteriores a 2018; el rango 1000-100000 los identifica
    is_excel_serial = (s_numeric > 1000) & (s_numeric < 100_000)

    serie_clean = serie.copy()
    if is_excel_serial.any():
        serie_clean = serie_clean.mask(is_excel_serial)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=UserWarning, message='.*Parsing dates.*',
        )
        fechas = pd.to_datetime(serie_clean, dayfirst=True, errors='coerce')

    if is_excel_serial.any():
        excel_days = s_numeric[is_excel_serial].astype(int)
        fechas_excel = pd.to_datetime(
            excel_days, unit='D', origin='1899-12-30', errors='coerce',
        )
        fechas = fechas.fillna(fechas_excel)

    # Intento adicional sin dayfirst para fechas en formato ambiguo (MM/DD/YYYY)
    por_vias_alternas = fechas.isna() & serie_clean.notna()
    if por_vias_alternas.any():
        alternas_str = serie_clean[por_vias_alternas].astype(str)
        fechas_alt = pd.to_datetime(alternas_str, errors='coerce')
        fechas = fechas.fillna(fechas_alt)

    return fechas


def _candidatos_fecha(tipo):
    """Retorna los candidatos de columna de fecha para un tipo de evento.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de nombres candidatos en orden de preferencia.
    """
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
    """Detecta qué columna de fecha está presente en el DataFrame.

    Args:
        df: DataFrame a inspeccionar.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Nombre de la columna de fecha encontrada, o None.
    """
    candidatos = _candidatos_fecha(tipo)
    candidatos_norm = {_normalizar_encabezado(c) for c in candidatos}
    for col in df.columns:
        if col in candidatos or _normalizar_encabezado(col) in candidatos_norm:
            return col
    return None


# ---------------------------------------------------------------------------
# Servicio de análisis completo
# ---------------------------------------------------------------------------

def obtener_analisis_completo(analisis, year, month):
    """Carga y procesa el análisis completo de un objeto Analisis.

    Lee el Excel del disco (con caché de 10 min), aplica filtros de
    fecha opcionales y construye el dict de resultado con todas las
    estadísticas del procesador correspondiente.

    Args:
        analisis: Instancia del modelo Analisis.
        year: Año para filtrar (str o None).
        month: Mes para filtrar (str o None).

    Returns:
        Tupla (resultado_dict, http_status).
    """
    cache_key = f'completo_{analisis.pk}_{year or ""}_{month or ""}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, status.HTTP_200_OK

    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df = _canonizar_columnas_dataframe(df, analisis.tipo)
        df, limpieza = preparar_dataframe_analisis(df)

        col_fecha = _detectar_col_fecha(df, analisis.tipo)
        fechas_serie = None
        anos_disponibles = []
        distribucion_mensual = {}

        if col_fecha is not None:
            try:
                fechas_serie = _parse_serie_fechas(df[col_fecha])
                valid_fechas = fechas_serie.dropna()
                anos_disponibles = sorted(
                    valid_fechas.dt.year.unique().astype(int).tolist()
                )
                for fecha in valid_fechas:
                    y_str = str(fecha.year)
                    m_str = str(fecha.month)
                    if y_str not in distribucion_mensual:
                        distribucion_mensual[y_str] = {
                            str(i): 0 for i in range(1, 13)
                        }
                    distribucion_mensual[y_str][m_str] = (
                        distribucion_mensual[y_str].get(m_str, 0) + 1
                    )
            except Exception:
                pass

        if (year or month) and col_fecha is not None and fechas_serie is not None:
            mask = pd.Series([True] * len(df), index=df.index)
            if year:
                mask &= fechas_serie.dt.year == int(year)
            if month:
                mask &= fechas_serie.dt.month == int(month)
            df = df[mask].reset_index(drop=True)

        archivo_url = (
            analisis.archivo.url
            if hasattr(analisis, 'archivo') and analisis.archivo
            else None
        )

        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = {
                'tipo': 'mortalidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'archivo': archivo_url,
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'momento_muerte': processor.analizar_momento_muerte(),
                'demoras': processor.analizar_demoras(),
                'causas_cie10': processor.analizar_causas_cie10(top_n=15),
                'obstetrico_edad': processor.analizar_obstetrico_por_edad(),
                'anos_disponibles': anos_disponibles,
                'distribucion_mensual': distribucion_mensual,
                'filtros_activos': {'year': year, 'month': month},
            }
        else:
            processor = MorbilidadProcessor(df)
            resultado = {
                'tipo': 'morbilidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'archivo': archivo_url,
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'criterios_inclusion': processor.analizar_criterios_inclusion(),
                'momento_ocurrencia': processor.analizar_momento_ocurrencia(),
                'institucion_referencia': processor.analizar_institucion_referencia(),
                'tiempo_remision': processor.analizar_tiempo_remision(),
                'obstetrico_edad': processor.analizar_obstetrico_por_edad(),
                'anos_disponibles': anos_disponibles,
                'distribucion_mensual': distribucion_mensual,
                'filtros_activos': {'year': year, 'month': month},
            }

        cache.set(cache_key, resultado, timeout=600)
        return resultado, status.HTTP_200_OK

    except Exception as exc:
        return (
            {'error': f'Error al procesar el análisis: {str(exc)}'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def obtener_extra_columna(analisis):
    """Detecta y devuelve datos de una columna opcional del Excel.

    Solo disponible para mortalidad. Busca columnas de edad, municipio,
    departamento, régimen o EPS y construye datos listos para graficar.
    Se cachea 10 minutos para evitar re-leer el archivo.

    Args:
        analisis: Instancia del modelo Analisis.

    Returns:
        Tupla (resultado_dict, http_status). resultado_dict tiene clave
        'chart' con los datos del gráfico, o None si no se detectó columna.
    """
    if analisis.tipo != 'mortalidad':
        return {'chart': None}, status.HTTP_200_OK

    cache_key = f'extra_col_{analisis.pk}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, status.HTTP_200_OK

    try:
        # nrows=2000 para limitar consumo de memoria en archivos grandes
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl', nrows=2000)
    except Exception:
        return {'chart': None}, status.HTTP_200_OK

    kind, _col_idx, col_name = _detectar_extra_columna(list(df.columns))
    if kind is None:
        resultado = {'chart': None}
        cache.set(cache_key, resultado, timeout=600)
        return resultado, status.HTTP_200_OK

    serie = df[col_name]

    if kind == 'edad':
        edades = pd.to_numeric(serie, errors='coerce')
        edades = edades[(edades >= 0) & (edades <= 120)].dropna()
        if len(edades) < 3:
            resultado = {'chart': None}
            cache.set(cache_key, resultado, timeout=600)
            return resultado, status.HTTP_200_OK

        buckets = [
            ('<15', 0, 14.999), ('15-19', 15, 19.999), ('20-24', 20, 24.999),
            ('25-29', 25, 29.999), ('30-34', 30, 34.999),
            ('35-39', 35, 39.999), ('40+', 40, 120),
        ]
        labels = [b[0] for b in buckets]
        values = [
            int(((edades >= b[1]) & (edades <= b[2])).sum()) for b in buckets
        ]
        resultado = {
            'chart': {
                'type': 'bar',
                'orientation': 'v',
                'title': 'Distribución por edad',
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels,
                'values': values,
                'total': int(sum(values)),
                'xTitle': 'Rango de edad (años)',
                'yTitle': 'Casos',
            }
        }
    else:
        def _clean_cell(val):
            """Limpia una celda categórica; retorna None si es vacía o nula."""
            s = str(val or '').strip()
            if not s or s.lower() in ('nan', 'null', 'none', 'sin dato'):
                return None
            return s

        cats = [_clean_cell(v) for v in serie]
        cats = [c for c in cats if c]
        if len(cats) < 3:
            resultado = {'chart': None}
            cache.set(cache_key, resultado, timeout=600)
            return resultado, status.HTTP_200_OK

        counts_map: dict = {}
        for c in cats:
            counts_map[c] = counts_map.get(c, 0) + 1

        sorted_cats = sorted(
            counts_map.items(), key=lambda x: x[1], reverse=True,
        )
        top = sorted_cats[:10]
        other = sum(v for _, v in sorted_cats[10:])
        labels = [k for k, _ in top]
        values = [v for _, v in top]
        if other > 0:
            labels.append('Otros')
            values.append(other)

        title_map = {
            'departamento': 'Top departamentos',
            'municipio': 'Top municipios',
            'regimen': 'Distribución por régimen',
            'eps': 'Top EPS',
        }
        resultado = {
            'chart': {
                'type': 'bar',
                'orientation': 'h',
                'title': title_map.get(kind, 'Distribución'),
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels,
                'values': values,
                'total': int(sum(values)),
                'xTitle': 'Casos',
                'yTitle': '',
            }
        }

    cache.set(cache_key, resultado, timeout=600)
    return resultado, status.HTTP_200_OK


def obtener_clustering(analisis, tipo_clustering, n_clusters):
    """Ejecuta clustering K-means o jerárquico sobre el Excel del análisis.

    Args:
        analisis: Instancia del modelo Analisis.
        tipo_clustering: 'kmeans' o 'jerarquico'.
        n_clusters: Número de clusters (ignorado en jerarquico).

    Returns:
        Tupla (resultado_dict, http_status).
    """
    try:
        df_raw = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df_raw)

        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = (
                processor.clustering_jerarquico()
                if tipo_clustering == 'jerarquico'
                else processor.clustering_factores_riesgo(n_clusters=n_clusters)
            )
        else:
            processor = MorbilidadProcessor(df)
            resultado = processor.clustering_perfiles_morbilidad(
                n_clusters=n_clusters,
            )

        resultado['analisis_id'] = analisis.id
        resultado['tipo_analisis'] = analisis.tipo
        resultado['tipo_clustering'] = tipo_clustering
        resultado['limpieza_datos'] = limpieza
        return resultado, status.HTTP_200_OK

    except Exception as exc:
        return (
            {'error': f'Error en clustering: {str(exc)}'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def obtener_heatmap(analisis):
    """Calcula la matriz de correlación para análisis de morbilidad.

    Solo disponible para morbilidad; retorna 400 para mortalidad.

    Args:
        analisis: Instancia del modelo Analisis.

    Returns:
        Tupla (resultado_dict, http_status).
    """
    if analisis.tipo != 'morbilidad':
        return (
            {'error': 'Heatmap solo disponible para análisis de morbilidad'},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        df_raw = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df_raw)
        processor = MorbilidadProcessor(df)
        resultado = processor.heatmap_correlacion()
        resultado['analisis_id'] = analisis.id
        resultado['limpieza_datos'] = limpieza
        return resultado, status.HTTP_200_OK

    except Exception as exc:
        return (
            {'error': f'Error al generar heatmap: {str(exc)}'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
