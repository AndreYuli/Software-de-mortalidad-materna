"""Servicio de autenticación de usuarios.

Encapsula el registro y la verificación de credenciales,
desacoplando esta lógica de la capa HTTP.
"""
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status

from ..models import Usuario


def registrar_usuario(nombre, email, password):
    """Registra un nuevo usuario en el sistema.

    Valida que todos los campos estén presentes, que la contraseña
    tenga al menos 6 caracteres y que el email no esté ya registrado.

    Args:
        nombre: Nombre completo del usuario.
        email: Correo electrónico (se normaliza a minúsculas antes de llamar).
        password: Contraseña en texto plano (se almacena como hash).

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    if not nombre or not email or not password:
        return (
            {'error': 'Todos los campos son requeridos.'},
            status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return (
            {'error': 'La contraseña debe tener al menos 6 caracteres.'},
            status.HTTP_400_BAD_REQUEST,
        )

    if Usuario.objects.filter(email=email).exists():
        return (
            {'error': 'Ya existe una cuenta con este correo electrónico.'},
            status.HTTP_400_BAD_REQUEST,
        )

    usuario = Usuario.objects.create(
        nombre=nombre,
        email=email,
        password_hash=make_password(password),
    )
    data = {
        'id': usuario.id,
        'nombre': usuario.nombre,
        'email': usuario.email,
    }
    return data, status.HTTP_201_CREATED


def autenticar_usuario(email, password):
    """Verifica las credenciales de un usuario.

    Args:
        email: Correo electrónico del usuario.
        password: Contraseña en texto plano para comparar con el hash.

    Returns:
        Tupla (data_dict, http_status) lista para construir un Response.
    """
    if not email or not password:
        return (
            {'error': 'Correo y contraseña son requeridos.'},
            status.HTTP_400_BAD_REQUEST,
        )

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Mensaje genérico para no revelar si el email existe en el sistema
        return (
            {'error': 'Correo o contraseña incorrectos.'},
            status.HTTP_401_UNAUTHORIZED,
        )

    if not check_password(password, usuario.password_hash):
        return (
            {'error': 'Correo o contraseña incorrectos.'},
            status.HTTP_401_UNAUTHORIZED,
        )

    data = {
        'id': usuario.id,
        'nombre': usuario.nombre,
        'email': usuario.email,
    }
    return data, status.HTTP_200_OK
