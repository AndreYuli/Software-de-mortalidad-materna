"""Endpoints de autenticación: registro e inicio de sesión."""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password, verify_password
from core.tenant import resolver_secretaria
from db.database import get_db
from db.models_sqlalchemy import Usuario
from schemas.user_schema import TokenResponse, UsuarioLogin, UsuarioRegister, UsuarioResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/auth', tags=['auth'])

# Límite de intentos fallidos por correo (NIST SP 800-63B-4, 3.1.1.2: "SHALL implement a
# rate-limiting mechanism"; 3.2.2 fija como tope 100 intentos y permite uno menor).
# ponytail: contador en memoria por proceso; con varios workers cada uno cuenta aparte.
# Pasar a una tabla o a Redis si se despliega con más de un worker.
MAX_INTENTOS_FALLIDOS = 10
VENTANA_BLOQUEO_S = 15 * 60
_intentos_fallidos: dict[str, tuple[int, float]] = {}  # correo -> (fallos, inicio de ventana)

# Hash falso para gastar el mismo tiempo que un correo real y no revelar qué cuentas existen.
_HASH_FALSO = hash_password('contraseña-que-nadie-usa')


def reiniciar_intentos_fallidos() -> None:
    """Vacía el contador de intentos fallidos (lo usan las pruebas)."""
    _intentos_fallidos.clear()


def _bloqueado(email: str) -> bool:
    """True si el correo agotó sus intentos y la ventana de bloqueo sigue vigente."""
    fallos, inicio = _intentos_fallidos.get(email, (0, 0.0))
    if fallos and time.monotonic() - inicio > VENTANA_BLOQUEO_S:
        _intentos_fallidos.pop(email, None)
        return False
    return fallos >= MAX_INTENTOS_FALLIDOS


def _registrar_fallo(email: str) -> None:
    fallos, inicio = _intentos_fallidos.get(email, (0, time.monotonic()))
    _intentos_fallidos[email] = (fallos + 1, inicio)


@router.post('/register/', response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UsuarioRegister, db: Session = Depends(get_db)) -> UsuarioResponse:
    """Registra un nuevo usuario en el sistema.

    Args:
        user_in: Datos del formulario de registro.
        db: Sesión de base de datos inyectada.

    Returns:
        Los datos del usuario creado.

    Raises:
        HTTPException: 400 si el correo ya está registrado.
        HTTPException: 500 si falla la inserción en la base de datos.
    """
    if db.query(Usuario).filter(Usuario.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Ya existe una cuenta con este correo electrónico.',
        )

    # La secretaría es el tenant de datos: solo se aceptan valores del catálogo
    # controlado, nunca texto libre del cliente.
    try:
        departamento, secretaria, secretaria_codigo = resolver_secretaria(
            user_in.departamento_codigo, user_in.secretaria_codigo
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    usuario = Usuario(
        nombre=user_in.nombre,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        fecha_registro=datetime.now(timezone.utc),
        departamento=departamento,
        secretaria=secretaria,
        secretaria_codigo=secretaria_codigo,
    )
    try:
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    except Exception as exc:
        db.rollback()
        logger.exception('Error inesperado al registrar usuario en la base de datos.')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error interno al crear la cuenta.',
        ) from exc
    return usuario


@router.post('/login/', response_model=TokenResponse)
def login(credentials: UsuarioLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica un usuario y devuelve un token JWT.

    Args:
        credentials: Correo y contraseña del usuario.
        db: Sesión de base de datos inyectada.

    Returns:
        Token JWT de acceso.

    Raises:
        HTTPException: 401 si las credenciales son incorrectas.
        HTTPException: 429 tras 10 intentos fallidos seguidos del mismo correo.
    """
    if _bloqueado(credentials.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Demasiados intentos fallidos. Inténtalo de nuevo en unos 15 minutos.',
        )

    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    hash_a_verificar = usuario.password_hash if usuario else _HASH_FALSO
    clave_valida = verify_password(credentials.password, hash_a_verificar)

    if not usuario or not clave_valida:
        _registrar_fallo(credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Correo o contraseña incorrectos.',
        )

    _intentos_fallidos.pop(credentials.email, None)
    token = create_access_token(data={'sub': str(usuario.id)})
    respuesta_token = TokenResponse(
        access_token=token,
        token_type='bearer',
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        departamento=usuario.departamento,
        secretaria=usuario.secretaria,
        secretaria_codigo=usuario.secretaria_codigo,
    )
    return respuesta_token
