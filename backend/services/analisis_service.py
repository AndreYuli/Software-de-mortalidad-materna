"""Lógica de negocio para carga y consulta de análisis de mortalidad y morbilidad."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis
from services import sivigila_service

# Re-exportar para que el router acceda vía analisis_service.*
from services._analisis_calculo import (  # noqa: F401
    calcular_completo,
    calcular_cruce,
    calcular_extra_columna,
    calcular_heatmap,
    ejecutar_clustering,
)
from services._analisis_excel import (
    _leer_columnas_excel,
    _leer_dataframe_excel,
    _obtener_columnas_faltantes,
    preparar_dataframe_analisis,
)
from services._analisis_historial import (  # noqa: F401
    anios_historial,
    buscar_historial,
    periodo_de_carga,
)
from services._analisis_persistencia import _construir_df_desde_bd, _guardar_df_como_excel

logger = logging.getLogger(__name__)


def procesar_subida(tipo: str, archivo: UploadFile, db: Session) -> dict[str, Any]:
    """Valida, persiste y genera el análisis de un archivo Excel subido.

    Args:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').
        archivo: Archivo Excel recibido por el endpoint.
        db: Sesión de base de datos.

    Returns:
        Dict con datos del análisis creado/actualizado y resumen SIVIGILA.

    Raises:
        ValueError: Si el archivo no es válido o faltan columnas requeridas.
        RuntimeError: Si falla la persistencia en base de datos.
    """
    archivo.file.seek(0)
    columnas = _leer_columnas_excel(archivo.file, tipo)
    if columnas is None:
        raise ValueError('No se pudo leer el archivo Excel.')

    faltantes = _obtener_columnas_faltantes(tipo, columnas)
    if faltantes:
        raise ValueError(f'Faltan columnas requeridas: {faltantes}')

    try:
        df = _leer_dataframe_excel(archivo.file, tipo)
    except Exception as exc:
        logger.exception('Error leyendo el contenido del archivo Excel')
        raise ValueError(f'No se pudo leer el contenido del archivo: {exc}') from exc

    df_cleaned, _ = preparar_dataframe_analisis(df)

    # --- Fase 1: operaciones DB + preparación de datos en memoria ---
    analisis_existente = (
        db.query(Analisis)
        .filter(Analisis.tipo == tipo)
        .order_by(Analisis.fecha_carga.desc(), Analisis.id.desc())
        .first()
    )

    try:
        persistencia = sivigila_service.persistir_dataframe(db, df_cleaned, tipo)
        df_bd = _construir_df_desde_bd(db, tipo)
    except Exception as exc:
        db.rollback()
        logger.exception('Error al procesar datos SIVIGILA')
        raise RuntimeError(f'Error al persistir en base de datos: {exc}') from exc

    if df_bd is not None:
        df_acum = df_bd
    else:
        dataframes = []
        if analisis_existente and analisis_existente.archivo:
            path = Path(analisis_existente.archivo.lstrip('/'))
            if path.exists():
                dataframes.append(pd.read_excel(path, engine='openpyxl'))
        dataframes.append(df_cleaned)
        df_acum = pd.concat(dataframes, ignore_index=True) if len(dataframes) > 1 else dataframes[0]

    # --- Fase 2: I/O de disco (fuera de la transacción) ---
    ruta, hash_, resumen, total = _guardar_df_como_excel(df_acum, archivo.filename)

    # --- Fase 3: transacción mínima — siempre inserta una fila nueva ---
    # Cada subida es un evento de carga distinto (ver historial de cargas);
    # el dataset acumulado que consumen los análisis vive en las tablas
    # SIVIGILA (paciente/caso_*), no en esta fila, así que insertar en vez
    # de actualizar no afecta los cálculos, solo preserva el historial.
    try:
        analisis = Analisis(
            tipo=tipo,
            nombre_archivo=archivo.filename,
            archivo_hash=hash_,
            archivo=ruta,
            total_registros=total,
            resumen=resumen,
            fecha_carga=datetime.now(timezone.utc),
        )
        db.add(analisis)

        db.commit()
    except ValueError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception('Error al confirmar el análisis en base de datos')
        raise RuntimeError(f'Error al persistir en base de datos: {exc}') from exc

    resultado_final: dict[str, Any] = {
        'id': analisis.id,
        'tipo': analisis.tipo,
        'nombre_archivo': analisis.nombre_archivo,
        'archivo': analisis.archivo,
        'fecha_carga': analisis.fecha_carga.isoformat(),
        'total_registros': analisis.total_registros,
        'resumen': analisis.resumen,
        'sivigila': persistencia,
    }
    return resultado_final


def listar_unicos(db: Session) -> list[Analisis]:
    """Devuelve el análisis más reciente de cada tipo.

    Args:
        db: Sesión de base de datos.

    Returns:
        Lista de análisis únicos ordenados por fecha descendente.
    """
    subq = (
        db.query(Analisis.tipo, func.max(Analisis.fecha_carga).label('max_fecha'))
        .group_by(Analisis.tipo)
        .subquery()
    )
    return (
        db.query(Analisis)
        .join(subq, (Analisis.tipo == subq.c.tipo) & (Analisis.fecha_carga == subq.c.max_fecha))
        .order_by(Analisis.fecha_carga.desc())
        .all()
    )


def listar_historial(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    q: str | None = None,
    tipo: str | None = None,
    year: int | None = None,
    month: int | None = None,
    week: int | None = None,
) -> tuple[list[Analisis], int]:
    """Devuelve el historial de análisis paginado, con búsqueda y filtros opcionales.

    Args:
        db: Sesión de base de datos.
        page: Número de página (1-indexed).
        per_page: Registros por página.
        q: Texto a buscar en el nombre del archivo, el tipo o el código del evento.
        tipo: 'mortalidad' o 'morbilidad'.
        year: Año de la carga.
        month: Mes de la carga (1-12).
        week: Semana ISO de la carga.

    Returns:
        Tupla (lista de análisis ordenados por fecha_carga desc, total que cumple los filtros).
    """
    return buscar_historial(db, page, per_page, q, tipo, year, month, week)
