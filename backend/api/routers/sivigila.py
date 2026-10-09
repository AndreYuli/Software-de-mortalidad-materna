"""Endpoints para consulta de datos SIVIGILA: pacientes, morbilidad y mortalidad."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import (
    CasoMorbilidad,
    CasoMortalidad,
    CatTipoId,
    Paciente,
    Usuario,
    VMorbilidadCompleta,
    VMortalidadCompleta,
)
from schemas.sivigila_schema import PacienteResponse, VMorbilidadResponse, VMortalidadResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/sivigila', tags=['sivigila'], dependencies=[Depends(get_current_user)]
)

_LIMITE_DEFAULT = 100
_LIMITE_MAXIMO = 500


def _obtener_limite(limit: int | None) -> int:
    """Normaliza el parámetro limit dentro del rango permitido.

    Args:
        limit: Valor solicitado por el cliente, puede ser None.

    Returns:
        Límite válido entre 1 y _LIMITE_MAXIMO.
    """
    resultado: int
    if limit is None:
        resultado = _LIMITE_DEFAULT
    else:
        resultado = max(1, min(limit, _LIMITE_MAXIMO))
    return resultado


def _filtro_pacientes_de_secretaria(secretaria_codigo: str | None):
    """Condición que limita un query de Paciente a los que tienen algún caso de la secretaría.

    El paciente es una identidad compartida, pero solo es visible para una secretaría si
    tiene al menos un caso (morbilidad o mortalidad) de esa secretaría.
    """
    morbilidad = select(CasoMorbilidad.id_paciente).where(
        CasoMorbilidad.secretaria_codigo == secretaria_codigo
    )
    mortalidad = select(CasoMortalidad.id_paciente).where(
        CasoMortalidad.secretaria_codigo == secretaria_codigo
    )
    return or_(Paciente.id_paciente.in_(morbilidad), Paciente.id_paciente.in_(mortalidad))


@router.get('/resumen/')
def resumen(
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
) -> dict[str, int]:
    """Devuelve el conteo de pacientes y casos de la secretaría del usuario.

    Args:
        db: Sesión de base de datos inyectada.
        usuario: Usuario autenticado; su secretaría acota los conteos.

    Returns:
        Diccionario con los tres conteos.
    """
    sc = usuario.secretaria_codigo
    conteos: dict[str, int] = {
        'pacientes': (
            db.query(Paciente).filter(
                _filtro_pacientes_de_secretaria(sc)).count()
        ),
        'casos_morbilidad': db.query(CasoMorbilidad).filter(
            CasoMorbilidad.secretaria_codigo == sc
        ).count(),
        'casos_mortalidad': db.query(CasoMortalidad).filter(
            CasoMortalidad.secretaria_codigo == sc
        ).count(),
    }
    return conteos


@router.get('/pacientes/', response_model=list[PacienteResponse])
def listar_pacientes(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[PacienteResponse]:
    """Lista pacientes con su tipo de identificación.

    Args:
        skip: Número de registros a omitir para paginación.
        limit: Máximo de registros a devolver (por defecto 100, máximo 500).
        db: Sesión de base de datos inyectada.
        usuario: Usuario autenticado; su secretaría acota los pacientes visibles.

    Returns:
        Lista paginada de pacientes con datos de identificación.
    """
    limite = _obtener_limite(limit)
    resultados = (
        db.query(Paciente, CatTipoId)
        .outerjoin(CatTipoId, Paciente.id_tipo_id == CatTipoId.id)
        .filter(_filtro_pacientes_de_secretaria(usuario.secretaria_codigo))
        .order_by(Paciente.id_paciente)
        .offset(skip)
        .limit(limite)
        .all()
    )
    lista_pacientes = [
        PacienteResponse(
            id_paciente=p.id_paciente,
            nombres_apellidos=p.nombres_apellidos,
            tipo_identificacion=t.codigo if t else None,
            descripcion_tipo_identificacion=t.descripcion if t else None,
            numero_id=p.numero_id,
            fecha_nacimiento=p.fecha_nacimiento,
            creado_en=p.creado_en,
        )
        for p, t in resultados
    ]
    return lista_pacientes


@router.get('/morbilidad/', response_model=list[VMorbilidadResponse])
def listar_morbilidad(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[VMorbilidadResponse]:
    """Lista casos de morbilidad materna extrema desde la vista consolidada.

    Args:
        skip: Número de registros a omitir para paginación.
        limit: Máximo de registros a devolver (por defecto 100, máximo 500).
        db: Sesión de base de datos inyectada.

    Returns:
        Lista paginada de casos de morbilidad con todos sus campos.

    Raises:
        HTTPException: 500 si la vista no existe en la base de datos.
    """
    limite = _obtener_limite(limit)
    try:
        casos = (
            db.query(VMorbilidadCompleta)
            .filter(VMorbilidadCompleta.secretaria_codigo == usuario.secretaria_codigo)
            .order_by(VMorbilidadCompleta.id_caso)
            .offset(skip)
            .limit(limite)
            .all()
        )
        lista_morbilidad: list[VMorbilidadResponse] = [
            VMorbilidadResponse.model_validate(caso) for caso in casos
        ]
    except Exception as exc:
        logger.exception('Error al consultar la vista de morbilidad completa.')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error interno al consultar los registros de morbilidad.',
        ) from exc
    return lista_morbilidad


@router.get('/mortalidad/', response_model=list[VMortalidadResponse])
def listar_mortalidad(
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[VMortalidadResponse]:
    """Lista casos de mortalidad materna desde la vista consolidada.

    Args:
        skip: Número de registros a omitir para paginación.
        limit: Máximo de registros a devolver (por defecto 100, máximo 500).
        db: Sesión de base de datos inyectada.

    Returns:
        Lista paginada de casos de mortalidad con todos sus campos.

    Raises:
        HTTPException: 500 si la vista no existe en la base de datos.
    """
    limite = _obtener_limite(limit)
    try:
        casos = (
            db.query(VMortalidadCompleta)
            .filter(VMortalidadCompleta.secretaria_codigo == usuario.secretaria_codigo)
            .order_by(VMortalidadCompleta.id_caso)
            .offset(skip)
            .limit(limite)
            .all()
        )
        lista_mortalidad: list[VMortalidadResponse] = [
            VMortalidadResponse.model_validate(caso) for caso in casos
        ]
    except Exception as exc:
        logger.exception('Error al consultar la vista de mortalidad completa.')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Error interno al consultar los registros de mortalidad.',
        ) from exc
    return lista_mortalidad
