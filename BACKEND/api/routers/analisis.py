"""Endpoints para carga, consulta y análisis estadístico de archivos Excel."""

from contextlib import contextmanager
from typing import Any, Generator

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from db.database import get_db
from db.models_sqlalchemy import Analisis
from schemas.analisis_schema import AnalisisResponse, ClusteringRequest
from services import analisis_service, narrativa_service
from services.ia_client import IAServiceUnavailableError

router = APIRouter(prefix="/api", tags=["analisis"])


@contextmanager
def _errores_servicio() -> Generator[None, None, None]:
    """Traduce excepciones de dominio del servicio a respuestas HTTP."""
    try:
        yield
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


def _get_analisis_or_404(pk: int, db: Session) -> Analisis:
    """Busca un análisis por ID o lanza 404.

    Args:
        pk: ID del análisis.
        db: Sesión de base de datos.

    Returns:
        Instancia del análisis encontrado.

    Raises:
        HTTPException: 404 si el análisis no existe.
    """
    analisis = db.get(Analisis, pk)
    if not analisis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis no encontrado.",
        )
    return analisis


@router.post("/analisis/", status_code=status.HTTP_201_CREATED)
def subir_archivo(
    tipo: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Recibe un archivo Excel, lo valida, lo persiste y genera el análisis.

    Args:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').
        archivo: Archivo Excel cargado por el usuario.
        db: Sesión de base de datos inyectada.

    Returns:
        Datos del análisis creado o actualizado, incluyendo resumen SIVIGILA.

    Raises:
        HTTPException: 400 si el archivo no es válido.
        HTTPException: 422 si faltan columnas requeridas.
        HTTPException: 500 si falla la persistencia.
    """
    with _errores_servicio():
        resultado_persistencia = analisis_service.procesar_subida(tipo=tipo, archivo=archivo, db=db)
    return resultado_persistencia


@router.get("/analisis/", response_model=list[AnalisisResponse])
def listar_analisis(db: Session = Depends(get_db)) -> list[AnalisisResponse]:
    """Lista el análisis más reciente de cada tipo (mortalidad y morbilidad).

    Args:
        db: Sesión de base de datos inyectada.

    Returns:
        Lista de análisis únicos ordenados por fecha de carga descendente.
    """
    lista_analisis = analisis_service.listar_unicos(db=db)
    return lista_analisis


@router.get("/analisis/{pk}/", response_model=AnalisisResponse)
def detalle_analisis(pk: int, db: Session = Depends(get_db)) -> AnalisisResponse:
    """Devuelve los metadatos de un análisis específico.

    Args:
        pk: ID del análisis.
        db: Sesión de base de datos inyectada.

    Returns:
        Datos del análisis.

    Raises:
        HTTPException: 404 si no existe.
    """
    analisis_recuperado = _get_analisis_or_404(pk, db)
    return analisis_recuperado


@router.get("/analisis/{pk}/completo/")
def analisis_completo(
    pk: int,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    week: str | None = Query(default=None),
    day: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Devuelve el análisis estadístico completo con filtros opcionales.

    Args:
        pk: ID del análisis.
        year: Año para filtrar los datos (opcional).
        month: Mes para filtrar los datos (opcional).
        week: Semana ISO del año para filtrar los datos (opcional).
        day: Día del mes para filtrar los datos (opcional).
        db: Sesión de base de datos inyectada.

    Returns:
        Diccionario con estadísticas, distribuciones, clustering y metadatos.

    Raises:
        HTTPException: 404 si el análisis no existe.
        HTTPException: 404 si el archivo físico no existe.
        HTTPException: 500 si ocurre un error al procesar.
    """
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        resultado = analisis_service.calcular_completo(
            analisis=analisis,
            year=year,
            month=month,
            db=db,
            week=week,
            day=day,
        )
    return resultado


@router.post("/analisis/{pk}/clustering/")
def clustering(
    pk: int,
    req: ClusteringRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Ejecuta un algoritmo de clustering sobre los datos del análisis.

    Args:
        pk: ID del análisis.
        req: Parámetros del clustering (tipo y número de clusters).
        db: Sesión de base de datos inyectada.

    Returns:
        Resultado del clustering con etiquetas y métricas.

    Raises:
        HTTPException: 404 si el análisis no existe.
        HTTPException: 500 si ocurre un error en el clustering.
    """
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        resultado = analisis_service.ejecutar_clustering(
            analisis=analisis, tipo_clustering=req.tipo_clustering, n_clusters=req.n_clusters, db=db
        )
    return resultado


@router.get("/analisis/{pk}/heatmap/")
def heatmap(pk: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Genera el heatmap de correlación para un análisis de morbilidad.

    Args:
        pk: ID del análisis.
        db: Sesión de base de datos inyectada.

    Returns:
        Datos del heatmap para renderizar en el frontend.

    Raises:
        HTTPException: 400 si el análisis no es de morbilidad.
        HTTPException: 404 si el análisis no existe.
        HTTPException: 500 si ocurre un error al procesar.
    """
    analisis = _get_analisis_or_404(pk, db)
    if analisis.tipo != "morbilidad":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El heatmap solo está disponible para análisis de morbilidad.",
        )
    with _errores_servicio():
        resultado = analisis_service.calcular_heatmap(analisis=analisis, db=db)
    return resultado


@router.get("/analisis/{pk}/extra-columna/")
def extra_columna(pk: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Devuelve la distribución de una columna adicional para mortalidad.

    Args:
        pk: ID del análisis.
        db: Sesión de base de datos inyectada.

    Returns:
        Datos de la gráfica de distribución extra.

    Raises:
        HTTPException: 400 si el análisis no es de mortalidad.
        HTTPException: 404 si el análisis no existe.
        HTTPException: 500 si ocurre un error al procesar.
    """
    analisis = _get_analisis_or_404(pk, db)
    if analisis.tipo != "mortalidad":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Extra columna solo está disponible para análisis de mortalidad.",
        )
    with _errores_servicio():
        resultado = analisis_service.calcular_extra_columna(analisis=analisis, columna_idx=0, db=db)
    return resultado


@router.get("/analisis/{pk}/narrativa/{tipo_narrativa}/")
def obtener_narrativa_ia(
    pk: int,
    tipo_narrativa: str,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    tipo_clustering: str = Query(default="kmeans"),
    n_clusters: int = Query(default=3, ge=2, le=20),
    regenerar: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Obtiene (o genera) la narrativa de IA para un análisis y tipo dados.

    Args:
        pk: ID del análisis.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        year: Año para filtrar (opcional).
        month: Mes para filtrar (opcional).
        tipo_clustering: Algoritmo de clustering, solo relevante si tipo_narrativa='clustering'.
        n_clusters: Número de clusters, solo relevante si tipo_narrativa='clustering'.
        regenerar: Si es True, fuerza una nueva llamada a IA-SERVICE ignorando cache.
        db: Sesión de base de datos.

    Returns:
        Dict con narrativa, modelo, generado_en y desde_cache.

    Raises:
        HTTPException: 404 si el análisis no existe, 503 si IA-SERVICE no está disponible.
    """
    analisis = _get_analisis_or_404(pk, db)
    filtros: dict[str, Any] = {"year": year, "month": month}

    with _errores_servicio():
        if tipo_narrativa == "clustering":
            filtros.update({"tipo_clustering": tipo_clustering, "n_clusters": n_clusters})
            clustering_resultado = analisis_service.ejecutar_clustering(
                analisis,
                tipo_clustering,
                n_clusters,
            )
            indicadores = narrativa_service.extraer_indicadores_para_narrativa(
                tipo_narrativa,
                None,
                clustering_resultado,
            )
        else:
            analisis_completo = analisis_service.calcular_completo(analisis, year, month, db)
            indicadores = narrativa_service.extraer_indicadores_para_narrativa(
                tipo_narrativa,
                analisis_completo,
                None,
            )

        try:
            resultado = narrativa_service.obtener_narrativa(
                db,
                analisis,
                tipo_narrativa,
                indicadores,
                filtros,
                regenerar,
            )
        except IAServiceUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

    return resultado
