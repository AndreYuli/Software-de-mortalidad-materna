"""Consulta del historial de cargas: período de cada carga (año, mes, semana) y filtros."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis

# `fecha_carga` se guarda en UTC sin zona horaria. El período se calcula en hora de Colombia:
# una carga el domingo por la noche ya es lunes en UTC y caería en la semana siguiente.
_ZONA_LOCAL = ZoneInfo('America/Bogota')
_EVENTO_POR_TIPO = {'mortalidad': '550', 'morbilidad': '549'}


def periodo_de_carga(fecha_carga: datetime) -> tuple[int, int, int]:
    """Calcula el período de una carga.

    La semana es la semana ISO, la misma que usan los filtros del dashboard.

    Args:
        fecha_carga: Fecha de la carga (UTC; si no trae zona horaria se asume UTC).

    Returns:
        Tupla (año, mes, semana ISO) en hora de Colombia.
    """
    if fecha_carga.tzinfo is None:
        fecha_carga = fecha_carga.replace(tzinfo=timezone.utc)
    local = fecha_carga.astimezone(_ZONA_LOCAL)
    return local.year, local.month, local.isocalendar().week


def buscar_historial(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    q: str | None = None,
    tipo: str | None = None,
    year: int | None = None,
    month: int | None = None,
    week: int | None = None,
) -> tuple[list[Analisis], int]:
    """Devuelve una página del historial de cargas aplicando búsqueda y filtros.

    El filtrado se hace en el servidor y el total corresponde a las cargas que cumplen los
    filtros, así que la paginación es coherente con ellos. El período se calcula en Python
    (hora de Colombia, semana ISO) sobre unas pocas columnas; las filas completas solo se
    cargan para la página pedida.

    Args:
        db: Sesión de base de datos.
        page: Número de página (1-indexed).
        per_page: Registros por página.
        q: Texto a buscar en el nombre del archivo, el tipo o el código del evento (549/550).
        tipo: 'mortalidad' o 'morbilidad'.
        year: Año de la carga.
        month: Mes de la carga (1-12).
        week: Semana ISO de la carga.

    Returns:
        Tupla (análisis de la página, ordenados por fecha de carga desc; total que cumple).
    """
    consulta = db.query(Analisis.id, Analisis.tipo, Analisis.nombre_archivo, Analisis.fecha_carga)
    if tipo:
        consulta = consulta.filter(Analisis.tipo == tipo)
    filas = consulta.order_by(Analisis.fecha_carga.desc(), Analisis.id.desc()).all()

    termino = (q or '').strip().lower()
    coincidentes: list[int] = []
    for id_, tipo_fila, nombre, fecha in filas:
        anio, mes, semana = periodo_de_carga(fecha)
        if year is not None and anio != year:
            continue
        if month is not None and mes != month:
            continue
        if week is not None and semana != week:
            continue
        if termino:
            evento = _EVENTO_POR_TIPO.get(tipo_fila, '')
            if termino not in f'{nombre} {tipo_fila} {evento}'.lower():
                continue
        coincidentes.append(id_)

    total = len(coincidentes)
    ids_pagina = coincidentes[(page - 1) * per_page : page * per_page]
    if not ids_pagina:
        return [], total
    por_id = {a.id: a for a in db.query(Analisis).filter(Analisis.id.in_(ids_pagina)).all()}
    return [por_id[i] for i in ids_pagina if i in por_id], total


def anios_historial(db: Session) -> list[int]:
    """Lista los años (más reciente primero) en los que hay cargas, para el filtro de año."""
    fechas = db.query(Analisis.fecha_carga).all()
    return sorted({periodo_de_carga(f)[0] for (f,) in fechas}, reverse=True)
