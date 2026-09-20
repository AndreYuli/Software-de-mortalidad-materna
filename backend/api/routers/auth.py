"""Endpoints de autenticación: registro e inicio de sesión."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password, verify_password
from db.database import get_db
from db.models_sqlalchemy import Usuario
from schemas.user_schema import TokenResponse, UsuarioLogin, UsuarioRegister, UsuarioResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/auth', tags=['auth'])


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

    usuario = Usuario(
        nombre=user_in.nombre,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        fecha_registro=datetime.now(timezone.utc),
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
    """
    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()

    if not usuario or not verify_password(credentials.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Correo o contraseña incorrectos.',
        )

    token = create_access_token(data={'sub': str(usuario.id)})
    respuesta_token = TokenResponse(
        access_token=token,
        token_type='bearer',
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
    )
    return respuesta_token
