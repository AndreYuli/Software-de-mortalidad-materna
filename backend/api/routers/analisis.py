"""Endpoints para carga, consulta y análisis estadístico de archivos Excel."""

from contextlib import contextmanager
from typing import Any, Generator, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.database import get_db
from db.models_sqlalchemy import Analisis
from schemas.analisis_schema import AnalisisResponse, CargaUpdate, ChatRequest, ClusteringRequest
from services import analisis_service, narrativa_service
from services.ia_client import IAServiceUnavailableError, chatear_ia

router = APIRouter(prefix='/api', tags=['analisis'], dependencies=[Depends(get_current_user)])


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
            detail='Análisis no encontrado.',
        )
    return analisis


@router.post('/analisis/', status_code=status.HTTP_201_CREATED)
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


@router.get('/analisis/', response_model=list[AnalisisResponse])
def listar_analisis(db: Session = Depends(get_db)) -> list[AnalisisResponse]:
    """Lista el análisis más reciente de cada tipo (mortalidad y morbilidad).

    Args:
        db: Sesión de base de datos inyectada.

    Returns:
        Lista de análisis únicos ordenados por fecha de carga descendente.
    """
    lista_analisis = analisis_service.listar_unicos(db=db)
    return lista_analisis


@router.get('/analisis/historial/')
def historial_analisis(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
    tipo: Literal['mortalidad', 'morbilidad'] | None = Query(default=None),
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    week: int | None = Query(default=None, ge=1, le=53),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Lista el historial de cargas paginado, con búsqueda y filtros.

    Args:
        page: Número de página (1-indexed).
        per_page: Registros por página.
        q: Texto a buscar en el nombre del archivo, el tipo o el código del evento (549/550).
        tipo: Filtra por 'mortalidad' o 'morbilidad'.
        year: Filtra por año de la carga.
        month: Filtra por mes de la carga (1-12).
        week: Filtra por semana ISO de la carga.
        db: Sesión de base de datos inyectada.

    Returns:
        Dict con 'items' (cada uno con anio, mes y semana de la carga), 'total' (que cumple
        los filtros), 'page', 'per_page', 'total_pages' y 'anios_disponibles'.
    """
    items, total = analisis_service.listar_historial(
        db=db, page=page, per_page=per_page, q=q, tipo=tipo, year=year, month=month, week=week
    )
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    respuesta_items = []
    for a in items:
        anio, mes, semana = analisis_service.periodo_de_carga(a.fecha_carga)
        respuesta_items.append(
            {
                'id': a.id,
                'tipo': a.tipo,
                'nombre_archivo': a.nombre_archivo,
                'archivo': a.archivo,
                'fecha_carga': a.fecha_carga.isoformat(),
                'anio': anio,
                'mes': mes,
                'semana': semana,
                'total_registros': a.total_registros,
                'resumen': a.resumen,
            }
        )
    return {
        'items': respuesta_items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'anios_disponibles': analisis_service.anios_historial(db),
    }


@router.patch('/analisis/{pk}/', response_model=AnalisisResponse)
def actualizar_analisis(
    pk: int, datos: CargaUpdate, db: Session = Depends(get_db)
) -> AnalisisResponse:
    """Corrige el nombre de archivo y/o la fecha de una carga del historial.

    Args:
        pk: ID de la carga.
        datos: Campos a modificar.
        db: Sesión de base de datos inyectada.

    Returns:
        La carga actualizada.
    """
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        actualizado = analisis_service.actualizar_carga(
            db, analisis, nombre_archivo=datos.nombre_archivo, fecha_carga=datos.fecha_carga
        )
    return AnalisisResponse.model_validate(actualizado)


@router.delete('/analisis/{pk}/', status_code=status.HTTP_204_NO_CONTENT)
def eliminar_analisis(pk: int, db: Session = Depends(get_db)) -> None:
    """Elimina una carga del historial junto con sus narrativas de IA."""
    analisis = _get_analisis_or_404(pk, db)
    analisis_service.eliminar_carga(db, analisis)


@router.get('/analisis/{pk}/', response_model=AnalisisResponse)
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


@router.get('/analisis/{pk}/completo/')
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


@router.post('/analisis/{pk}/clustering/')
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


@router.get('/analisis/{pk}/heatmap/')
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
    if analisis.tipo != 'morbilidad':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='El heatmap solo está disponible para análisis de morbilidad.',
        )
    with _errores_servicio():
        resultado = analisis_service.calcular_heatmap(analisis=analisis, db=db)
    return resultado


@router.get('/analisis/{pk}/extra-columna/')
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
    if analisis.tipo != 'mortalidad':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Extra columna solo está disponible para análisis de mortalidad.',
        )
    with _errores_servicio():
        resultado = analisis_service.calcular_extra_columna(analisis=analisis, columna_idx=0, db=db)
    return resultado


@router.get('/analisis/{pk}/cruce/')
def cruce_variables(
    pk: int,
    var_socio: str = Query(
        ...,
        description='Variable sociodemográfica: zona_residencia, poblacion_vulnerable, etnia, '
        'tipo_afiliacion',
    ),
    var_clinica: str = Query(..., description='Variable clínica (depende del tipo de análisis)'),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Cruza una variable sociodemográfica con una clínica, devolviendo conteos.

    Args:
        pk: ID del análisis.
        var_socio: Clave de la variable sociodemográfica.
        var_clinica: Clave de la variable clínica.
        db: Sesión de base de datos inyectada.

    Returns:
        Dict con categorias_socio, categorias_clinica, matriz de conteos, total.

    Raises:
        HTTPException: 404 si el análisis no existe.
        HTTPException: 422 si las variables no son válidas.
        HTTPException: 500 si ocurre un error al procesar.
    """
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        resultado = analisis_service.calcular_cruce(
            analisis=analisis,
            var_socio=var_socio,
            var_clinica=var_clinica,
            db=db,
        )
    return resultado


@router.get('/analisis/{pk}/narrativa/{tipo_narrativa}/')
def obtener_narrativa_ia(
    pk: int,
    tipo_narrativa: str,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    tipo_clustering: str = Query(default='kmeans'),
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
    filtros: dict[str, Any] = {'year': year, 'month': month}

    with _errores_servicio():
        if tipo_narrativa == 'clustering':
            filtros.update({'tipo_clustering': tipo_clustering, 'n_clusters': n_clusters})
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


@router.post('/analisis/{pk}/chat/')
def chat_analisis(
    pk: int,
    req: ChatRequest,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Envía una pregunta al chatbot de IA sobre los datos del análisis.

    Args:
        pk: ID del análisis.
        req: Pregunta y el historial de chat.
        year: Año para filtrar los datos (opcional).
        month: Mes para filtrar los datos (opcional).
        db: Sesión de BD inyectada.

    Returns:
        Diccionario con la respuesta y el modelo utilizado.

    Raises:
        HTTPException: 503 si el servicio de IA no responde.
    """
    analisis = _get_analisis_or_404(pk, db)
    with _errores_servicio():
        analisis_completo = analisis_service.calcular_completo(analisis, year, month, db)

        # Subconjunto de datos agregados para el contexto del chatbot
        claves_contexto = [
            'estadisticas_basicas',
            'distribucion_mensual',
            'demoras',
            'causas_cie10',
            'criterios_inclusion',
            'distribucion_sociodemografica',
            'obstetrico_edad',
            'distribucion_edad_riesgo',
        ]
        contexto = {k: analisis_completo[k] for k in claves_contexto if k in analisis_completo}

        historial_dicts = [{'rol': h.rol, 'contenido': h.contenido} for h in req.historial]

        try:
            return chatear_ia(req.pregunta, historial_dicts, analisis.tipo, contexto)
        except IAServiceUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
