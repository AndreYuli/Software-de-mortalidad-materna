"""Schemas Pydantic para registro, login y respuesta de usuarios."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CLAVES_COMUNES = frozenset(
    {
        '12345678',
        '123456789',
        '1234567890',
        '87654321',
        'password',
        'password1',
        'contraseña',
        'qwertyui',
        'qwerty123',
        'abcd1234',
        'abc12345',
        'iloveyou',
        'admin123',
        'colombia',
        'bienvenido',
        '11111111',
        '00000000',
        '12341234',
    }
)


class UsuarioRegister(BaseModel):
    """Datos requeridos para registrar un usuario nuevo.

    Attributes:
        nombre: Nombre completo del usuario (máximo 150 caracteres).
        email: Correo electrónico único, normalizado a minúsculas.
        password: Contraseña en texto plano (8 a 128 caracteres, sin claves comunes).
        departamento_codigo: Código del departamento (ej. 'antioquia').
        secretaria_codigo: Código de la secretaría de salud (ej. 'bello'); define el
            tenant con el que se aíslan los datos del usuario.
    """

    nombre: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    departamento_codigo: str = Field(..., min_length=1)
    secretaria_codigo: str = Field(..., min_length=1)

    @field_validator('nombre', mode='before')
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        """Elimina espacios al inicio y al final del nombre."""
        return v.strip()

    @field_validator('nombre')
    @classmethod
    def nombre_sin_marcado(cls, v: str) -> str:
        """Rechaza `<` y `>` en el nombre: no es un nombre válido y evita HTML guardado."""
        if '<' in v or '>' in v:
            raise ValueError('El nombre no puede contener los caracteres < o >.')
        return v

    @field_validator('password')
    @classmethod
    def password_no_comun(cls, v: str) -> str:
        """Rechaza claves de la lista de comunes o de un solo carácter repetido.

        NIST SP 800-63B-4, sección 3.1.1.2: la contraseña usada como único factor debe tener al
        menos 15 caracteres (8 sólo si es parte de autenticación multifactor, que esta app no
        tiene), se debe permitir un máximo de al menos 64 y se debe comparar contra una lista de
        contraseñas comunes o comprometidas, sin imponer otras reglas de composición. Decisión
        del equipo: mínimo 8 y máximo 128, por debajo del mínimo de la norma para un solo factor
        (limitación declarada). La lista de comunes es corta y de ejemplo (ampliar con una lista
        pública como la de contraseñas filtradas si se necesita más).
        """
        if v.lower() in CLAVES_COMUNES or len(set(v)) == 1:
            raise ValueError('La contraseña es demasiado común; elige otra.')
        return v

    @field_validator('departamento_codigo', 'secretaria_codigo', mode='before')
    @classmethod
    def normalizar_codigo(cls, v: str) -> str:
        """Normaliza un código de afiliación a minúsculas sin espacios extremos."""
        return v.strip().lower()

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
    departamento: str | None = None
    secretaria: str | None = None
    secretaria_codigo: str | None = None


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
    departamento: str | None = None
    secretaria: str | None = None
    secretaria_codigo: str | None = None
