"""Vistas HTTP de la API de mortalidad y morbilidad materna.

Cada vista parsea el request, delega la lógica de negocio al servicio
correspondiente y retorna el Response. No contiene lógica de dominio.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    Analisis,
    CasoMorbilidad,
    CasoMortalidad,
    Paciente,
    VMorbilidadCompleta,
    VMortalidadCompleta,
)
from .serializers import (
    AnalisisSerializer,
    MorbilidadCompletaSerializer,
    MortalidadCompletaSerializer,
    PacienteSerializer,
)
from .services import analisis_service, auth_service, upload_service

ERROR_ANALISIS_NO_ENCONTRADO = 'Análisis no encontrado.'


def _obtener_limite(request, default=100, maximo=500):
    """Extrae y valida el parámetro 'limit' de la query string.

    Args:
        request: Request de DRF.
        default: Valor por defecto si el parámetro no está presente.
        maximo: Límite máximo permitido para evitar consultas sin cota.

    Returns:
        Entero entre 1 y maximo.
    """
    try:
        limite = int(request.query_params.get('limit', default))
    except (TypeError, ValueError):
        limite = default
    return max(1, min(limite, maximo))


def _obtener_analisis_unicos(lista):
    """Retorna solo el análisis más reciente por tipo de evento.

    Garantiza que la lista de la UI muestre un único registro por tipo
    (mortalidad / morbilidad), aunque exista historial de cargas.

    Args:
        lista: QuerySet o iterable de instancias Analisis.

    Returns:
        Lista de instancias Analisis ordenada por fecha descendente.
    """
    unicos = {}
    for analisis in lista:
        clave = analisis.tipo
        existente = unicos.get(clave)
        if existente is None or analisis.fecha_carga > existente.fecha_carga:
            unicos[clave] = analisis
    return sorted(unicos.values(), key=lambda a: a.fecha_carga, reverse=True)


# ---------------------------------------------------------------------------
# Endpoints de carga y listado de análisis
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def subir_archivo(request):
    """Recibe un Excel SIVIGILA y lo persiste como análisis.

    POST /api/subir/
    """
    data, http_status = upload_service.procesar_carga_archivo(
        request.data, request.FILES,
    )
    return Response(data, status=http_status)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def listar_analisis(request):
    """Lista análisis guardados o sube uno nuevo.

    GET  /api/analisis/ — retorna el análisis más reciente por tipo.
    POST /api/analisis/ — equivalente a POST /api/subir/.
    """
    if request.method == 'GET':
        analisis = _obtener_analisis_unicos(Analisis.objects.all())
        return Response(AnalisisSerializer(analisis, many=True).data)

    data, http_status = upload_service.procesar_carga_archivo(
        request.data, request.FILES,
    )
    return Response(data, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def detalle_analisis(request, pk):
    """Retorna el detalle de un análisis por ID.

    GET /api/analisis/<id>/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(AnalisisSerializer(analisis).data)


# ---------------------------------------------------------------------------
# Endpoints de procesamiento de análisis
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def analisis_completo(request, pk):
    """Retorna estadísticas completas de un análisis con filtros opcionales.

    GET /api/analisis/<id>/completo/?year=2023&month=3
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    year = request.query_params.get('year', '').strip() or None
    month = request.query_params.get('month', '').strip() or None

    resultado, http_status = analisis_service.obtener_analisis_completo(
        analisis, year, month,
    )
    return Response(resultado, status=http_status)


@api_view(['POST'])
@permission_classes([AllowAny])
def clustering_analisis(request, pk):
    """Ejecuta clustering K-means o jerárquico sobre un análisis.

    POST /api/analisis/<id>/clustering/
    Body: {"tipo_clustering": "kmeans"|"jerarquico", "n_clusters": 3}
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    tipo_clustering = request.data.get('tipo_clustering', 'kmeans')
    n_clusters = request.data.get('n_clusters', 3)

    resultado, http_status = analisis_service.obtener_clustering(
        analisis, tipo_clustering, n_clusters,
    )
    return Response(resultado, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_correlacion(request, pk):
    """Genera la matriz de correlación para un análisis de morbilidad.

    GET /api/analisis/<id>/heatmap/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    resultado, http_status = analisis_service.obtener_heatmap(analisis)
    return Response(resultado, status=http_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def extra_columna_analisis(request, pk):
    """Detecta y devuelve datos de columna opcional (edad/municipio/etc.).

    GET /api/analisis/<id>/extra-columna/
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response(
            {'error': ERROR_ANALISIS_NO_ENCONTRADO},
            status=status.HTTP_404_NOT_FOUND,
        )

    resultado, http_status = analisis_service.obtener_extra_columna(analisis)
    return Response(resultado, status=http_status)


# ---------------------------------------------------------------------------
# Endpoints SIVIGILA
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def resumen_sivigila(request):
    """Retorna conteos globales de pacientes y casos SIVIGILA en BD.

    GET /api/sivigila/resumen/
    """
    return Response({
        'pacientes': Paciente.objects.count(),
        'casos_morbilidad': CasoMorbilidad.objects.count(),
        'casos_mortalidad': CasoMortalidad.objects.count(),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_pacientes(request):
    """Lista pacientes con paginación por el parámetro 'limit'.

    GET /api/sivigila/pacientes/?limit=100
    """
    limite = _obtener_limite(request)
    pacientes = (
        Paciente.objects
        .select_related('id_tipo')
        .order_by('id_paciente')[:limite]
    )
    return Response(PacienteSerializer(pacientes, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_morbilidad_sivigila(request):
    """Lista casos de morbilidad con paginación por el parámetro 'limit'.

    GET /api/sivigila/morbilidad/?limit=100
    """
    limite = _obtener_limite(request)
    casos = VMorbilidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MorbilidadCompletaSerializer(casos, many=True).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_mortalidad_sivigila(request):
    """Lista casos de mortalidad con paginación por el parámetro 'limit'.

    GET /api/sivigila/mortalidad/?limit=100
    """
    limite = _obtener_limite(request)
    casos = VMortalidadCompleta.objects.order_by('id_caso')[:limite]
    return Response(MortalidadCompletaSerializer(casos, many=True).data)


# ---------------------------------------------------------------------------
# Endpoints de autenticación
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def register_usuario(request):
    """Registra un nuevo usuario en el sistema.

    POST /api/auth/register/
    Body: {"nombre": "...", "email": "...", "password": "..."}
    """
    data, http_status = auth_service.registrar_usuario(
        nombre=request.data.get('nombre', '').strip(),
        email=request.data.get('email', '').strip().lower(),
        password=request.data.get('password', ''),
    )
    return Response(data, status=http_status)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    """Autentica un usuario y retorna sus datos básicos.

    POST /api/auth/login/
    Body: {"email": "...", "password": "..."}
    """
    data, http_status = auth_service.autenticar_usuario(
        email=request.data.get('email', '').strip().lower(),
        password=request.data.get('password', ''),
    )
    return Response(data, status=http_status)
