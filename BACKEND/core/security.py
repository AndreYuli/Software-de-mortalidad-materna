"""Utilidades de seguridad: hashing de contraseñas y tokens JWT."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from core.config import Config

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano.

    Args:
        plain_password: Contraseña sin hashear.

    Returns:
        Hash bcrypt de la contraseña.
    """
    pwd_hash: str = _pwd_context.hash(plain_password)
    return pwd_hash


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash.

    Args:
        plain_password: Contraseña sin hashear ingresada por el usuario.
        hashed_password: Hash almacenado en la base de datos.

    Returns:
        True si la contraseña es correcta, False en caso contrario.
    """
    es_valido: bool = _pwd_context.verify(plain_password, hashed_password)
    return es_valido


def create_access_token(data: dict[str, Any]) -> str:
    """Crea un token JWT firmado con los datos proporcionados.

    Args:
        data: Payload a incluir en el token.

    Returns:
        Token JWT codificado como string.
    """
    payload = data.copy()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=Config.jwt_expiration_minutes)
    payload["exp"] = expiration
    token_jwt: str = jwt.encode(payload, Config.jwt_secret, algorithm=Config.jwt_algorithm)
    return token_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un token JWT.

    Args:
        token: Token JWT a decodificar.

    Returns:
        Payload del token si es válido, None si expiró o es inválido.
    """
    resultado: dict[str, Any] | None
    try:
        resultado = jwt.decode(token, Config.jwt_secret, algorithms=[Config.jwt_algorithm])
    except jwt.PyJWTError as exc:
        logger.warning("Error validando token JWT: %s", exc)
        resultado = None
    return resultado
