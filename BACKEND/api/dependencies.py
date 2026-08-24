"""Dependencias reutilizables para inyección en los endpoints de FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.security import decode_access_token
from db.database import get_db
from db.models_sqlalchemy import Usuario

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> type[Usuario]:
    """Extrae y valida el token JWT del header Authorization.

    Args:
        credentials: Token Bearer extraído del header por FastAPI.
        db: Sesión de base de datos inyectada.

    Returns:
        El usuario autenticado.

    Raises:
        HTTPException: 401 si el token es inválido, expirado o el usuario no existe.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario.",
        )

    user = db.get(Usuario, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )

    return user
