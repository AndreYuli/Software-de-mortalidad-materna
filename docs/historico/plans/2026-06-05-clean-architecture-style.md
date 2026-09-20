# Clean Architecture + PEP 8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar la lógica de negocio de `views.py` en una capa `services/`, y aplicar PEP 8, comillas simples y docstrings Google a todos los archivos Python de `BACKEND/api/`.

**Architecture:** Capa HTTP (`views.py`) → capa de servicios (`services/`) → capa de dominio (`processors.py`) → capa de persistencia (`sivigila_ingestion.py`). Cada capa solo conoce la siguiente; `views.py` no importa `pandas` ni `openpyxl`.

**Tech Stack:** Django 6, Django REST Framework, pandas, openpyxl, scikit-learn, LocMemCache

---

## Reglas de estilo aplicadas en todos los archivos

| Regla | Ejemplo incorrecto | Ejemplo correcto |
|---|---|---|
| Comillas simples | `"texto"` | `'texto'` |
| Docstring apertura | sin docstring | `"""Hace X.\n\nArgs:\n    y: ...\n"""` |
| Línea máxima | `super_larga_linea_de_mas_de_79_chars = algo_muy_largo + otro_thing` | partir con `\` o paréntesis |
| Import orden | mezclados | stdlib → terceros → locales, con línea en blanco entre grupos |
| Constante | `error_msg = 'X'` | `ERROR_MSG = 'X'` |
| Comentario de negocio | sin comentario en lógica SIVIGILA | `# SIVIGILA exporta fechas como seriales Excel (días desde 1899-12-30)` |

---

### Task 1: Crear estructura `services/`

**Files:**
- Create: `BACKEND/api/services/__init__.py`

- [ ] **Step 1: Crear el paquete**

```python
# BACKEND/api/services/__init__.py
# Capa de servicios: lógica de negocio desacoplada de HTTP.
# Las vistas delegan aquí; los servicios no conocen request/response.
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/services/__init__.py
git commit -m "feat: crear paquete services para capa de negocio"
```

---

### Task 2: `services/auth_service.py`

**Files:**
- Create: `BACKEND/api/services/auth_service.py`

- [ ] **Step 1: Escribir el archivo completo**

```python
"""Servicio de autenticación de usuarios.

Encapsula el registro y la verificación de credenciales,
desacoplando esta lógica de la capa HTTP.
"""
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status

from ..models import Usuario


def registrar_usuario(nombre, email, password):
    """Registra un nuevo usuario en el sistema.

    Valida que todos los campos estén presentes, que la contraseña
    tenga al menos 6 caracteres y que el email no esté ya registrado.

    Args:
        nombre: Nombre completo del usuario.
        email: Correo electrónico (se normaliza a minúsculas).
        password: Contraseña en texto plano (se almacena como hash).

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    if not nombre or not email or not password:
        return (
            {'error': 'Todos los campos son requeridos.'},
            status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return (
            {'error': 'La contraseña debe tener al menos 6 caracteres.'},
            status.HTTP_400_BAD_REQUEST,
        )

    if Usuario.objects.filter(email=email).exists():
        return (
            {'error': 'Ya existe una cuenta con este correo electrónico.'},
            status.HTTP_400_BAD_REQUEST,
        )

    usuario = Usuario.objects.create(
        nombre=nombre,
        email=email,
        password_hash=make_password(password),
    )
    data = {'id': usuario.id, 'nombre': usuario.nombre, 'email': usuario.email}
    return data, status.HTTP_201_CREATED


def autenticar_usuario(email, password):
    """Verifica las credenciales de un usuario.

    Args:
        email: Correo electrónico del usuario.
        password: Contraseña en texto plano para comparar con el hash.

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    if not email or not password:
        return (
            {'error': 'Correo y contraseña son requeridos.'},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Mensaje genérico para no revelar si el email existe en el sistema
        return (
            {'error': 'Correo o contraseña incorrectos.'},
            status.HTTP_401_UNAUTHORIZED,
        )

    if not check_password(password, usuario.password_hash):
        return (
            {'error': 'Correo o contraseña incorrectos.'},
            status.HTTP_401_UNAUTHORIZED,
        )

    data = {'id': usuario.id, 'nombre': usuario.nombre, 'email': usuario.email}
    return data, status.HTTP_200_OK
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/services/auth_service.py
git commit -m "feat: auth_service con registro y autenticacion de usuarios"
```

---

### Task 3: `services/upload_service.py`

**Files:**
- Create: `BACKEND/api/services/upload_service.py`

Extrae de `views.py`: toda la lógica de validación de columnas, lectura de Excel, procesamiento del DataFrame y persistencia del objeto `Analisis`.

- [ ] **Step 1: Escribir el archivo completo**

```python
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
from . import analisis_service


# ---------------------------------------------------------------------------
# Normalización de encabezados
# ---------------------------------------------------------------------------

def _normalizar_encabezado(valor):
    """Normaliza un encabezado de columna para comparación robusta.

    Convierte a minúsculas, elimina acentos, reemplaza variantes de
    'N°'/'Nº'/'No.' y colapsa espacios.

    Args:
        valor: Valor de celda (cualquier tipo); se convierte a str.

    Returns:
        Cadena normalizada lista para comparar.
    """
    texto = str(valor or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = texto.replace('n°', 'n ').replace('nº', 'n ').replace('no.', 'n ').replace('no ', 'n ')
    texto = re.sub(r'[^a-z0-9]+', ' ', texto)
    return ' '.join(texto.split())


@lru_cache(maxsize=4)
def _construir_mapa_alias(tipo):
    """Construye el mapa de alias → nombre canónico para un tipo de evento.

    Se cachea con lru_cache porque el mapa es constante durante la vida
    del proceso; construirlo en cada request es innecesario.

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
        columnas_archivo: Lista de nombres de columna tal como aparecen en el Excel.

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
    """Renombra columnas del DataFrame a sus nombres canónicos.

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
    o metadatos antes de los encabezados reales.

    Args:
        filas: Lista de filas (cada fila es una lista de valores).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de strings con los encabezados de la mejor fila.
    """
    mejor_fila = []
    mejor_puntaje = -1
    for fila in filas:
        columnas = [str(v).strip() for v in fila if v is not None and str(v).strip()]
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
            len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, fila))
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
    cuando solo se necesita verificar las columnas.

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
        Índice (int) de la fila con mayor coincidencia de columnas.
    """
    mejor_indice = 0
    mejor_puntaje = -1
    for indice in range(min(5, len(df_sin_encabezado.index))):
        fila = df_sin_encabezado.iloc[indice].tolist()
        columnas = [
            str(v).strip() for v in fila
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
        sheets: Dict {nombre_hoja: DataFrame} de pd.read_excel sheet_name=None.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Tupla (nombre_hoja, indice_encabezados).
    """
    mejor_hoja = None
    mejor_indice = 0
    mejor_puntaje = -1

    for nombre_hoja, dataframe in sheets.items():
        indice = _detectar_indice_encabezados_dataframe(dataframe, tipo)
        fila = dataframe.iloc[indice].tolist() if len(dataframe.index) > indice else []
        columnas = [str(v).strip() for v in fila if not pd.isna(v) and str(v).strip()]
        puntaje = (
            len(COLUMNAS_REQUERIDAS[tipo]) - len(_obtener_columnas_faltantes(tipo, columnas))
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
        DataFrame con columnas canónicas.
    """
    archivo.seek(0)
    hojas = pd.read_excel(archivo, engine='openpyxl', header=None, sheet_name=None)
    nombre_hoja, indice_encabezados = _seleccionar_hoja_y_encabezados_dataframe(hojas, tipo)

    archivo.seek(0)
    df = pd.read_excel(
        archivo, engine='openpyxl',
        header=indice_encabezados, sheet_name=nombre_hoja,
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
                top5 = df[COLUMNA_CAUSA_BASICA_CIE10].value_counts().head(5).to_dict()
                resumen['top5_causas'] = {str(k): int(v) for k, v in top5.items()}

        elif tipo == 'morbilidad':
            criterios_cols = [
                'Eclampsia', 'Sepsis sistémica severa',
                'Hemorragia obstétrica severa', 'Preeclampsia', 'Ruptura uterina',
            ]
            presentes = [c for c in criterios_cols if c in df.columns]
            if presentes:
                resumen['criterios_frecuencia'] = {
                    c: int(df[c].apply(es_valor_positivo).sum()) for c in presentes
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
        tipo: 'mortalidad' o 'morbilidad'. Solo mortalidad está implementado.

    Returns:
        DataFrame con los registros de la BD, o None si el tipo no aplica.
    """
    from ..views_constants import MORTALIDAD_ANALISIS_MAPPING
    from ..models import VMortalidadCompleta

    if tipo != 'mortalidad':
        return None

    registros = list(
        VMortalidadCompleta.objects.order_by('id_caso').values(
            *MORTALIDAD_ANALISIS_MAPPING.keys()
        )
    )
    if not registros:
        return pd.DataFrame(columns=MORTALIDAD_ANALISIS_MAPPING.values())

    dataframe = pd.DataFrame.from_records(registros)
    return dataframe.rename(columns=MORTALIDAD_ANALISIS_MAPPING)


def _construir_archivo_analisis_desde_dataframe(df_fuente, tipo, nombre_archivo):
    """Serializa un DataFrame limpio a un archivo Excel en memoria.

    Args:
        df_fuente: DataFrame ya procesado con preparar_dataframe_analisis.
        tipo: 'mortalidad' o 'morbilidad'.
        nombre_archivo: Nombre que tendrá el archivo guardado.

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


def _construir_archivo_analisis_acumulado(analisis_existente, df_nuevo, tipo, nombre_archivo):
    """Combina el archivo previo con el nuevo DataFrame para análisis acumulado.

    Cuando no hay datos en la BD (morbilidad), se acumulan los archivos
    históricos para que el análisis no pierda datos anteriores.

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
    df_acumulado = (
        pd.concat(dataframes, ignore_index=True) if len(dataframes) > 1 else dataframes[0]
    )
    return _construir_archivo_analisis_desde_dataframe(df_acumulado, tipo, nombre_archivo)


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def procesar_carga_archivo(request_data, request_files):
    """Orquesta la carga completa de un archivo Excel SIVIGILA.

    Flujo:
        1. Validar campos del formulario (tipo + archivo).
        2. Leer encabezados del Excel y verificar columnas requeridas.
        3. Leer el DataFrame completo y limpiarlo.
        4. Persistir en tablas SIVIGILA (dentro de transacción atómica).
        5. Construir o actualizar el registro Analisis.

    Args:
        request_data: request.data de DRF (contiene 'tipo').
        request_files: request.FILES de DRF (contiene 'archivo').

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    serializer = UploadSerializer(data={**request_data, **request_files})
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
                Analisis.objects.filter(tipo=tipo)
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
            {'error': f'No se pudo persistir el archivo en SIVIGILA: {str(error)}'},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    from ..serializers import AnalisisSerializer
    data = AnalisisSerializer(analisis).data
    data['sivigila'] = persistencia
    return data, status.HTTP_201_CREATED
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/services/upload_service.py
git commit -m "feat: upload_service con validacion, lectura y persistencia de Excel"
```

---

### Task 4: `services/analisis_service.py`

**Files:**
- Create: `BACKEND/api/services/analisis_service.py`

- [ ] **Step 1: Escribir el archivo completo**

```python
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

from ..models import Analisis
from ..processors import (
    MorbilidadProcessor,
    MortalidadProcessor,
    preparar_dataframe_analisis,
)
from .upload_service import _canonizar_columnas_dataframe


# ---------------------------------------------------------------------------
# Patrones para detección de columna opcional (edad, municipio, etc.)
# ---------------------------------------------------------------------------

_EXTRA_COL_PATTERNS = {
    'edad': ['edad', 'edad (anos)', 'edad (años)', 'edad anos', 'edad años'],
    'departamento': ['departamento', 'depto', 'dpto'],
    'municipio': ['municipio'],
    'regimen': ['regimen', 'régimen', 'afiliacion', 'afiliación'],
    'eps': ['eps', 'entidad promotora', 'aseguradora'],
}

# Orden de prioridad para elegir qué columna opcional mostrar
_EXTRA_COL_PRIORITY = ['municipio', 'departamento', 'edad', 'regimen', 'eps']


def _normalizar_extra(valor):
    """Normaliza un valor para comparación de columnas opcionales.

    Args:
        valor: Valor de cualquier tipo a normalizar.

    Returns:
        Cadena ASCII en minúsculas sin caracteres especiales.
    """
    texto = str(valor or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
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
            'ignore', category=UserWarning, message='.*Parsing dates.*'
        )
        fechas = pd.to_datetime(serie_clean, dayfirst=True, errors='coerce')

    if is_excel_serial.any():
        excel_days = s_numeric[is_excel_serial].astype(int)
        fechas_excel = pd.to_datetime(
            excel_days, unit='D', origin='1899-12-30', errors='coerce'
        )
        fechas = fechas.fillna(fechas_excel)

    # Intento adicional sin dayfirst para fechas en formato ambiguo
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
        Lista de nombres de columna candidatos, en orden de preferencia.
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
    from .upload_service import _normalizar_encabezado
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
                        distribucion_mensual[y_str] = {str(i): 0 for i in range(1, 13)}
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
        'chart' con datos del gráfico, o None si no se detectó columna.
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
            ('25-29', 25, 29.999), ('30-34', 30, 34.999), ('35-39', 35, 39.999),
            ('40+', 40, 120),
        ]
        labels = [b[0] for b in buckets]
        values = [int(((edades >= b[1]) & (edades <= b[2])).sum()) for b in buckets]
        resultado = {
            'chart': {
                'type': 'bar', 'orientation': 'v',
                'title': 'Distribución por edad',
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels, 'values': values,
                'total': int(sum(values)),
                'xTitle': 'Rango de edad (años)', 'yTitle': 'Casos',
            }
        }
    else:
        def _clean_cell(val):
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

        sorted_cats = sorted(counts_map.items(), key=lambda x: x[1], reverse=True)
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
                'type': 'bar', 'orientation': 'h',
                'title': title_map.get(kind, 'Distribución'),
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels, 'values': values,
                'total': int(sum(values)),
                'xTitle': 'Casos', 'yTitle': '',
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
        df, limpieza = preparar_dataframe_analisis(
            pd.read_excel(analisis.archivo.path, engine='openpyxl')
        )

        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = (
                processor.clustering_jerarquico()
                if tipo_clustering == 'jerarquico'
                else processor.clustering_factores_riesgo(n_clusters=n_clusters)
            )
        else:
            processor = MorbilidadProcessor(df)
            resultado = processor.clustering_perfiles_morbilidad(n_clusters=n_clusters)

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

    Solo disponible para morbilidad; retorna error 400 para mortalidad.

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
        df, limpieza = preparar_dataframe_analisis(
            pd.read_excel(analisis.archivo.path, engine='openpyxl')
        )
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
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/services/analisis_service.py
git commit -m "feat: analisis_service con completo, clustering, heatmap y extra-columna"
```

---

### Task 5: Crear `views_constants.py` y reescribir `views.py`

**Files:**
- Create: `BACKEND/api/views_constants.py`
- Modify: `BACKEND/api/views.py` (reemplazar completamente)

Primero extraer las constantes a `views_constants.py` (las necesitan tanto los servicios como las vistas):

- [ ] **Step 1: Crear `views_constants.py`**

```python
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
    'A. Nombres y Apellidos', COLUMNA_TIPO_ID_MORTALIDAD, COLUMNA_NUMERO_ID_MORTALIDAD,
    '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
    '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
    '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
    COLUMNA_NUM_CPN_MORTALIDAD, '8.2 Semana inicio CPN', COLUMNA_MOMENTO_MUERTE,
    '9.2 Semana gestación', '9.4 Tipo de parto', COLUMNA_CAUSA_BASICA_CIE10,
    '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
    'Fecha de Nacimiento',
]

# Columnas mínimas requeridas para el Evento 549 — Morbilidad Materna Extrema
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

# Alias aceptados por columna para tolerar variaciones en los archivos de campo
ALIAS_COLUMNAS = {
    'morbilidad': {
        'Nombres y apellidos': ['Nombre y apellidos', 'Nombres y Apellidos'],
        'Tipo de ID': ['Tipo ID', 'Tipo identificación', 'Tipo de identificación'],
        'N° identificación': [
            'No identificación', 'Nro identificación', 'Nº identificación',
            'Número identificación', 'Numero identificacion',
        ],
        'N° gestaciones': [
            'No gestaciones', 'Nro gestaciones', 'Nº gestaciones', 'Numero gestaciones',
        ],
        'Partos vaginales': ['Partos Vaginales'],
        'Cesáreas': ['Cesareas'],
        'N° controles prenatales': [
            'No controles prenatales', 'Nro controles prenatales',
            'Nº controles prenatales', 'Numero controles prenatales',
        ],
        'Causa principal CIE-10': ['Causa principal cie10', 'Causa principal CIE10'],
        'Días estancia hospitalaria': ['Dias estancia hospitalaria'],
        'Días estancia UCI': ['Dias estancia UCI'],
        'Fecha de Nacimiento': ['Fecha de nacimiento', 'Fecha nacimiento'],
        'Fecha de egreso': [
            'Fecha egreso', 'Fecha de egreso (dd/mm/aaaa)',
            'Fecha egreso (dd/mm/aaaa)', 'Fecha de egreso (dd/mm/yyyy)',
            'Fecha egreso (dd/mm/yyyy)',
        ],
    },
    'mortalidad': {
        COLUMNA_TIPO_ID_MORTALIDAD: ['B. Tipo de ID', 'B Tipo ID'],
        COLUMNA_NUMERO_ID_MORTALIDAD: ['C. Numero ID', 'C Número ID'],
        COLUMNA_NUM_CPN_MORTALIDAD: ['8.1 N° CPN', '8.1 Nº CPN', '8.1 Numero CPN'],
        'Fecha de Nacimiento': [
            'Fecha de nacimiento', 'Fecha nacimiento',
            'Fecha de Nacimiento (dd/mm/aaaa)', 'Fecha nacimiento (dd/mm/aaaa)',
        ],
        '5.2 Fecha de defunción': [
            '5.2 Fecha defunción', 'Fecha de defunción', 'Fecha defunción',
            '5.2 Fecha de defunción (dd/mm/aaaa)', '5.2 Fecha de defuncion (dd/mm/aaaa)',
            '5.2 Fecha de defuncion', '5.2 Fecha defuncion',
            'Fecha de defuncion', 'Fecha defuncion',
        ],
    },
}

# Mapeo campo_bd → columna_excel para reconstruir DataFrame desde VMortalidadCompleta
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
```

- [ ] **Step 2: Reescribir `views.py` completo (solo HTTP)**

```python
"""Vistas HTTP de la API de mortalidad y morbilidad materna.

Cada vista parsea el request, delega la lógica de negocio al servicio
correspondiente y retorna el Response. No contiene lógica de dominio.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    Analisis,
    CasoMorbilidad,
    CasoMortalidad,
    Paciente,
    VMorbilidadCompleta,
    VMortalidadCompleta,
)
from .serializers import (
    AnalisisSerializer,
    MorbilidadCompletaSerializer,
    MortalidadCompletaSerializer,
    PacienteSerializer,
)
from .services import analisis_service, auth_service, upload_service

ERROR_ANALISIS_NO_ENCONTRADO = 'Análisis no encontrado.'


def _obtener_limite(request, default=100, maximo=500):
    """Extrae y valida el parámetro 'limit' de la query string.

    Args:
        request: Request de DRF.
        default: Valor por defecto si el parámetro no está presente.
        maximo: Límite máximo permitido.

    Returns:
        Entero entre 1 y maximo.
    """
    try:
        limite = int(request.query_params.get('limit', default))
    except (TypeError, ValueError):
        limite = default
    return max(1, min(limite, maximo))


def _obtener_analisis_unicos(lista):
    """Retorna solo el análisis más reciente por tipo.

    Garantiza que la lista de la UI muestre un único registro por
    tipo de evento (mortalidad / morbilidad), aunque haya historial.

    Args:
        lista: QuerySet o iterable de instancias Analisis.

    Returns:
        Lista de instancias Analisis ordenada por fecha descendente.
    """
    unicos = {}
    for analisis in lista:
        clave = analisis.tipo
        existente = unicos.get(clave)
        if existente is None or analisis.fecha_carga > existente.fecha_carga:
            unicos[clave] = analisis
    return sorted(unicos.values(), key=lambda a: a.fecha_carga, reverse=True)


# ---------------------------------------------------------------------------
# Endpoints de carga y listado de análisis
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def subir_archivo(request):
    """Recibe un Excel SIVIGILA y lo persiste como análisis.

    POST /api/subir/
    """
    data, http_status = upload_service.procesar_carga_archivo(
        request.data, request.FILES
    )
    return Response(data, status=http_status)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def listar_analisis(request):
    """Lista análisis guardados o sube uno nuevo.

    GET  /api/analisis/ — retorna el análisis más reciente por tipo.
    POST /api/analisis/ — equivalente a POST /api/subir/.
    """
    if request.method == 'GET':
        analisis = _obtener_analisis_unicos(Analisis.objects.all())
        return Response(AnalisisSerializer(analisis, many=True).data)

    data, http_status = upload_service.procesar_carga_archivo(
        request.data, request.FILES
    )
    return Response(data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def detalle_analisis(request, pk):
    """Retorna el detalle de un análisis por ID.

    GET /api/analisis/<id>/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(AnalisisSerializer(analisis).data)


# ---------------------------------------------------------------------------
# Endpoints de procesamiento de análisis
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def analisis_completo(request, pk):
    """Retorna estadísticas completas de un análisis, con filtros opcionales.

    GET /api/analisis/<id>/completo/?year=2023&month=3
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    year = request.query_params.get('year', '').strip() or None
    month = request.query_params.get('month', '').strip() or None

    resultado, http_status = analisis_service.obtener_analisis_completo(
        analisis, year, month
    )
    return Response(resultado, status=http_status)


@api_view(['POST'])
@permission_classes([AllowAny])
def clustering_analisis(request, pk):
    """Ejecuta clustering K-means o jerárquico sobre un análisis.

    POST /api/analisis/<id>/clustering/
    Body: {"tipo_clustering": "kmeans"|"jerarquico", "n_clusters": 3}
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    tipo_clustering = request.data.get('tipo_clustering', 'kmeans')
    n_clusters = request.data.get('n_clusters', 3)

    resultado, http_status = analisis_service.obtener_clustering(
        analisis, tipo_clustering, n_clusters
    )
    return Response(resultado, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_correlacion(request, pk):
    """Genera la matriz de correlación para un análisis de morbilidad.

    GET /api/analisis/<id>/heatmap/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    resultado, http_status = analisis_service.obtener_heatmap(analisis)
    return Response(resultado, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def extra_columna_analisis(request, pk):
    """Detecta y devuelve datos de columna opcional (edad/municipio/etc.).

    GET /api/analisis/<id>/extra-columna/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    resultado, http_status = analisis_service.obtener_extra_columna(analisis)
    return Response(resultado, status=http_status)


# ---------------------------------------------------------------------------
# Endpoints SIVIGILA
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def resumen_sivigila(request):
    """Retorna conteos de pacientes y casos SIVIGILA en BD.

    GET /api/sivigila/resumen/
    """
    return Response({
        'pacientes': Paciente.objects.count(),
        'casos_morbilidad': CasoMorbilidad.objects.count(),
        'casos_mortalidad': CasoMortalidad.objects.count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_pacientes(request):
    """Lista pacientes con paginación por 'limit'.

    GET /api/sivigila/pacientes/?limit=100
    """
    limite = _obtener_limite(request)
    pacientes = (
        Paciente.objects.select_related('id_tipo')
        .order_by('id_paciente')[:limite]
    )
    return Response(PacienteSerializer(pacientes, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_morbilidad_sivigila(request):
    """Lista casos de morbilidad con paginación por 'limit'.

    GET /api/sivigila/morbilidad/?limit=100
    """
    limite = _obtener_limite(request)
    casos = VMorbilidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MorbilidadCompletaSerializer(casos, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_mortalidad_sivigila(request):
    """Lista casos de mortalidad con paginación por 'limit'.

    GET /api/sivigila/mortalidad/?limit=100
    """
    limite = _obtener_limite(request)
    casos = VMortalidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MortalidadCompletaSerializer(casos, many=True).data)


# ---------------------------------------------------------------------------
# Endpoints de autenticación
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def register_usuario(request):
    """Registra un nuevo usuario en el sistema.

    POST /api/auth/register/
    Body: {"nombre": "...", "email": "...", "password": "..."}
    """
    data, http_status = auth_service.registrar_usuario(
        nombre=request.data.get('nombre', '').strip(),
        email=request.data.get('email', '').strip().lower(),
        password=request.data.get('password', ''),
    )
    return Response(data, status=http_status)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    """Autentica un usuario y retorna sus datos básicos.

    POST /api/auth/login/
    Body: {"email": "...", "password": "..."}
    """
    data, http_status = auth_service.autenticar_usuario(
        email=request.data.get('email', '').strip().lower(),
        password=request.data.get('password', ''),
    )
    return Response(data, status=http_status)
```

- [ ] **Step 3: Actualizar `upload_service.py` para importar desde `views_constants`**

En `upload_service.py`, reemplazar el import:
```python
from ..views_constants import (
    ALIAS_COLUMNAS,
    COLUMNA_CAUSA_BASICA_CIE10,
    COLUMNA_MOMENTO_MUERTE,
    COLUMNAS_REQUERIDAS,
    MORTALIDAD_ANALISIS_MAPPING,
)
```

- [ ] **Step 4: Commit**

```bash
git add BACKEND/api/views_constants.py BACKEND/api/views.py BACKEND/api/services/upload_service.py
git commit -m "refactor: separar views en capa HTTP pura + views_constants"
```

---

### Task 6: Refactorizar `processors.py`

**Files:**
- Modify: `BACKEND/api/processors.py` (estilo completo)

Aplicar en todo el archivo:
- Comillas simples en todas las cadenas
- Docstrings Google en todos los métodos públicos
- Comentarios de lógica de negocio donde el WHY no es obvio
- PEP 8: líneas ≤ 79 chars, imports al tope, 2 líneas entre defs de nivel superior
- Mover `import warnings` al nivel de módulo (actualmente está dentro de una función)

Ejemplo de transformación:

```python
# ANTES
def _limpiar_datos(self):
    """Limpia y normaliza los datos."""
    numeric_cols = [
        '6.5 Gestaciones', '6.6 Partos Vaginales', '6.7 Cesáreas',

# DESPUÉS
def _limpiar_datos(self):
    """Convierte columnas numéricas clave y elimina filas completamente vacías."""
    # Forzar numérico para tolerar celdas con texto ('N/A', '-', etc.)
    # que SIVIGILA a veces exporta en lugar de dejar la celda vacía
    numeric_cols = [
        '6.5 Gestaciones', '6.6 Partos Vaginales', '6.7 Cesáreas',
```

- [ ] **Step 1: Reescribir `processors.py` aplicando las reglas de estilo**

Leer el archivo actual, aplicar todas las transformaciones y escribirlo completo.

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/processors.py
git commit -m "style: pep8, comillas simples y docstrings en processors.py"
```

---

### Task 7: Refactorizar `models.py`

**Files:**
- Modify: `BACKEND/api/models.py`

- [ ] **Step 1: Reescribir `models.py` con estilo limpio**

Aplicar comillas simples, docstrings Google y PEP 8 al archivo completo.

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/models.py
git commit -m "style: pep8, comillas simples y docstrings en models.py"
```

---

### Task 8: Refactorizar `serializers.py`, `urls.py`, `apps.py`

**Files:**
- Modify: `BACKEND/api/serializers.py`
- Modify: `BACKEND/api/urls.py`
- Modify: `BACKEND/api/apps.py`

- [ ] **Step 1: Reescribir los tres archivos con estilo limpio**

`serializers.py`: agregar docstrings a cada clase y comillas simples.  
`urls.py`: comillas simples en nombres de URL.  
`apps.py`: comillas simples y docstring de módulo.

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/serializers.py BACKEND/api/urls.py BACKEND/api/apps.py
git commit -m "style: pep8, comillas simples y docstrings en serializers, urls, apps"
```

---

### Task 9: Refactorizar `sivigila_models.py`

**Files:**
- Modify: `BACKEND/api/sivigila_models.py`

- [ ] **Step 1: Reescribir `sivigila_models.py` con estilo limpio**

545 líneas de modelos `managed = False`. Aplicar: comillas simples, docstring de módulo, docstring en cada clase con descripción de la tabla BD que representa.

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/sivigila_models.py
git commit -m "style: pep8, comillas simples y docstrings en sivigila_models.py"
```

---

### Task 10: Refactorizar `sivigila_ingestion.py`

**Files:**
- Modify: `BACKEND/api/sivigila_ingestion.py`

883 líneas de lógica de persistencia SIVIGILA. Es el archivo más complejo de estilizar.

- [ ] **Step 1: Reescribir `sivigila_ingestion.py` con estilo limpio**

Aplicar: comillas simples, docstrings en cada función pública, comentarios explicando los mapeos de campos SIVIGILA (WHY: la estructura de tablas SIVIGILA no es obvia para quien no conoce el sistema), PEP 8 en líneas largas.

Ejemplo de comentario de negocio a agregar:
```python
# SIVIGILA usa tablas de catálogo normalizadas (cat_convivencia, cat_escolaridad, etc.)
# Los valores numéricos del Excel se mapean a instancias de estas tablas mediante
# get_or_create para tolerar variaciones en los catálogos entre versiones del sistema
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/sivigila_ingestion.py
git commit -m "style: pep8, comillas simples y docstrings en sivigila_ingestion.py"
```

---

## Self-Review

| Requisito del spec | Task que lo cubre |
|---|---|
| Separar capas (views → services) | Task 3, 4, 5 |
| `views.py` sin pandas/openpyxl | Task 5 |
| `services/auth_service.py` | Task 2 |
| `services/upload_service.py` | Task 3 |
| `services/analisis_service.py` | Task 4 |
| Comillas simples en todos los archivos | Tasks 2–10 |
| Docstrings Google en funciones públicas | Tasks 2–10 |
| Comentarios de lógica de negocio | Tasks 3, 4, 6, 10 |
| PEP 8 estricto | Tasks 2–10 |
| `processors.py` estilizado | Task 6 |
| `models.py` estilizado | Task 7 |
| `serializers.py`, `urls.py`, `apps.py` | Task 8 |
| `sivigila_models.py` estilizado | Task 9 |
| `sivigila_ingestion.py` estilizado | Task 10 |

Sin placeholders. Todos los archivos nuevos tienen código completo. Los archivos de estilo tienen reglas claras y ejemplos concretos.
