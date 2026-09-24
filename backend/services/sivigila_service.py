"""Persistencia de registros SIVIGILA en la base de datos."""

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    CasoMorbilidad,
    CasoMortalidad,
    CatSitioDefuncion,
    Paciente,
    SivigilaImportacion,
)
from services._sivigila_catalog import _resolve_catalog
from services._sivigila_escritura import (
    _MORBILIDAD_FECHA_EGRESO_COLS,
    _MORTALIDAD_FECHA_DEFUNCION_COLS,
    _MORTALIDAD_MOMENTO_MUERTE_COLS,
    _actualizar_caso_mortalidad,
    _get_value,
    _registrar_importacion,
    _resolve_momento_ocurrencia,
    _resolver_identificacion,
)
from services._sivigila_helpers import (
    SivigilaCaches,
    _date_key,
    _DatosPasada1,
    _hash_payload,
    _precargar_caches_sivigila,
    _row_hash,
)
from services._sivigila_morbilidad import _escribir_relacionados_morbilidad
from services._sivigila_mortalidad import _escribir_relacionados_mortalidad
from utils.column_validators import _require_text
from utils.date_parsers import _parse_date
from utils.type_parsers import _parse_int

logger = logging.getLogger(__name__)


def _fase1_validar_filas(
    tipo: str,
    registros: pd.DataFrame,
    df_hashes: pd.Series,
    existing_hashes: set[str],
    db: Session,
    catalog_cache: dict[Any, Any],
    resumen: dict[str, Any],
) -> tuple[list[int], dict[int, _DatosPasada1], set[str], list[str]]:
    """Identifica y prepara los datos de las filas no duplicadas.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.
        registros: DataFrame limpio sin filas completamente vacías.
        df_hashes: Serie con el hash de cada fila, indexada igual que registros.
        existing_hashes: Conjunto de hashes ya presentes en la BD.
        db: Sesión de base de datos.
        catalog_cache: Caché de catálogos compartido por la petición.
        resumen: Dict de contadores que se actualiza en lugar.

    Returns:
        Tupla (non_dup_indices, pass1_data, numeros_id, event_hashes).
    """
    non_dup_indices: list[int] = []
    pass1_data: dict[int, _DatosPasada1] = {}
    numeros_id: set[str] = set()
    event_hashes: list[str] = []

    for index, row in registros.iterrows():
        numero_fila = index + 2
        row_hash = df_hashes.loc[index]
        resumen['registros_procesados'] += 1

        if row_hash in existing_hashes:
            resumen['filas_omitidas_duplicadas'] += 1
            continue

        non_dup_indices.append(index)

        if tipo == 'morbilidad':
            ident = _resolver_identificacion(
                db=db,
                nombres_cols=[
                    'Nombres y apellidos',
                    'A. Nombres y apellidos del paciente',
                    'A. Nombres y apellidos',
                ],
                tipo_id_cols=[
                    'Tipo de ID',
                    'Tipo de identificación',
                    'B. Tipo ID',
                    'B. Tipo de ID',
                ],
                numero_id_cols=[
                    'N° identificación',
                    'Número de identificación',
                    'C. Número ID',
                    'C. Número de identificación',
                ],
                row=row,
                numero_fila=numero_fila,
                catalog_cache=catalog_cache,
            )
            fecha_egreso = _parse_date(_get_value(row, _MORBILIDAD_FECHA_EGRESO_COLS))
            causa = _require_text(
                _get_value(row, ['Causa principal CIE-10']),
                'Causa principal CIE-10',
                numero_fila,
            ).upper()
            momento = _resolve_momento_ocurrencia(_get_value(row, ['Momento ocurrencia']))
            edad_gestacional = _parse_int(_get_value(row, ['Edad gestacional ocurrencia (sem)']))
            event_hash = _hash_payload(
                {
                    'tipo': 'morbilidad',
                    'tipo_identificacion': ident['tipo_codigo'],
                    'numero_id': ident['numero_id'],
                    'fecha_egreso': _date_key(fecha_egreso),
                    'causa_principal_cie10': causa,
                    'momento_ocurrencia': momento,
                    'edad_gestacional_sem': edad_gestacional,
                }
            )
            pass1_data[index] = _DatosPasada1(
                ident=ident,
                event_hash=event_hash,
                row_hash=row_hash,
                causa=causa,
                fecha_egreso=fecha_egreso,
            )
        else:
            ident = _resolver_identificacion(
                db=db,
                nombres_cols=[
                    'A. Nombres y Apellidos',
                    'A. Nombres y apellidos del paciente',
                    'Nombres y apellidos',
                ],
                tipo_id_cols=['B. Tipo ID', 'Tipo de ID', 'Tipo de identificación'],
                numero_id_cols=['C. Número ID', 'N° identificación', 'Número de identificación'],
                row=row,
                numero_fila=numero_fila,
                catalog_cache=catalog_cache,
            )
            sitio = _resolve_catalog(
                db,
                CatSitioDefuncion,
                _get_value(row, ['5.1 Sitio de Defunción']),
                catalog_cache=catalog_cache,
                numero_fila=numero_fila,
                nombre_campo='5.1 Sitio de Defunción',
            )
            fecha_def = _parse_date(_get_value(row, _MORTALIDAD_FECHA_DEFUNCION_COLS))
            causa = _require_text(
                _get_value(row, ['10.1 Causa básica CIE-10']),
                '10.1 Causa básica CIE-10',
                numero_fila,
            ).upper()
            event_hash = _hash_payload(
                {
                    'tipo': 'mortalidad',
                    'tipo_identificacion': ident['tipo_codigo'],
                    'numero_id': ident['numero_id'],
                    'fecha_defuncion': _date_key(fecha_def),
                    'causa_basica_cie10': causa,
                    'sitio_defuncion': sitio.id,
                    'momento_muerte': _get_value(row, _MORTALIDAD_MOMENTO_MUERTE_COLS),
                    'semana_gestacion_muerte': _parse_int(
                        _get_value(row, ['9.2 Semana gestación'])
                    ),
                }
            )
            pass1_data[index] = _DatosPasada1(
                ident=ident,
                event_hash=event_hash,
                row_hash=row_hash,
                causa=causa,
                sitio=sitio,
                fecha_def=fecha_def,
            )

        numeros_id.add(ident['numero_id'])
        event_hashes.append(event_hash)

    return non_dup_indices, pass1_data, numeros_id, event_hashes


def _fase2_upsert_pacientes(
    non_dup_indices: list[int],
    pass1_data: dict[int, _DatosPasada1],
    caches: SivigilaCaches,
    db: Session,
    resumen: dict[str, Any],
) -> None:
    """Crea o actualiza pacientes en la BD y en el caché.

    Args:
        non_dup_indices: Índices de las filas no duplicadas del DataFrame.
        pass1_data: Datos preparados en la pasada 1, por índice de fila.
        caches: Cachés masivos cargados desde BD.
        db: Sesión de base de datos.
        resumen: Dict de contadores que se actualiza en lugar.
    """
    for index in non_dup_indices:
        ident = pass1_data[index].ident
        cache_key = ident['numero_id']
        if cache_key not in caches.paciente_cache:
            p = Paciente(
                id_tipo_id=ident['tipo_obj'].id,
                numero_id=ident['numero_id'],
                nombres_apellidos=ident['nombres'],
                fecha_nacimiento=ident.get('fecha_nacimiento'),
                creado_en=datetime.now(timezone.utc),
            )
            db.add(p)
            caches.paciente_cache[cache_key] = p
            resumen['pacientes_nuevos'] += 1
        else:
            p = caches.paciente_cache[cache_key]
            if p.id_tipo_id != ident['tipo_obj'].id:
                p.id_tipo_id = ident['tipo_obj'].id
            if p.nombres_apellidos != ident['nombres']:
                p.nombres_apellidos = ident['nombres']
            if ident.get('fecha_nacimiento') and p.fecha_nacimiento != ident['fecha_nacimiento']:
                p.fecha_nacimiento = ident['fecha_nacimiento']
            resumen['pacientes_existentes'] += 1


def _fase3_upsert_casos(
    tipo: str,
    non_dup_indices: list[int],
    pass1_data: dict[int, _DatosPasada1],
    caches: SivigilaCaches,
    db: Session,
    resumen: dict[str, Any],
) -> dict[int, tuple[Any, bool]]:
    """Crea o actualiza casos clínicos en la BD.

    Args:
        tipo: 'mortalidad' o 'morbilidad'.
        non_dup_indices: Índices de las filas no duplicadas del DataFrame.
        pass1_data: Datos preparados en la pasada 1, por índice de fila.
        caches: Cachés masivos cargados desde BD.
        db: Sesión de base de datos.
        resumen: Dict de contadores que se actualiza en lugar.

    Returns:
        Dict que mapea índice de fila a (instancia_caso, caso_creado).
    """
    row_cases: dict[int, tuple[Any, bool]] = {}

    for index in non_dup_indices:
        pdata = pass1_data[index]
        ident = pdata.ident
        paciente = caches.paciente_cache[ident['numero_id']]
        importacion = caches.import_cache.get(pdata.event_hash)
        caso = caches.caso_by_id.get(importacion.caso_id) if importacion else None

        if tipo == 'morbilidad':
            if caso is None:
                clave_busqueda = (paciente.id_paciente, pdata.fecha_egreso)
                caso_potencial = caches.caso_by_paciente_fecha.get(clave_busqueda)
                if caso_potencial:
                    causa_existente = caches.causa_cache.get(caso_potencial.id_caso)
                    if causa_existente and causa_existente.causa_principal_cie10 == pdata.causa:
                        caso = caso_potencial
            caso_creado = caso is None
            if caso_creado:
                caso = CasoMorbilidad(
                    id_paciente=paciente.id_paciente,
                    fecha_egreso=pdata.fecha_egreso,
                    creado_en=datetime.now(timezone.utc),
                )
                db.add(caso)
                caches.caso_by_paciente_fecha[clave_busqueda] = caso
                resumen['casos_creados'] += 1
            else:
                if pdata.fecha_egreso and caso.fecha_egreso != pdata.fecha_egreso:
                    caso.fecha_egreso = pdata.fecha_egreso
                resumen['casos_actualizados'] += 1
        else:
            if caso is None:
                clave_busqueda = (paciente.id_paciente, pdata.fecha_def)
                caso_potencial = caches.caso_by_paciente_fecha.get(clave_busqueda)
                if caso_potencial:
                    causa_existente = caches.causa_cache.get(caso_potencial.id_caso)
                    if causa_existente and causa_existente.causa_basica_cie10 == pdata.causa:
                        caso = caso_potencial
            caso_creado = caso is None
            if caso_creado:
                caso = CasoMortalidad(
                    id_paciente=paciente.id_paciente,
                    id_sitio_defuncion=pdata.sitio.id,
                    fecha_defuncion=pdata.fecha_def,
                    creado_en=datetime.now(timezone.utc),
                )
                db.add(caso)
                caches.caso_by_paciente_fecha[(paciente.id_paciente, pdata.fecha_def)] = caso
                resumen['casos_creados'] += 1
            else:
                _actualizar_caso_mortalidad(db, caso, pdata.sitio, pdata.fecha_def)
                resumen['casos_actualizados'] += 1

        row_cases[index] = (caso, caso_creado)

    return row_cases


def persistir_dataframe(db: Session, df: pd.DataFrame, tipo: str) -> dict[str, Any]:
    """Persiste un DataFrame de mortalidad o morbilidad en la base de datos.

    Usa cuatro pasadas (hashes → validación → pacientes → casos → relacionados)
    con cachés masivos para minimizar queries individuales.

    Args:
        db: Sesión de base de datos.
        df: DataFrame ya limpio con los datos del Excel.
        tipo: 'mortalidad' o 'morbilidad'.

    Returns:
        Dict con conteos de registros procesados, pacientes y casos.
    """
    catalog_cache: dict[Any, Any] = {}
    registros = df.dropna(how='all').copy()
    resumen: dict[str, Any] = {
        'tipo': tipo,
        'registros_procesados': 0,
        'filas_omitidas_duplicadas': 0,
        'pacientes_nuevos': 0,
        'pacientes_existentes': 0,
        'casos_creados': 0,
        'casos_actualizados': 0,
    }

    try:
        df_hashes = registros.apply(lambda r: _row_hash(tipo, r), axis=1)
        query = db.query(SivigilaImportacion.row_hash)
        hashes_bd = query.filter(SivigilaImportacion.row_hash.in_(df_hashes.tolist())).all()
        existing_hashes = set(row[0] for row in hashes_bd)
    except Exception:
        logger.warning(
            'Fallo al pre-cargar hashes en lote; usando fallback fila a fila',
            exc_info=True,
        )
        df_hashes = pd.Series(
            [_row_hash(tipo, r) for _, r in registros.iterrows()],
            index=registros.index,
        )
        existing_hashes = set()

    non_dup_indices, pass1_data, numeros_id, event_hashes = _fase1_validar_filas(
        tipo,
        registros,
        df_hashes,
        existing_hashes,
        db,
        catalog_cache,
        resumen,
    )

    if not non_dup_indices:
        return resumen

    caches = _precargar_caches_sivigila(db, tipo, numeros_id, event_hashes)

    _fase2_upsert_pacientes(non_dup_indices, pass1_data, caches, db, resumen)
    db.flush()

    row_cases = _fase3_upsert_casos(tipo, non_dup_indices, pass1_data, caches, db, resumen)
    db.flush()

    for index in non_dup_indices:
        row = registros.loc[index]
        pdata = pass1_data[index]
        caso, caso_creado = row_cases[index]

        if tipo == 'morbilidad':
            _escribir_relacionados_morbilidad(
                db,
                row,
                pdata,
                caso,
                caso_creado,
                caches.related_cache,
                catalog_cache,
            )
        else:
            _escribir_relacionados_mortalidad(
                db,
                row,
                pdata,
                caso,
                caso_creado,
                caches.related_cache,
                catalog_cache,
            )

        _registrar_importacion(
            db,
            tipo,
            pdata.row_hash,
            pdata.event_hash,
            caso.id_caso,
            pdata.ident,
        )

    return resumen
