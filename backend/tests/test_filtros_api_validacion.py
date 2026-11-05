"""Validación del formato de year/month/week/day en los endpoints de análisis (sobre PostgreSQL)."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import Analisis
from main import app
from services._analisis_filtros import _filtrar_por_fecha

DF = pd.DataFrame({'Fecha de defunción': ['2026-03-10', '2026-04-15', '2025-04-20']})


@pytest.fixture
def client(db_session):
    """Client."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(secretaria_codigo=None)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture
def analisis_id(db_session):
    """Analisis id."""
    a = Analisis(
        tipo='mortalidad',
        nombre_archivo='t.xlsx',
        archivo_hash='h-prueba',
        archivo='media/t.xlsx',
        fecha_carga=datetime.now(timezone.utc),
        total_registros=1,
        resumen={},
    )
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a.id


@pytest.fixture
def espia(mocker):
    """Reemplaza calcular_completo por un espía que usa el filtro de fechas real."""
    llamadas = []

    def falso(**kw):
        """Registra la llamada y aplica el filtro de fechas real."""
        llamadas.append(kw)
        _filtrar_por_fecha(
            DF, 'mortalidad', kw.get('year'), kw.get('month'), kw.get('week'), kw.get('day')
        )
        return {'estadisticas_basicas': {'total_casos': 1}, 'tipo': 'mortalidad'}

    mocker.patch('api.routers.analisis.analisis_service.calcular_completo', side_effect=falso)
    return llamadas


MALOS = [
    'abc',
    '1.5',
    '-1',
    '12345',
    ' 2026',
    '2026 ',
    '2026\n',
    '1e3',
    '0x10',
    "' OR 1=1--",
    '<b>',
    '²',
]


@pytest.mark.parametrize('campo', ['year', 'month', 'week', 'day'])
@pytest.mark.parametrize('valor', MALOS)
def test_completo_rechaza_formato_invalido(client, analisis_id, espia, campo, valor):
    """Completo rechaza formato invalido."""
    r = client.get(f'/api/analisis/{analisis_id}/completo/', params={campo: valor})
    assert r.status_code == 422, (campo, valor, r.status_code, r.text[:120])
    assert 'invalid literal' not in r.text
    assert espia == []


@pytest.mark.parametrize(
    'campo,valor',
    [
        ('year', '2026'),
        ('month', '4'),
        ('week', '12'),
        ('day', '15'),
        ('year', ''),
        ('month', ''),
        ('week', ''),
        ('day', ''),
        ('year', '0'),
        ('month', '07'),
    ],
)
def test_completo_acepta_formato_valido(client, analisis_id, espia, campo, valor):
    """Completo acepta formato valido."""
    r = client.get(f'/api/analisis/{analisis_id}/completo/', params={campo: valor})
    assert r.status_code == 200, (campo, valor, r.status_code, r.text[:120])
    assert espia[0][campo] == valor


def test_completo_combinaciones(client, analisis_id, espia):
    """Completo combinaciones."""
    assert client.get(f'/api/analisis/{analisis_id}/completo/').status_code == 200
    r = client.get(
        f'/api/analisis/{analisis_id}/completo/',
        params={'year': '2026', 'month': '4', 'week': '15', 'day': '15'},
    )
    assert r.status_code == 200 and espia[-1]['year'] == '2026'
    assert (
        client.get(
            f'/api/analisis/{analisis_id}/completo/', params={'year': '2026', 'month': 'x'}
        ).status_code
        == 422
    )


def test_completo_analisis_inexistente_con_filtro_valido_da_404(client, espia):
    """Completo analisis inexistente con filtro valido da 404."""
    assert (
        client.get('/api/analisis/99999999/completo/', params={'year': '2026'}).status_code == 404
    )


@pytest.mark.parametrize('campo', ['year', 'month'])
@pytest.mark.parametrize('valor', MALOS)
def test_narrativa_rechaza_formato_invalido(client, analisis_id, espia, campo, valor):
    """Narrativa rechaza formato invalido."""
    r = client.get(
        f'/api/analisis/{analisis_id}/narrativa/resumen_ejecutivo/', params={campo: valor}
    )
    assert r.status_code == 422, (campo, valor, r.status_code)
    assert 'invalid literal' not in r.text


@pytest.mark.parametrize('campo', ['year', 'month'])
@pytest.mark.parametrize('valor', MALOS)
def test_chat_rechaza_formato_invalido(client, analisis_id, espia, campo, valor):
    """Chat rechaza formato invalido."""
    r = client.post(
        f'/api/analisis/{analisis_id}/chat/',
        params={campo: valor},
        json={'pregunta': 'hola', 'historial': []},
    )
    assert r.status_code == 422, (campo, valor, r.status_code)
    assert 'invalid literal' not in r.text


@pytest.mark.parametrize(
    'campo,valor', [('year', '2026'), ('month', '4'), ('year', ''), ('month', '')]
)
def test_narrativa_acepta_valores_validos(client, analisis_id, espia, mocker, campo, valor):
    """Narrativa acepta valores validos."""
    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa', return_value={'narrativa': 'x'}
    )
    r = client.get(
        f'/api/analisis/{analisis_id}/narrativa/resumen_ejecutivo/', params={campo: valor}
    )
    assert r.status_code != 422, (campo, valor, r.text[:150])


def test_historial_no_cambia(client):
    """Historial no cambia."""
    assert client.get('/api/analisis/historial/', params={'year': 'abc'}).status_code == 422
    assert client.get('/api/analisis/historial/', params={'year': '2026'}).status_code == 200
