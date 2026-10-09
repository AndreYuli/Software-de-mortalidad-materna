"""Catálogo de departamentos y secretarías de salud habilitadas en la plataforma.

La secretaría de salud es el criterio de aislamiento de datos (tenant): cada caso,
archivo e importación se etiqueta con el `codigo` de la secretaría con la que se
registró el usuario, y todas las consultas filtran por ese valor. Por eso el `codigo`
debe ser estable y controlado: nunca se toma como texto libre del cliente.
"""

from dataclasses import dataclass

# Antioquia es el único departamento habilitado por ahora; se amplía agregando
# entradas con sus secretarías (cada secretaría necesita un `codigo` único global).


@dataclass(frozen=True)
class Secretaria:
    codigo: str
    nombre: str


@dataclass(frozen=True)
class Departamento:
    codigo: str
    nombre: str
    secretarias: tuple[Secretaria, ...]


DEPARTAMENTOS: tuple[Departamento, ...] = (
    Departamento(
        codigo='antioquia',
        nombre='Antioquia',
        secretarias=(
            Secretaria(codigo='bello', nombre='Secretaría de Salud de Bello'),
            Secretaria(codigo='envigado',
                       nombre='Secretaría de Salud de Envigado'),
            Secretaria(codigo='itagui',
                       nombre='Secretaría de Salud de Itagüí'),
        ),
    ),
)

# Índice global código de secretaría -> (departamento, secretaría) para validación O(1).
_POR_CODIGO_SECRETARIA: dict[str, tuple[Departamento, Secretaria]] = {
    sec.codigo: (dep, sec)
    for dep in DEPARTAMENTOS
    for sec in dep.secretarias
}


def resolver_secretaria(departamento_codigo: str, secretaria_codigo: str) -> tuple[str, str, str]:
    """Valida el par departamento/secretaría contra el catálogo.

    Args:
        departamento_codigo: Código del departamento elegido (ej. 'antioquia').
        secretaria_codigo: Código de la secretaría elegida (ej. 'bello').

    Returns:
        Tupla (nombre_departamento, nombre_secretaria, codigo_secretaria).

    Raises:
        ValueError: Si la secretaría no existe o no pertenece al departamento.
    """
    entrada = _POR_CODIGO_SECRETARIA.get(secretaria_codigo)
    if entrada is None:
        raise ValueError('La secretaría de salud seleccionada no es válida.')
    departamento, secretaria = entrada
    if departamento.codigo != departamento_codigo:
        raise ValueError(
            'La secretaría seleccionada no pertenece al departamento indicado.')
    return departamento.nombre, secretaria.nombre, secretaria.codigo
