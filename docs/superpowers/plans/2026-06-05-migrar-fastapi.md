# Migración a FastAPI + PostgreSQL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar Django por FastAPI como único backend, aplicando la arquitectura de servicios, caché TTL y PEP 8 completo.

**Architecture:** `main.py` solo con rutas HTTP que delegan a `services/`. Los servicios usan SQLAlchemy + PostgreSQL. Caché en memoria con `cachetools.TTLCache`. `processors.py` y `views_constants.py` viven en `api_fastapi/`.

**Tech Stack:** FastAPI 0.111, SQLAlchemy 2.0, psycopg2-binary, pydantic v2, cachetools, uvicorn, pandas, scikit-learn

---

## Archivos a crear/modificar

| Acción | Archivo |
|---|---|
| Eliminar | `BACKEND/api/`, `BACKEND/config/`, `BACKEND/manage.py` |
| Crear | `BACKEND/api_fastapi/processors.py` |
| Crear | `BACKEND/api_fastapi/views_constants.py` |
| Crear | `BACKEND/api_fastapi/services/__init__.py` |
| Crear | `BACKEND/api_fastapi/services/auth_service.py` |
| Crear | `BACKEND/api_fastapi/services/upload_service.py` |
| Crear | `BACKEND/api_fastapi/services/analisis_service.py` |
| Reescribir | `BACKEND/api_fastapi/main.py` |
| Actualizar | `BACKEND/api_fastapi/sivigila_ingestion.py` |
| Actualizar | `BACKEND/api_fastapi/database_views.py` |
| Actualizar | `BACKEND/api_fastapi/database.py` |
| Actualizar | `BACKEND/api_fastapi/schemas.py` |
| Actualizar | `BACKEND/api_fastapi/auth.py` |
| Actualizar | `BACKEND/api_fastapi/models_sqlalchemy.py` |
| Actualizar | `BACKEND/requirements.txt` |

---

### Task 1: Eliminar Django y limpiar requirements.txt

**Files:**
- Delete: `BACKEND/api/`, `BACKEND/config/`, `BACKEND/manage.py`
- Modify: `BACKEND/requirements.txt`

- [ ] **Step 1: Eliminar carpetas Django**

```powershell
Remove-Item -Recurse -Force BACKEND\api
Remove-Item -Recurse -Force BACKEND\config
Remove-Item -Force BACKEND\manage.py
Remove-Item -Force BACKEND\db.sqlite3 -ErrorAction SilentlyContinue
```

- [ ] **Step 2: Reescribir requirements.txt** (solo FastAPI + análisis, sin Django)

```
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
pydantic[email]==2.7.4
python-multipart==0.0.9
passlib[bcrypt]==1.7.4
cachetools==5.3.3
pandas==3.0.2
openpyxl==3.1.5
numpy==2.4.4
scikit-learn==1.6.1
scipy==1.15.1
python-dotenv==1.1.1
python-dateutil==2.9.0.post0
```

- [ ] **Step 3: Instalar cachetools**

```powershell
cd BACKEND; .\venv\Scripts\pip.exe install cachetools==5.3.3
```

- [ ] **Step 4: Commit**

```powershell
git add BACKEND/requirements.txt
git commit -m "chore: eliminar Django, agregar cachetools a requirements"
```

---

### Task 2: Crear `processors.py` y `views_constants.py` en `api_fastapi/`

**Files:**
- Create: `BACKEND/api_fastapi/processors.py`
- Create: `BACKEND/api_fastapi/views_constants.py`

- [ ] **Step 1: Crear `processors.py`**

Copiar el contenido limpio (PEP 8, docstrings, sin prints) del archivo `BACKEND/api/processors.py` que ya creamos, con una diferencia: el import en la primera línea cambia de `from api.processors import` a módulo autónomo.

El archivo es idéntico al `BACKEND/api/processors.py` ya refactorizado (que no tiene dependencias externas). Copiarlo directamente:

```python
"""Procesadores de datos para análisis de Mortalidad y Morbilidad Materna.

Contiene la lógica de análisis estadístico, clustering y reglas de negocio
para los eventos SIVIGILA 550 (Mortalidad) y 549 (Morbilidad Extrema).
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage

# ... (contenido completo de BACKEND/api/processors.py)
```

Acción: copiar `BACKEND/api/processors.py` → `BACKEND/api_fastapi/processors.py` sin modificaciones.

- [ ] **Step 2: Crear `views_constants.py`**

Copiar `BACKEND/api/views_constants.py` → `BACKEND/api_fastapi/views_constants.py` sin modificaciones. Ya está limpio.

- [ ] **Step 3: Commit**

```powershell
git add BACKEND/api_fastapi/processors.py BACKEND/api_fastapi/views_constants.py
git commit -m "feat: agregar processors.py y views_constants.py a api_fastapi"
```

---

### Task 3: Crear `services/__init__.py` y `services/auth_service.py`

**Files:**
- Create: `BACKEND/api_fastapi/services/__init__.py`
- Create: `BACKEND/api_fastapi/services/auth_service.py`

- [ ] **Step 1: Crear `services/__init__.py`**

```python
# Capa de servicios: lógica de negocio desacoplada de HTTP.
# Las rutas delegan aquí; los servicios no conocen Request/Response.
```

- [ ] **Step 2: Crear `services/auth_service.py`**

```python
"""Servicio de autenticación de usuarios.

Encapsula el registro y la verificación de credenciales,
desacoplando esta lógica de la capa HTTP.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_password_hash, verify_password
from ..models_sqlalchemy import Usuario


def registrar_usuario(db: Session, nombre: str, email: str, password: str) -> Usuario:
    """Registra un nuevo usuario en el sistema.

    Args:
        db: Sesión activa de SQLAlchemy.
        nombre: Nombre completo del usuario.
        email: Correo electrónico (ya normalizado a minúsculas).
        password: Contraseña en texto plano.

    Returns:
        Instancia Usuario recién creada.

    Raises:
        HTTPException 400: Si el email ya está registrado o la contraseña es muy corta.
    """
    import datetime

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='La contraseña debe tener al menos 6 caracteres.',
        )

    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ya existe una cuenta con este correo electrónico.',
        )

    usuario = Usuario(
        nombre=nombre.strip(),
        email=email,
        password_hash=get_password_hash(password),
        fecha_registro=datetime.datetime.utcnow(),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, password: str) -> Usuario:
    """Verifica las credenciales de un usuario.

    Args:
        db: Sesión activa de SQLAlchemy.
        email: Correo electrónico del usuario.
        password: Contraseña en texto plano.

    Returns:
        Instancia Usuario si las credenciales son válidas.

    Raises:
        HTTPException 401: Si el email no existe o la contraseña no coincide.
    """
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        # Mensaje genérico para no revelar si el email existe
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Correo o contraseña incorrectos.',
        )

    if not verify_password(password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Correo o contraseña incorrectos.',
        )

    return usuario
```

- [ ] **Step 3: Commit**

```powershell
git add BACKEND/api_fastapi/services/
git commit -m "feat: services/__init__.py y auth_service"
```

---

### Task 4: Crear `services/upload_service.py`

**Files:**
- Create: `BACKEND/api_fastapi/services/upload_service.py`

- [ ] **Step 1: Escribir el archivo completo**

```python
"""Servicio de carga y validación de archivos Excel SIVIGILA.

Orquesta la validación de columnas, la lectura del DataFrame,
la persistencia SIVIGILA y la creación del registro Analisis.
"""
import datetime
import re
import unicodedata
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import openpyxl
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models_sqlalchemy import Analisis, VMortalidadCompleta
from ..processors import es_valor_positivo, preparar_dataframe_analisis
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

def _normalizar_encabezado(valor: str) -> str:
    """Normaliza un encabezado de columna para comparación robusta.

    Args:
        valor: Valor de celda (cualquier tipo).

    Returns:
        Cadena normalizada ASCII en minúsculas.
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
def _construir_mapa_alias(tipo: str) -> dict:
    """Construye el mapa alias → nombre canónico para un tipo de evento.

    Se cachea con lru_cache porque el mapa es constante durante el proceso.

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


def _obtener_columnas_faltantes(tipo: str, columnas_archivo: list) -> list:
    """Retorna las columnas requeridas que no están en el archivo.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.
        columnas_archivo: Nombres de columna del Excel.

    Returns:
        Lista de columnas canónicas faltantes.
    """
    mapa_alias = _construir_mapa_alias(tipo)
    presentes = {
        mapa_alias[normalizada]
        for columna in columnas_archivo
        for normalizada in [_normalizar_encabezado(columna)]
        if normalizada in mapa_alias
    }
    return [col for col in COLUMNAS_REQUERIDAS[tipo] if col not in presentes]


def _canonizar_columnas_dataframe(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
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

def _seleccionar_fila_encabezados(filas: list, tipo: str) -> list:
    """Elige la fila con mayor coincidencia con las columnas requeridas.

    Args:
        filas: Lista de filas (cada una es lista de valores de celda).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de strings con los encabezados de la mejor fila.
    """
    mejor_fila: list = []
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


def _seleccionar_hoja_y_encabezados_openpyxl(workbook, tipo: str):
    """Encuentra la hoja y fila de encabezados con mejor coincidencia.

    Args:
        workbook: Workbook de openpyxl ya abierto.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Tupla (nombre_hoja, lista_encabezados).
    """
    mejor_fila: list = []
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


def leer_columnas_excel(file_like, tipo: str):
    """Lee solo los encabezados del Excel para validación rápida.

    Args:
        file_like: Objeto de archivo (BytesIO o UploadFile.file).
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Lista de strings con los encabezados, o None si falla.
    """
    try:
        wb = openpyxl.load_workbook(file_like, read_only=True, data_only=True)
        _, headers = _seleccionar_hoja_y_encabezados_openpyxl(wb, tipo)
        wb.close()
        return headers
    except Exception:
        return None


def _detectar_indice_encabezados_dataframe(
    df_sin_encabezado: pd.DataFrame, tipo: str
) -> int:
    """Detecta en qué fila están los encabezados de un DataFrame sin header.

    Args:
        df_sin_encabezado: DataFrame leído con header=None.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Índice de la fila con mayor coincidencia.
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


def _seleccionar_hoja_y_encabezados_dataframe(sheets: dict, tipo: str):
    """Selecciona hoja e índice de encabezados con mejor coincidencia.

    Args:
        sheets: Dict {nombre_hoja: DataFrame}.
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


def _leer_dataframe_excel(file_like, tipo: str) -> pd.DataFrame:
    """Lee el Excel completo y canoniza los nombres de columna.

    Args:
        file_like: Objeto de archivo.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        DataFrame con columnas canónicas.
    """
    file_like.seek(0)
    hojas = pd.read_excel(
        file_like, engine='openpyxl', header=None, sheet_name=None,
    )
    nombre_hoja, indice_encabezados = _seleccionar_hoja_y_encabezados_dataframe(
        hojas, tipo,
    )
    file_like.seek(0)
    df = pd.read_excel(
        file_like,
        engine='openpyxl',
        header=indice_encabezados,
        sheet_name=nombre_hoja,
    )
    return _canonizar_columnas_dataframe(df, tipo)


# ---------------------------------------------------------------------------
# Construcción del archivo de análisis
# ---------------------------------------------------------------------------

def _calcular_resumen_desde_dataframe(df: pd.DataFrame, tipo: str) -> dict:
    """Calcula estadísticas de resumen sobre un DataFrame ya limpio.

    Args:
        df: DataFrame procesado.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Dict con total_registros y estadísticas del tipo.
    """
    try:
        resumen: dict = {'total_registros': len(df)}

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
                resumen['top5_causas'] = {str(k): int(v) for k, v in top5.items()}

        elif tipo == 'morbilidad':
            criterios_cols = [
                'Eclampsia', 'Sepsis sistémica severa',
                'Hemorragia obstétrica severa', 'Preeclampsia', 'Ruptura uterina',
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


def _construir_dataframe_desde_bd(db: Session, tipo: str):
    """Reconstruye el DataFrame autoritativo desde la BD SIVIGILA.

    Solo implementado para mortalidad; morbilidad usa acumulado de archivos.

    Args:
        db: Sesión SQLAlchemy.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        DataFrame o None si el tipo no aplica.
    """
    from decimal import Decimal

    if tipo != 'mortalidad':
        return None

    registros = (
        db.query(VMortalidadCompleta)
        .order_by(VMortalidadCompleta.id_caso)
        .all()
    )
    if not registros:
        return pd.DataFrame(columns=list(MORTALIDAD_ANALISIS_MAPPING.values()))

    records = []
    for r in registros:
        d = {}
        for key in MORTALIDAD_ANALISIS_MAPPING:
            val = getattr(r, key, None)
            if isinstance(val, Decimal):
                d[key] = float(val) if val is not None else None
            elif hasattr(val, 'isoformat'):
                d[key] = val.isoformat()
            else:
                d[key] = val
        records.append(d)

    return pd.DataFrame.from_records(records).rename(
        columns=MORTALIDAD_ANALISIS_MAPPING
    )


def _construir_archivo_analisis(
    df_fuente: pd.DataFrame, tipo: str, nombre_archivo: str
) -> tuple:
    """Serializa el DataFrame a un archivo Excel en disco y calcula el hash.

    Args:
        df_fuente: DataFrame ya procesado.
        tipo: 'mortalidad' o 'morbilidad'.
        nombre_archivo: Nombre base del archivo.

    Returns:
        Tupla (ruta_relativa, archivo_hash, resumen, total_registros).
    """
    resumen = _calcular_resumen_desde_dataframe(df_fuente, tipo)
    total_registros = resumen.pop('total_registros', len(df_fuente))

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_fuente.to_excel(writer, index=False)

    contenido = buffer.getvalue()

    now = datetime.datetime.now()
    upload_dir = (
        Path('media') / 'uploads' / str(now.year) / f'{now.month:02d}'
    )
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = ''.join(
        c if c.isalnum() or c in ('.', '_', '-') else '_'
        for c in nombre_archivo
    )
    file_path = upload_dir / safe_name
    file_path.write_bytes(contenido)

    ruta_relativa = f'/media/uploads/{now.year}/{now.month:02d}/{safe_name}'
    archivo_hash = sha256(contenido).hexdigest()

    return ruta_relativa, archivo_hash, resumen, total_registros


def _construir_archivo_acumulado(
    db: Session,
    analisis_existente,
    df_nuevo: pd.DataFrame,
    tipo: str,
    nombre_archivo: str,
) -> tuple:
    """Combina el archivo previo con el nuevo DataFrame.

    Args:
        db: Sesión SQLAlchemy.
        analisis_existente: Instancia Analisis previa o None.
        df_nuevo: DataFrame del archivo recién cargado.
        tipo: 'mortalidad' o 'morbilidad'.
        nombre_archivo: Nombre del archivo resultante.

    Returns:
        Tupla (ruta_relativa, archivo_hash, resumen, total_registros).
    """
    dataframes = []

    if analisis_existente is not None and analisis_existente.archivo:
        try:
            clean_path = analisis_existente.archivo.lstrip('/')
            full_path = Path(clean_path)
            if full_path.exists():
                dataframes.append(pd.read_excel(full_path, engine='openpyxl'))
        except Exception:
            pass

    dataframes.append(df_nuevo.copy())
    df_acumulado = (
        pd.concat(dataframes, ignore_index=True)
        if len(dataframes) > 1
        else dataframes[0]
    )
    return _construir_archivo_analisis(df_acumulado, tipo, nombre_archivo)


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def procesar_carga_archivo(db: Session, tipo: str, archivo_file, filename: str) -> dict:
    """Orquesta la carga completa de un archivo Excel SIVIGILA.

    Flujo:
        1. Validar columnas requeridas.
        2. Leer y limpiar el DataFrame.
        3. Persistir en tablas SIVIGILA.
        4. Construir o actualizar el registro Analisis.

    Args:
        db: Sesión SQLAlchemy activa.
        tipo: 'mortalidad' o 'morbilidad'.
        archivo_file: Objeto de archivo (UploadFile.file).
        filename: Nombre original del archivo.

    Returns:
        Dict con datos del análisis creado + info SIVIGILA.

    Raises:
        HTTPException: En caso de error de validación o persistencia.
    """
    from ..services import analisis_service

    archivo_file.seek(0)
    columnas_archivo = leer_columnas_excel(archivo_file, tipo)
    if columnas_archivo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No se pudo leer el archivo. Verifica que sea un Excel válido.',
        )

    faltantes = _obtener_columnas_faltantes(tipo, columnas_archivo)
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'error': 'Faltan columnas requeridas.', 'columnas_faltantes': faltantes},
        )

    try:
        df = _leer_dataframe_excel(archivo_file, tipo)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No se pudo leer el contenido del Excel.',
        )

    df, _ = preparar_dataframe_analisis(df)

    try:
        analisis_existente = (
            db.query(Analisis)
            .filter(Analisis.tipo == tipo)
            .order_by(Analisis.fecha_carga.desc(), Analisis.id.desc())
            .first()
        )
        persistencia = persistir_dataframe_sivigila(db, df, tipo)

        df_autoritativo = _construir_dataframe_desde_bd(db, tipo)
        if df_autoritativo is not None:
            ruta, archivo_hash, resumen, total_registros = _construir_archivo_analisis(
                df_autoritativo, tipo, filename,
            )
        else:
            ruta, archivo_hash, resumen, total_registros = _construir_archivo_acumulado(
                db, analisis_existente, df, tipo, filename,
            )

        if analisis_existente is None:
            analisis = Analisis(
                tipo=tipo,
                nombre_archivo=filename,
                archivo_hash=archivo_hash,
                archivo=ruta,
                total_registros=total_registros,
                resumen=resumen,
                fecha_carga=datetime.datetime.utcnow(),
            )
            db.add(analisis)
        else:
            analisis_existente.nombre_archivo = filename
            analisis_existente.archivo_hash = archivo_hash
            analisis_existente.archivo = ruta
            analisis_existente.total_registros = total_registros
            analisis_existente.resumen = resumen
            analisis_existente.fecha_carga = datetime.datetime.utcnow()
            analisis = analisis_existente

        db.commit()
        db.refresh(analisis)

        # Invalidar caché al subir nuevo archivo
        analisis_service.invalidar_cache(analisis.id)

    except HTTPException:
        db.rollback()
        raise
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'No se pudo persistir el archivo en SIVIGILA: {str(exc)}',
        )

    return {
        'id': analisis.id,
        'tipo': analisis.tipo,
        'nombre_archivo': analisis.nombre_archivo,
        'archivo': analisis.archivo,
        'fecha_carga': analisis.fecha_carga.isoformat(),
        'total_registros': analisis.total_registros,
        'resumen': analisis.resumen,
        'sivigila': persistencia,
    }
```

- [ ] **Step 2: Commit**

```powershell
git add BACKEND/api_fastapi/services/upload_service.py
git commit -m "feat: upload_service con validacion Excel y persistencia Analisis"
```

---

### Task 5: Crear `services/analisis_service.py`

**Files:**
- Create: `BACKEND/api_fastapi/services/analisis_service.py`

- [ ] **Step 1: Escribir el archivo completo**

```python
"""Servicio de análisis de datos SIVIGILA para FastAPI.

Encapsula carga de DataFrame, filtrado por fecha, estadísticas,
clustering, heatmap y columna extra. Usa TTLCache (10 min) para
evitar re-procesar el Excel en cada petición.
"""
import re
import unicodedata
import warnings
from typing import Optional

import pandas as pd
from cachetools import TTLCache
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..processors import (
    MorbilidadProcessor,
    MortalidadProcessor,
    preparar_dataframe_analisis,
)
from .upload_service import _canonizar_columnas_dataframe, _normalizar_encabezado

# ---------------------------------------------------------------------------
# Caché en memoria: 50 entradas, 10 minutos de TTL
# ---------------------------------------------------------------------------

_cache: TTLCache = TTLCache(maxsize=50, ttl=600)


def invalidar_cache(analisis_id: int) -> None:
    """Elimina todas las entradas de caché del análisis indicado.

    Args:
        analisis_id: ID del análisis cuyas entradas deben eliminarse.
    """
    keys_to_delete = [k for k in list(_cache.keys()) if str(analisis_id) in str(k)]
    for key in keys_to_delete:
        _cache.pop(key, None)


# ---------------------------------------------------------------------------
# Columnas opcionales para gráfico adicional
# ---------------------------------------------------------------------------

_EXTRA_COL_PATTERNS = {
    'edad': ['edad', 'edad (anos)', 'edad (años)', 'edad anos', 'edad años'],
    'departamento': ['departamento', 'depto', 'dpto'],
    'municipio': ['municipio'],
    'regimen': ['regimen', 'régimen', 'afiliacion', 'afiliación'],
    'eps': ['eps', 'entidad promotora', 'aseguradora'],
}
_EXTRA_COL_PRIORITY = ['municipio', 'departamento', 'edad', 'regimen', 'eps']


def _normalizar_extra(valor: str) -> str:
    """Normaliza un valor para comparación de columnas opcionales."""
    texto = str(valor or '').strip().lower()
    texto = (
        unicodedata.normalize('NFKD', texto)
        .encode('ascii', 'ignore')
        .decode('ascii')
    )
    return re.sub(r'[^a-z0-9]+', ' ', texto).strip()


def _detectar_extra_columna(headers: list) -> tuple:
    """Detecta la primera columna opcional presente en los headers.

    Args:
        headers: Lista de nombres de columna del Excel.

    Returns:
        Tupla (kind, indice, nombre_columna) o (None, -1, None).
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

def _parse_serie_fechas(serie: pd.Series) -> pd.Series:
    """Parsea una Serie pandas con fechas en múltiples formatos SIVIGILA.

    Maneja datetime nativos, seriales Excel (días desde 1899-12-30)
    y strings DD/MM/YYYY.

    Args:
        serie: pd.Series con valores de fecha.

    Returns:
        pd.Series de tipo datetime64 con NaT donde no se pudo parsear.
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie

    s_numeric = pd.to_numeric(serie, errors='coerce')

    # SIVIGILA exporta fechas como seriales Excel en versiones < 2018
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

    por_vias_alternas = fechas.isna() & serie_clean.notna()
    if por_vias_alternas.any():
        fechas_alt = pd.to_datetime(
            serie_clean[por_vias_alternas].astype(str), errors='coerce',
        )
        fechas = fechas.fillna(fechas_alt)

    return fechas


def _candidatos_fecha(tipo: str) -> list:
    """Retorna los candidatos de columna de fecha para un tipo de evento."""
    if tipo == 'mortalidad':
        return [
            '9.3 Fecha parto (dd/mm/aaaa)', '9.3 Fecha parto',
            '5.2 Fecha de defunción', '5.2 Fecha de defuncion',
            'Fecha de defunción', 'Fecha de defuncion',
        ]
    return [
        'Fecha de egreso', 'Fecha egreso',
        'Fecha de egreso (dd/mm/aaaa)', 'Fecha egreso (dd/mm/aaaa)',
    ]


def _detectar_col_fecha(df: pd.DataFrame, tipo: str) -> Optional[str]:
    """Detecta qué columna de fecha está presente en el DataFrame."""
    candidatos = _candidatos_fecha(tipo)
    candidatos_norm = {_normalizar_encabezado(c) for c in candidatos}
    for col in df.columns:
        if col in candidatos or _normalizar_encabezado(col) in candidatos_norm:
            return col
    return None


# ---------------------------------------------------------------------------
# Servicio de análisis completo
# ---------------------------------------------------------------------------

def obtener_analisis_completo(
    db: Session, analisis, year: Optional[str], month: Optional[str],
) -> dict:
    """Carga y procesa el análisis completo con caché de 10 min.

    Args:
        db: Sesión SQLAlchemy (no usada directamente pero disponible).
        analisis: Instancia del modelo Analisis.
        year: Año para filtrar (str o None).
        month: Mes para filtrar (str o None).

    Returns:
        Dict con todas las estadísticas del análisis.

    Raises:
        HTTPException 404: Si el archivo físico no existe.
        HTTPException 500: Si el procesamiento falla.
    """
    from pathlib import Path

    cache_key = f'completo_{analisis.id}_{year or ""}_{month or ""}'
    if cache_key in _cache:
        return _cache[cache_key]

    clean_path = analisis.archivo.lstrip('/')
    full_path = Path(clean_path)
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='El archivo físico del análisis no existe en el servidor.',
        )

    try:
        df = pd.read_excel(full_path, engine='openpyxl')
        df = _canonizar_columnas_dataframe(df, analisis.tipo)
        df, limpieza = preparar_dataframe_analisis(df)

        col_fecha = _detectar_col_fecha(df, analisis.tipo)
        fechas_serie = None
        anos_disponibles: list = []
        distribucion_mensual: dict = {}

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

        archivo_url = analisis.archivo

        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = {
                'tipo': 'mortalidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga.isoformat(),
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
                'fecha_carga': analisis.fecha_carga.isoformat(),
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

        _cache[cache_key] = resultado
        return resultado

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error al procesar el análisis: {str(exc)}',
        )


def obtener_extra_columna(analisis) -> dict:
    """Detecta columna opcional (edad/municipio/etc.) y devuelve datos de gráfico.

    Solo disponible para mortalidad. Se cachea 10 min.

    Args:
        analisis: Instancia del modelo Analisis.

    Returns:
        Dict con clave 'chart' (datos del gráfico o None).
    """
    from pathlib import Path

    if analisis.tipo != 'mortalidad':
        return {'chart': None}

    cache_key = f'extra_col_{analisis.id}'
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        clean_path = analisis.archivo.lstrip('/')
        df = pd.read_excel(Path(clean_path), engine='openpyxl', nrows=2000)
    except Exception:
        return {'chart': None}

    kind, _col_idx, col_name = _detectar_extra_columna(list(df.columns))
    if kind is None:
        resultado = {'chart': None}
        _cache[cache_key] = resultado
        return resultado

    serie = df[col_name]

    if kind == 'edad':
        edades = pd.to_numeric(serie, errors='coerce')
        edades = edades[(edades >= 0) & (edades <= 120)].dropna()
        if len(edades) < 3:
            resultado = {'chart': None}
            _cache[cache_key] = resultado
            return resultado

        buckets = [
            ('<15', 0, 14.999), ('15-19', 15, 19.999), ('20-24', 20, 24.999),
            ('25-29', 25, 29.999), ('30-34', 30, 34.999),
            ('35-39', 35, 39.999), ('40+', 40, 120),
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
            _cache[cache_key] = resultado
            return resultado

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
            'departamento': 'Top departamentos', 'municipio': 'Top municipios',
            'regimen': 'Distribución por régimen', 'eps': 'Top EPS',
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

    _cache[cache_key] = resultado
    return resultado


def obtener_clustering(analisis, tipo_clustering: str, n_clusters: int) -> dict:
    """Ejecuta clustering K-means o jerárquico.

    Args:
        analisis: Instancia del modelo Analisis.
        tipo_clustering: 'kmeans' o 'jerarquico'.
        n_clusters: Número de clusters.

    Returns:
        Dict con los resultados del clustering.
    """
    from pathlib import Path

    clean_path = analisis.archivo.lstrip('/')
    full_path = Path(clean_path)
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='El archivo físico del análisis no existe.',
        )

    try:
        df_raw = pd.read_excel(full_path, engine='openpyxl')
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
            resultado = processor.clustering_perfiles_morbilidad(n_clusters=n_clusters)

        resultado['analisis_id'] = analisis.id
        resultado['tipo_analisis'] = analisis.tipo
        resultado['tipo_clustering'] = tipo_clustering
        resultado['limpieza_datos'] = limpieza
        return resultado

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error en clustering: {str(exc)}',
        )


def obtener_heatmap(analisis) -> dict:
    """Calcula la matriz de correlación para morbilidad.

    Args:
        analisis: Instancia del modelo Analisis.

    Returns:
        Dict con la matriz de correlación.

    Raises:
        HTTPException 400: Si el tipo no es morbilidad.
    """
    from pathlib import Path

    if analisis.tipo != 'morbilidad':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Heatmap solo disponible para análisis de morbilidad.',
        )

    clean_path = analisis.archivo.lstrip('/')
    full_path = Path(clean_path)
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='El archivo físico del análisis no existe.',
        )

    try:
        df_raw = pd.read_excel(full_path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df_raw)
        processor = MorbilidadProcessor(df)
        resultado = processor.heatmap_correlacion()
        resultado['analisis_id'] = analisis.id
        resultado['limpieza_datos'] = limpieza
        return resultado

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error al generar heatmap: {str(exc)}',
        )
```

- [ ] **Step 2: Commit**

```powershell
git add BACKEND/api_fastapi/services/analisis_service.py
git commit -m "feat: analisis_service con TTLCache, extra-columna, clustering y heatmap"
```

---

### Task 6: Reescribir `main.py` como HTTP puro

**Files:**
- Modify: `BACKEND/api_fastapi/main.py` (reemplazar completamente)

- [ ] **Step 1: Escribir el archivo completo**

```python
"""API REST de mortalidad y morbilidad materna — FastAPI.

Cada endpoint parsea el request, delega la lógica al servicio
correspondiente y retorna la respuesta. No contiene lógica de dominio.
"""
import os
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import get_db, engine
from .database_views import create_database_views
from .models_sqlalchemy import (
    Base,
    Analisis,
    CasoMorbilidad,
    CasoMortalidad,
    Paciente,
)
from .schemas import (
    AnalisisResponse,
    ClusteringRequest,
    UsuarioLogin,
    UsuarioRegister,
    UsuarioResponse,
)
from .services import analisis_service, auth_service, upload_service

# ---------------------------------------------------------------------------
# Inicialización: tablas Django + vistas SQL al arrancar
# ---------------------------------------------------------------------------

# Crear tablas gestionadas por SQLAlchemy (api_analisis, api_usuario, etc.)
# Excluir vistas — las crea database_views.py
_views_names = {'v_morbilidad_completa', 'v_mortalidad_completa'}
_tables_to_create = [
    t for name, t in Base.metadata.tables.items()
    if name not in _views_names
]
Base.metadata.create_all(bind=engine, tables=_tables_to_create)

# Recrear vistas SQL según el dialecto de BD (PostgreSQL, SQLite, MySQL)
_db_init = Session(bind=engine)
try:
    create_database_views(_db_init, engine.url.drivername)
finally:
    _db_init.close()

# ---------------------------------------------------------------------------
# Aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title='MaternAnalytics API',
    description='API de análisis de mortalidad y morbilidad materna SIVIGILA.',
    version='2.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

os.makedirs('media', exist_ok=True)
app.mount('/media', StaticFiles(directory='media'), name='media')

_ERROR_NO_ENCONTRADO = 'Análisis no encontrado.'


def _get_analisis_or_404(pk: int, db: Session) -> Analisis:
    """Obtiene un análisis por ID o lanza 404.

    Args:
        pk: ID del análisis.
        db: Sesión SQLAlchemy.

    Returns:
        Instancia Analisis.
    """
    analisis = db.query(Analisis).filter(Analisis.id == pk).first()
    if not analisis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_ERROR_NO_ENCONTRADO,
        )
    return analisis


def _obtener_analisis_unicos(lista: list) -> list:
    """Retorna solo el análisis más reciente por tipo de evento.

    Args:
        lista: Lista de instancias Analisis.

    Returns:
        Lista ordenada por fecha descendente, un elemento por tipo.
    """
    unicos: dict = {}
    for analisis in lista:
        clave = analisis.tipo
        existente = unicos.get(clave)
        if existente is None or analisis.fecha_carga > existente.fecha_carga:
            unicos[clave] = analisis
    return sorted(unicos.values(), key=lambda a: a.fecha_carga, reverse=True)


# ---------------------------------------------------------------------------
# Endpoints de carga y listado de análisis
# ---------------------------------------------------------------------------

@app.post('/api/subir/', status_code=status.HTTP_201_CREATED)
def subir_archivo(
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Recibe un Excel SIVIGILA y lo persiste como análisis.

    POST /api/subir/
    """
    return upload_service.procesar_carga_archivo(db, tipo, archivo.file, archivo.filename)


@app.get('/api/analisis/', response_model=List[AnalisisResponse])
def listar_analisis(db: Session = Depends(get_db)):
    """Lista el análisis más reciente por tipo.

    GET /api/analisis/
    """
    todos = db.query(Analisis).order_by(Analisis.fecha_carga.desc()).all()
    return _obtener_analisis_unicos(todos)


@app.post('/api/analisis/', status_code=status.HTTP_201_CREATED)
def crear_analisis(
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Equivalente a POST /api/subir/.

    POST /api/analisis/
    """
    return upload_service.procesar_carga_archivo(db, tipo, archivo.file, archivo.filename)


@app.get('/api/analisis/{pk}/', response_model=AnalisisResponse)
def detalle_analisis(pk: int, db: Session = Depends(get_db)):
    """Retorna el detalle de un análisis por ID.

    GET /api/analisis/{pk}/
    """
    return _get_analisis_or_404(pk, db)


# ---------------------------------------------------------------------------
# Endpoints de procesamiento de análisis
# ---------------------------------------------------------------------------

@app.get('/api/analisis/{pk}/completo/')
def analisis_completo(
    pk: int,
    year: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retorna estadísticas completas de un análisis con filtros opcionales.

    GET /api/analisis/{pk}/completo/?year=2023&month=3
    """
    analisis = _get_analisis_or_404(pk, db)
    year_clean = year.strip() if year else None
    month_clean = month.strip() if month else None
    return analisis_service.obtener_analisis_completo(db, analisis, year_clean, month_clean)


@app.post('/api/analisis/{pk}/clustering/')
def clustering_analisis(
    pk: int,
    req: ClusteringRequest,
    db: Session = Depends(get_db),
):
    """Ejecuta clustering K-means o jerárquico sobre un análisis.

    POST /api/analisis/{pk}/clustering/
    """
    analisis = _get_analisis_or_404(pk, db)
    return analisis_service.obtener_clustering(analisis, req.tipo_clustering, req.n_clusters)


@app.get('/api/analisis/{pk}/heatmap/')
def heatmap_correlacion(pk: int, db: Session = Depends(get_db)):
    """Genera la matriz de correlación para morbilidad.

    GET /api/analisis/{pk}/heatmap/
    """
    analisis = _get_analisis_or_404(pk, db)
    return analisis_service.obtener_heatmap(analisis)


@app.get('/api/analisis/{pk}/extra-columna/')
def extra_columna_analisis(pk: int, db: Session = Depends(get_db)):
    """Detecta y devuelve datos de columna opcional (edad/municipio/etc.).

    GET /api/analisis/{pk}/extra-columna/
    """
    analisis = _get_analisis_or_404(pk, db)
    return analisis_service.obtener_extra_columna(analisis)


# ---------------------------------------------------------------------------
# Endpoints SIVIGILA
# ---------------------------------------------------------------------------

@app.get('/api/sivigila/resumen/')
def resumen_sivigila(db: Session = Depends(get_db)):
    """Retorna conteos globales de pacientes y casos SIVIGILA.

    GET /api/sivigila/resumen/
    """
    return {
        'pacientes': db.query(Paciente).count(),
        'casos_morbilidad': db.query(CasoMorbilidad).count(),
        'casos_mortalidad': db.query(CasoMortalidad).count(),
    }


@app.get('/api/sivigila/pacientes/')
def listar_pacientes(
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Lista pacientes con paginación por 'limit'.

    GET /api/sivigila/pacientes/?limit=100
    """
    from .models_sqlalchemy import CatTipoId
    limite = max(1, min(limit or 100, 500))
    results = (
        db.query(Paciente, CatTipoId)
        .outerjoin(CatTipoId, Paciente.id_tipo_id == CatTipoId.id)
        .order_by(Paciente.id_paciente)
        .limit(limite)
        .all()
    )
    return [
        {
            'id_paciente': p.id_paciente,
            'nombres_apellidos': p.nombres_apellidos,
            'tipo_identificacion': t.codigo if t else None,
            'descripcion_tipo_identificacion': t.descripcion if t else None,
            'numero_id': p.numero_id,
            'fecha_nacimiento': p.fecha_nacimiento.isoformat() if p.fecha_nacimiento else None,
            'creado_en': p.creado_en.isoformat() if p.creado_en else None,
        }
        for p, t in results
    ]


@app.get('/api/sivigila/morbilidad/')
def listar_morbilidad_sivigila(
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Lista casos de morbilidad con paginación.

    GET /api/sivigila/morbilidad/?limit=100
    """
    from .models_sqlalchemy import VMorbilidadCompleta
    from decimal import Decimal
    import datetime

    limite = max(1, min(limit or 100, 500))
    try:
        casos = (
            db.query(VMorbilidadCompleta)
            .order_by(VMorbilidadCompleta.id_caso)
            .limit(limite)
            .all()
        )
        result = []
        for caso in casos:
            d = {}
            for c in caso.__table__.columns:
                val = getattr(caso, c.name)
                if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
                    d[c.name] = val.isoformat()
                elif isinstance(val, Decimal):
                    d[c.name] = float(val) if val is not None else None
                else:
                    d[c.name] = val
            result.append(d)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error al consultar v_morbilidad_completa: {str(exc)}',
        )


@app.get('/api/sivigila/mortalidad/')
def listar_mortalidad_sivigila(
    limit: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Lista casos de mortalidad con paginación.

    GET /api/sivigila/mortalidad/?limit=100
    """
    from .models_sqlalchemy import VMortalidadCompleta
    from decimal import Decimal
    import datetime

    limite = max(1, min(limit or 100, 500))
    try:
        casos = (
            db.query(VMortalidadCompleta)
            .order_by(VMortalidadCompleta.id_caso)
            .limit(limite)
            .all()
        )
        result = []
        for caso in casos:
            d = {}
            for c in caso.__table__.columns:
                val = getattr(caso, c.name)
                if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
                    d[c.name] = val.isoformat()
                elif isinstance(val, Decimal):
                    d[c.name] = float(val) if val is not None else None
                else:
                    d[c.name] = val
            result.append(d)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error al consultar v_mortalidad_completa: {str(exc)}',
        )


# ---------------------------------------------------------------------------
# Endpoints de autenticación
# ---------------------------------------------------------------------------

@app.post('/api/auth/register/', response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register_usuario(user_in: UsuarioRegister, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en el sistema.

    POST /api/auth/register/
    """
    return auth_service.registrar_usuario(
        db,
        nombre=user_in.nombre,
        email=user_in.email.strip().lower(),
        password=user_in.password,
    )


@app.post('/api/auth/login/', response_model=UsuarioResponse)
def login_usuario(credentials: UsuarioLogin, db: Session = Depends(get_db)):
    """Autentica un usuario y retorna sus datos básicos.

    POST /api/auth/login/
    """
    return auth_service.autenticar_usuario(
        db,
        email=credentials.email.strip().lower(),
        password=credentials.password,
    )
```

- [ ] **Step 2: Commit**

```powershell
git add BACKEND/api_fastapi/main.py
git commit -m "refactor: main.py HTTP puro, delega a services/"
```

---

### Task 7: Actualizar `sivigila_ingestion.py` con matching flexible

**Files:**
- Modify: `BACKEND/api_fastapi/sivigila_ingestion.py`

Agregar match parcial y fallback en `_resolve_catalog_by_fields` — igual a lo que hicimos en el Django. Solo modificar esa función y `_resolve_catalog`.

- [ ] **Step 1: Editar `_resolve_catalog_by_fields`** — agregar Paso 2 de match parcial:

```python
def _resolve_catalog_by_fields(db, model, texto, *, code_field=None, extra_field=None):
    global _CATALOG_BY_FIELDS
    if model not in _CATALOG_BY_FIELDS:
        _CATALOG_BY_FIELDS[model] = db.query(model).all()

    if code_field:
        for obj in _CATALOG_BY_FIELDS[model]:
            code_val = getattr(obj, code_field, None)
            if code_val and str(code_val).strip().lower() == texto.lower():
                return obj

    simplificado = _slugify(texto)

    # Paso 1: match exacto de slug
    for candidato in _CATALOG_BY_FIELDS[model]:
        comparables = _catalog_comparables(candidato, code_field, extra_field)
        if any(_slugify(v) == simplificado for v in comparables):
            return candidato

    # Paso 2: match parcial — tolera variaciones de texto en archivos de campo
    if simplificado:
        for candidato in _CATALOG_BY_FIELDS[model]:
            comparables = _catalog_comparables(candidato, code_field, extra_field)
            slugs = [s for s in (_slugify(v) for v in comparables) if s]
            if any(simplificado in s or s in simplificado for s in slugs):
                return candidato

    return None
```

- [ ] **Step 2: Editar `_resolve_catalog`** — agregar fallback al primer elemento cuando `required=True`:

```python
# Al final de _resolve_catalog, reemplazar el raise ValueError por:
if required:
    global _CATALOG_BY_FIELDS
    if model not in _CATALOG_BY_FIELDS:
        _CATALOG_BY_FIELDS[model] = db.query(model).all()
    if _CATALOG_BY_FIELDS[model]:
        return _CATALOG_BY_FIELDS[model][0]
    raise ValueError(f'Fila {numero_fila}: catálogo vacío para {nombre_campo}.')
return None
```

- [ ] **Step 3: Eliminar prints de debug** de `database_views.py` (líneas `print("Database views created...")` y `print(f"Warning: ...")`):

Reemplazar en `database_views.py`:
```python
    try:
        db.execute(text(sql_morbilidad))
        db.execute(text(sql_mortalidad))
        db.commit()
    except Exception:
        db.rollback()
```

- [ ] **Step 4: Commit**

```powershell
git add BACKEND/api_fastapi/sivigila_ingestion.py BACKEND/api_fastapi/database_views.py
git commit -m "fix: matching flexible de catalogos y fallback en sivigila_ingestion"
```

---

### Task 8: Estilo PEP 8 + comillas simples + docstrings en archivos restantes

**Files:**
- Modify: `BACKEND/api_fastapi/database.py`
- Modify: `BACKEND/api_fastapi/schemas.py`
- Modify: `BACKEND/api_fastapi/auth.py`

- [ ] **Step 1: Reescribir `database.py`**

```python
"""Configuración de SQLAlchemy para FastAPI.

Crea el engine según el motor definido en DB_ENGINE del .env
y expone get_db() como dependency de FastAPI.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BASE_DIR / '.env')

_DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite').lower()

if _DB_ENGINE in ('postgresql', 'postgres'):
    _DB_USER = os.getenv('DB_USER', 'postgres')
    _DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    _DB_HOST = os.getenv('DB_HOST', 'localhost')
    _DB_PORT = os.getenv('DB_PORT', '5432')
    _DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
    DATABASE_URL = (
        f'postgresql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}'
    )
elif _DB_ENGINE == 'mysql':
    _DB_USER = os.getenv('DB_USER', 'root')
    _DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    _DB_HOST = os.getenv('DB_HOST', 'localhost')
    _DB_PORT = os.getenv('DB_PORT', '3306')
    _DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
    DATABASE_URL = (
        f'mysql+pymysql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}'
    )
else:
    DATABASE_URL = f'sqlite:///{_BASE_DIR / "db.sqlite3"}'

_connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency FastAPI que provee una sesión SQLAlchemy por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Reescribir `auth.py`**

```python
"""Helpers de autenticación compatibles con el hash Django PBKDF2.

Usa django_pbkdf2_sha256 de passlib para que los usuarios creados
en Django puedan iniciar sesión en la API FastAPI sin migrar contraseñas.
"""
from passlib.hash import django_pbkdf2_sha256


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash Django PBKDF2.

    Args:
        plain_password: Contraseña en texto plano.
        hashed_password: Hash almacenado en la BD.

    Returns:
        True si la contraseña coincide, False en caso contrario.
    """
    try:
        return django_pbkdf2_sha256.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera un hash Django PBKDF2 para una contraseña.

    Args:
        password: Contraseña en texto plano.

    Returns:
        Hash en formato Django PBKDF2.
    """
    return django_pbkdf2_sha256.hash(password)
```

- [ ] **Step 3: Reescribir `schemas.py`**

```python
"""Esquemas Pydantic v2 para validación y serialización de la API."""
from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioRegister(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""

    nombre: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UsuarioLogin(BaseModel):
    """Credenciales de autenticación."""

    email: EmailStr
    password: str


class UsuarioResponse(BaseModel):
    """Datos públicos del usuario autenticado."""

    id: int
    nombre: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class AnalisisResponse(BaseModel):
    """Representación serializada de un análisis guardado."""

    id: int
    tipo: str
    nombre_archivo: str
    archivo: str
    fecha_carga: datetime
    total_registros: int
    resumen: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ClusteringRequest(BaseModel):
    """Parámetros para solicitar un análisis de clustering."""

    tipo_clustering: str = 'kmeans'
    n_clusters: int = 3
```

- [ ] **Step 4: Commit**

```powershell
git add BACKEND/api_fastapi/database.py BACKEND/api_fastapi/auth.py BACKEND/api_fastapi/schemas.py
git commit -m "style: pep8, comillas simples y docstrings en database, auth, schemas"
```

---

### Task 9: Verificar que el servidor arranca y los endpoints responden

- [ ] **Step 1: Arrancar uvicorn**

```powershell
cd BACKEND
.\venv\Scripts\uvicorn.exe api_fastapi.main:app --port 8000
```

Esperado: arranca sin errores, muestra `Application startup complete.`

- [ ] **Step 2: Probar GET /api/analisis/**

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/analisis/" -UseBasicParsing | Select-Object StatusCode, Content
```

Esperado: `StatusCode: 200`

- [ ] **Step 3: Probar GET /api/analisis/{pk}/completo/ (dos veces para verificar caché)**

```powershell
$t1 = (Measure-Command { Invoke-WebRequest "http://127.0.0.1:8000/api/analisis/1/completo/" -UseBasicParsing }).TotalSeconds
$t2 = (Measure-Command { Invoke-WebRequest "http://127.0.0.1:8000/api/analisis/1/completo/" -UseBasicParsing }).TotalSeconds
"1a llamada: ${t1}s | 2a (cache): ${t2}s"
```

Esperado: 2ª llamada < 0.5s.

- [ ] **Step 4: Commit final**

```powershell
git add -A
git commit -m "feat: migracion completa a FastAPI con servicios, cache TTL y PEP 8"
```

---

## Self-Review

| Requisito del spec | Task |
|---|---|
| Eliminar Django | Task 1 |
| `processors.py` en `api_fastapi/` | Task 2 |
| `views_constants.py` en `api_fastapi/` | Task 2 |
| `services/auth_service.py` | Task 3 |
| `services/upload_service.py` | Task 4 |
| `services/analisis_service.py` con TTLCache | Task 5 |
| `main.py` HTTP puro | Task 6 |
| Matching flexible + fallback en ingestion | Task 7 |
| PEP 8, comillas simples, docstrings | Tasks 3-8 |
| Endpoint `/extra-columna/` | Task 5+6 |
| requirements.txt limpio | Task 1 |
| Servidor arranca y responde | Task 9 |
