"""Helpers de hashing, tipos compartidos y carga masiva de cachés para SIVIGILA."""

import json
import logging
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Any

from sqlalchemy.orm import Session

from db.models_sqlalchemy import (
    AntecedenteMaterno,
    AntecedentePartoPuerperio,
    AntecedenteRiesgo,
    CasoMorbilidad,
    CasoMortalidad,
    CausaMuerte,
    CausasMorbilidad,
    ComplicacionEmbarazo,
    ControlPrenatal,
    Paciente,
    Referencia,
    SivigilaImportacion,
)
from utils.text_utils import clean_text, is_empty

logger = logging.getLogger(__name__)

_CHUNK_SIZE: int = 1000


@dataclass
class SivigilaCaches:
    """Cachés precargadas para la persistencia masiva de registros SIVIGILA."""

    paciente_cache: dict[str, Paciente]
    import_cache: dict[str, SivigilaImportacion]
    caso_by_id: dict[int, Any]
    caso_by_paciente_fecha: dict[tuple[int, Any], Any]
    causa_cache: dict[int, Any]
    related_cache: dict[type, set[int]]


@dataclass
class _DatosPasada1:
    """Datos intermedios por fila tras la validación de la pasada 1."""

    ident: dict[str, Any]
    event_hash: str
    row_hash: str
    causa: str
    fecha_egreso: date | None = None
    sitio: Any = None
    fecha_def: date | None = None


def _date_key(value: Any) -> str | None:
    """Convierte un objeto con isoformat() a su representación ISO, o None.

    Args:
        value: Objeto de fecha/hora con método isoformat(), o None.

    Returns:
        Cadena ISO si value no es None, de lo contrario None.
    """
    resultado: str | None
    if value is not None:
        resultado = value.isoformat()
    else:
        resultado = None
    return resultado


def _normalize_hash_value(value: Any) -> Any:
    """Normaliza un valor arbitrario para inclusión reproducible en hashes.

    Convierte valores vacíos a None, floats enteros a int, fechas a cadena
    ISO y texto a formato limpio.

    Args:
        value: Valor a normalizar; acepta Any porque puede ser cualquier
            celda de un DataFrame de pandas.

    Returns:
        Valor normalizado listo para serialización JSON determinista.
    """
    resultado: Any
    if is_empty(value):
        resultado = None
    elif isinstance(value, (int, float)):
        n: float = float(value)
        resultado = int(n) if n.is_integer() else n
    elif hasattr(value, 'isoformat'):
        try:
            resultado = value.isoformat()
        except TypeError:
            resultado = clean_text(value)
    else:
        resultado = clean_text(value)
    return resultado


def _row_hash(tipo: str, row: Any) -> str:
    """Genera un hash SHA-256 determinista para una fila de DataFrame.

    Args:
        tipo: Identificador del tipo de evento ('mortalidad' o 'morbilidad').
        row: Fila de pandas (Series) cuyas columnas se normalizan antes
            de generar el hash.

    Returns:
        Cadena hexadecimal SHA-256 de 64 caracteres.
    """
    col_names: list[str] = sorted(str(c) for c in row.index.tolist())
    normalizado: dict[str, Any] = {col: _normalize_hash_value(row[col]) for col in col_names}
    hash_generado: str = _hash_payload({'tipo': tipo, 'row': normalizado})
    return hash_generado


def _hash_payload(payload: dict[str, Any]) -> str:
    """Serializa un diccionario y retorna su hash SHA-256.

    Args:
        payload: Diccionario serializable a JSON con claves de cadena.

    Returns:
        Cadena hexadecimal SHA-256 de 64 caracteres.
    """
    serializado: str = json.dumps(
        payload, sort_keys=True, ensure_ascii=True, default=str, separators=(',', ':')
    )
    hash_generado: str = sha256(serializado.encode('utf-8')).hexdigest()
    return hash_generado


def _precargar_caches_sivigila(
    db: Session,
    tipo: str,
    numeros_id: set[str],
    event_hashes: list[str],
) -> SivigilaCaches:
    """Carga masiva de cachés desde BD para minimizar queries individuales.

    Args:
        db: Sesión de base de datos.
        tipo: 'mortalidad' o 'morbilidad'.
        numeros_id: Conjunto de números de ID de pacientes a precargar.
        event_hashes: Lista de hashes de eventos a buscar en importaciones.

    Returns:
        SivigilaCaches con todos los cachés precargados.
    """
    paciente_cache: dict[str, Paciente] = {}
    if numeros_id:
        for i in range(0, len(numeros_id), _CHUNK_SIZE):
            chunk: list[str] = list(numeros_id)[i : i + _CHUNK_SIZE]
            for p in db.query(Paciente).filter(Paciente.numero_id.in_(chunk)).all():
                paciente_cache[p.numero_id] = p

    import_cache: dict[str, SivigilaImportacion] = {}
    if event_hashes:
        unique_events: list[str] = list(set(event_hashes))
        for i in range(0, len(unique_events), _CHUNK_SIZE):
            chunk = unique_events[i : i + _CHUNK_SIZE]
            for imp in (
                db.query(SivigilaImportacion)
                .filter(SivigilaImportacion.tipo == tipo, SivigilaImportacion.event_hash.in_(chunk))
                .all()
            ):
                import_cache[imp.event_hash] = imp

    caso_model = CasoMorbilidad if tipo == 'morbilidad' else CasoMortalidad
    causa_model = CausasMorbilidad if tipo == 'morbilidad' else CausaMuerte
    fecha_field = 'fecha_egreso' if tipo == 'morbilidad' else 'fecha_defuncion'

    caso_by_id: dict[int, Any] = {}
    caso_by_paciente_fecha: dict[tuple[int, Any], Any] = {}
    causa_cache: dict[int, Any] = {}
    patient_ids: list[int] = [p.id_paciente for p in paciente_cache.values()]
    existing_caso_ids: list[int] = [imp.caso_id for imp in import_cache.values()]

    if patient_ids:
        for i in range(0, len(patient_ids), _CHUNK_SIZE):
            for c in (
                db.query(caso_model)
                .filter(caso_model.id_paciente.in_(patient_ids[i : i + _CHUNK_SIZE]))
                .all()
            ):
                caso_by_id[c.id_caso] = c
                caso_by_paciente_fecha[(c.id_paciente, getattr(c, fecha_field))] = c
                if c.id_caso not in existing_caso_ids:
                    existing_caso_ids.append(c.id_caso)

    if existing_caso_ids:
        for i in range(0, len(existing_caso_ids), _CHUNK_SIZE):
            for cau in (
                db.query(causa_model)
                .filter(causa_model.id_caso.in_(existing_caso_ids[i : i + _CHUNK_SIZE]))
                .all()
            ):
                causa_cache[cau.id_caso] = cau

    related_models = (
        [
            AntecedenteMaterno,
            AntecedenteRiesgo,
            ComplicacionEmbarazo,
            ControlPrenatal,
            AntecedentePartoPuerperio,
            CausaMuerte,
        ]
        if tipo == 'mortalidad'
        else [CausasMorbilidad, Referencia]
    )
    related_cache: dict[type, set[int]] = {m: set() for m in related_models}
    if existing_caso_ids:
        for model in related_models:
            for i in range(0, len(existing_caso_ids), _CHUNK_SIZE):
                for row in (
                    db.query(model.id_caso)
                    .filter(model.id_caso.in_(existing_caso_ids[i : i + _CHUNK_SIZE]))
                    .all()
                ):
                    related_cache[model].add(row[0])

    return SivigilaCaches(
        paciente_cache=paciente_cache,
        import_cache=import_cache,
        caso_by_id=caso_by_id,
        caso_by_paciente_fecha=caso_by_paciente_fecha,
        causa_cache=causa_cache,
        related_cache=related_cache,
    )
