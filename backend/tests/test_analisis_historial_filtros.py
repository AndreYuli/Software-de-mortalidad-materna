"""Historial de cargas: período (año, mes, semana ISO), búsqueda y filtros en el servidor."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import Analisis
from main import app
from services import analisis_service


def _carga(db, nombre, tipo, fecha_utc):
    """Inserta una carga con la fecha (UTC) indicada."""
    db.add(
        Analisis(
            tipo=tipo,
            nombre_archivo=nombre,
            archivo_hash='h',
            archivo='/media/x.xlsx',
            fecha_carga=fecha_utc,
            total_registros=1,
            resumen={},
        )
    )
    db.commit()


@pytest.fixture
def cargas(db_session):
    """Cinco cargas repartidas en tipos, semanas, meses y años."""
    _carga(
        db_session, 'mortalidad_sem37.xlsx', 'mortalidad', datetime(2026, 9, 15, 15, 0)
    )  # sem 38
    _carga(
        db_session, 'morbilidad_sem37.xlsx', 'morbilidad', datetime(2026, 9, 10, 15, 0)
    )  # sem 37
    _carga(
        db_session, 'mortalidad_agosto.xlsx', 'mortalidad', datetime(2026, 8, 20, 15, 0)
    )  # sem 34
    _carga(
        db_session, 'morbilidad_agosto.xlsx', 'morbilidad', datetime(2026, 8, 27, 15, 0)
    )  # sem 35
    _carga(db_session, 'mortalidad_2025.xlsx', 'mortalidad', datetime(2025, 12, 3, 15, 0))  # sem 49
    return db_session


def _nombres(items):
    """Nombres de archivo, en el orden recibido."""
    return [a.nombre_archivo for a in items]


def test_periodo_de_carga_usa_hora_de_colombia_y_semana_iso():
    """El período se calcula en hora de Colombia y con semana ISO."""
    # Domingo 13-sep-2026 22:00 en Bogotá == lunes 14-sep 03:00 UTC: sigue en la semana 37
    assert analisis_service.periodo_de_carga(datetime(2026, 9, 14, 3, 0)) == (2026, 9, 37)
    # Lunes 14-sep 15:00 UTC (10:00 en Bogotá) ya es la semana 38
    assert analisis_service.periodo_de_carga(datetime(2026, 9, 14, 15, 0)) == (2026, 9, 38)


def test_periodo_de_carga_cruza_el_ano_en_hora_local():
    """Una carga de fin de año en UTC puede pertenecer aún al año anterior en Colombia."""
    # 1-ene-2027 03:00 UTC == 31-dic-2026 22:00 en Bogotá: pertenece a 2026
    assert analisis_service.periodo_de_carga(datetime(2027, 1, 1, 3, 0))[:2] == (2026, 12)


def test_sin_filtros_devuelve_todo_ordenado_por_fecha_desc(cargas):
    """Sin filtros se devuelven todas las cargas, la más reciente primero."""
    items, total = analisis_service.listar_historial(cargas)
    assert total == 5
    assert _nombres(items) == [
        'mortalidad_sem37.xlsx',
        'morbilidad_sem37.xlsx',
        'morbilidad_agosto.xlsx',
        'mortalidad_agosto.xlsx',
        'mortalidad_2025.xlsx',
    ]


def test_filtra_por_tipo(cargas):
    """El filtro por tipo solo devuelve cargas de ese evento."""
    items, total = analisis_service.listar_historial(cargas, tipo='morbilidad')
    assert total == 2
    assert {a.tipo for a in items} == {'morbilidad'}


@pytest.mark.parametrize(
    ('filtros', 'esperado'),
    [
        ({'year': 2025}, ['mortalidad_2025.xlsx']),
        ({'year': 2026, 'month': 8}, ['morbilidad_agosto.xlsx', 'mortalidad_agosto.xlsx']),
        ({'year': 2026, 'week': 37}, ['morbilidad_sem37.xlsx']),
        ({'month': 9, 'tipo': 'mortalidad'}, ['mortalidad_sem37.xlsx']),
        ({'year': 2024}, []),
    ],
)
def test_filtra_por_periodo(cargas, filtros, esperado):
    """Los filtros de año, mes y semana se combinan entre sí y con el tipo."""
    items, total = analisis_service.listar_historial(cargas, **filtros)
    assert _nombres(items) == esperado
    assert total == len(esperado)


@pytest.mark.parametrize(
    ('q', 'esperado'),
    [
        ('agosto', {'morbilidad_agosto.xlsx', 'mortalidad_agosto.xlsx'}),
        ('MORBILIDAD_SEM', {'morbilidad_sem37.xlsx'}),  # sin distinguir mayúsculas
        ('550', {'mortalidad_sem37.xlsx', 'mortalidad_agosto.xlsx', 'mortalidad_2025.xlsx'}),
        ('549', {'morbilidad_sem37.xlsx', 'morbilidad_agosto.xlsx'}),
        ('inexistente', set()),
    ],
)
def test_busca_por_nombre_tipo_o_evento(cargas, q, esperado):
    """La búsqueda cubre nombre de archivo, tipo y código de evento, sin distinguir mayúsculas."""
    items, total = analisis_service.listar_historial(cargas, q=q)
    assert set(_nombres(items)) == esperado
    assert total == len(esperado)


def test_una_busqueda_de_solo_espacios_equivale_a_no_buscar(cargas):
    """Un texto de solo espacios no filtra nada."""
    assert analisis_service.listar_historial(cargas, q='   ')[1] == 5


def test_el_total_y_la_paginacion_respetan_los_filtros(cargas):
    """El total y las páginas corresponden a las cargas que cumplen los filtros."""
    pagina1, total = analisis_service.listar_historial(
        cargas, page=1, per_page=2, tipo='mortalidad'
    )
    pagina2, total2 = analisis_service.listar_historial(
        cargas, page=2, per_page=2, tipo='mortalidad'
    )
    assert total == total2 == 3
    assert len(pagina1) == 2
    assert _nombres(pagina2) == ['mortalidad_2025.xlsx']
    assert analisis_service.listar_historial(cargas, page=5, per_page=2)[0] == []


def test_anios_disponibles_mas_reciente_primero(cargas):
    """Los años disponibles se listan del más reciente al más antiguo."""
    assert analisis_service.anios_historial(cargas) == [2026, 2025]


# --- Endpoint -----------------------------------------------------------------------------


@pytest.fixture
def client(cargas):
    """Cliente HTTP con BD y autenticación sustituidas."""
    app.dependency_overrides[get_db] = lambda: cargas
    app.dependency_overrides[get_current_user] = lambda: object()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_endpoint_incluye_periodo_en_cada_item_y_anios_disponibles(client):
    """El endpoint devuelve año, mes y semana por carga y los años disponibles."""
    r = client.get('/api/analisis/historial/', params={'year': 2026, 'week': 37})
    assert r.status_code == 200
    body = r.json()
    assert body['total'] == 1
    assert body['total_pages'] == 1
    assert body['anios_disponibles'] == [2026, 2025]
    item = body['items'][0]
    assert (item['anio'], item['mes'], item['semana']) == (2026, 9, 37)
    assert item['nombre_archivo'] == 'morbilidad_sem37.xlsx'


def test_endpoint_sin_resultados_devuelve_lista_vacia(client):
    """Sin coincidencias el endpoint responde 200 con lista vacía."""
    body = client.get('/api/analisis/historial/', params={'q': 'nada que coincida'}).json()
    assert body['items'] == []
    assert body['total'] == 0
    assert body['total_pages'] == 0


@pytest.mark.parametrize(
    'params',
    [{'tipo': 'otro'}, {'month': 13}, {'month': 0}, {'week': 54}, {'year': 1999}, {'q': 'x' * 101}],
)
def test_endpoint_rechaza_filtros_invalidos(client, params):
    """Los filtros fuera de rango o de tipo desconocido responden 422."""
    assert client.get('/api/analisis/historial/', params=params).status_code == 422
