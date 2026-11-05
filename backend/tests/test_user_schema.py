"""Pruebas del schema UsuarioRegister: límite de 150 caracteres en nombre."""

import pytest
from pydantic import ValidationError

from schemas.user_schema import UsuarioRegister


def datos_base(nombre: str) -> dict:
    """Arma un payload válido con el nombre indicado."""
    return {
        'nombre': nombre,
        'email': 'a@b.co',
        'password': 'secreto12',
        'departamento_codigo': 'antioquia',
        'secretaria_codigo': 'bello',
    }


def test_nombre_de_150_caracteres_es_valido():
    """150 caracteres es el límite exacto permitido."""
    usuario = UsuarioRegister(**datos_base('a' * 150))
    assert len(usuario.nombre) == 150


@pytest.mark.parametrize('largo', [151, 3000])
def test_nombre_mayor_a_150_rechazado(largo: int):
    """Más de 150 caracteres lanza ValidationError."""
    with pytest.raises(ValidationError):
        UsuarioRegister(**datos_base('a' * largo))
