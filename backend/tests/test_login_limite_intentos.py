"""Límite de intentos fallidos de inicio de sesión (NIST SP 800-63B-4, 3.1.1.2 y 3.2.2)."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.routers import auth as auth_router
from core.security import hash_password
from db.database import get_db
from db.models_sqlalchemy import Usuario
from main import app

CLAVE = 'clave-correcta-de-prueba'


@pytest.fixture
def client(db_session):
    """Cliente con la BD de prueba y el contador de intentos vacío."""
    app.dependency_overrides[get_db] = lambda: db_session
    auth_router.reiniciar_intentos_fallidos()
    db_session.add(
        Usuario(
            nombre='Ana',
            email='ana@test.co',
            password_hash=hash_password(CLAVE),
            fecha_registro=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()
    auth_router.reiniciar_intentos_fallidos()


def _login(client, clave, email='ana@test.co'):
    return client.post('/api/auth/login/', json={'email': email, 'password': clave})


def test_tras_10_fallos_se_bloquea_incluso_con_la_clave_correcta(client):
    """El intento 11 responde 429 aunque la clave sea la correcta."""
    for _ in range(auth_router.MAX_INTENTOS_FALLIDOS):
        assert _login(client, 'incorrecta').status_code == 401
    bloqueado = _login(client, CLAVE)
    assert bloqueado.status_code == 429
    assert 'intentos' in bloqueado.json()['detail'].lower()


def test_un_inicio_correcto_reinicia_el_contador(client):
    """Nueve fallos y un acierto: el contador vuelve a cero."""
    for _ in range(auth_router.MAX_INTENTOS_FALLIDOS - 1):
        _login(client, 'incorrecta')
    assert _login(client, CLAVE).status_code == 200
    for _ in range(auth_router.MAX_INTENTOS_FALLIDOS - 1):
        assert _login(client, 'incorrecta').status_code == 401
    assert _login(client, CLAVE).status_code == 200


def test_el_bloqueo_expira(client, mocker):
    """Pasada la ventana (15 min) se puede volver a intentar."""
    for _ in range(auth_router.MAX_INTENTOS_FALLIDOS):
        _login(client, 'incorrecta')
    assert _login(client, CLAVE).status_code == 429
    ahora = auth_router.time.monotonic()
    mocker.patch.object(auth_router.time, 'monotonic', return_value=ahora + 16 * 60)
    assert _login(client, CLAVE).status_code == 200


def test_el_bloqueo_es_por_correo(client):
    """Bloquear un correo no afecta a otro."""
    for _ in range(auth_router.MAX_INTENTOS_FALLIDOS):
        _login(client, 'incorrecta', email='otra@test.co')
    assert _login(client, CLAVE).status_code == 200


def test_correo_inexistente_tambien_verifica_un_hash(client, mocker):
    """Con correo inexistente se verifica un hash falso: el tiempo no revela si la cuenta existe."""
    espia = mocker.patch.object(auth_router, 'verify_password', return_value=False)
    assert _login(client, 'cualquiera-de-15-o-mas', email='noexiste@test.co').status_code == 401
    assert espia.call_count == 1
