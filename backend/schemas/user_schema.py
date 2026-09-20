"""Schemas Pydantic para registro, login y respuesta de usuarios."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UsuarioRegister(BaseModel):
    """Datos requeridos para registrar un usuario nuevo.

    Attributes:
        nombre: Nombre completo del usuario.
        email: Correo electrónico único, normalizado a minúsculas.
        password: Contraseña en texto plano (mínimo 6 caracteres).
    """

    nombre: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator('nombre', mode='before')
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        """Elimina espacios al inicio y al final del nombre."""
        return v.strip()

    @field_validator('email', mode='before')
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Normaliza el email a minúsculas y elimina espacios."""
        return v.strip().lower()


class UsuarioLogin(BaseModel):
    """Credenciales para iniciar sesión.

    Attributes:
        email: Correo electrónico del usuario, normalizado a minúsculas.
        password: Contraseña en texto plano.
    """

    email: EmailStr
    password: str

    @field_validator('email', mode='before')
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Normaliza el email a minúsculas y elimina espacios."""
        return v.strip().lower()


class UsuarioResponse(BaseModel):
    """Datos del usuario devueltos por la API (sin contraseña).

    Attributes:
        id: Identificador del usuario.
        nombre: Nombre completo.
        email: Correo electrónico.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str


class TokenResponse(BaseModel):
    """Token JWT devuelto tras un login exitoso.

    Attributes:
        access_token: Token JWT firmado.
        token_type: Tipo de token (siempre 'bearer').
        id: Identificador del usuario.
        nombre: Nombre completo del usuario.
        email: Correo electrónico del usuario.
    """

    access_token: str
    token_type: str = 'bearer'
    id: int
    nombre: str
    email: str
