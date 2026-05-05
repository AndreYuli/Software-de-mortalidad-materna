import openpyxl
import pandas as pd
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Analisis
from .serializers import AnalisisSerializer, UploadSerializer
from .processors import (
    MortalidadProcessor, 
    MorbilidadProcessor,
    procesar_archivo_analisis
)

# Columnas requeridas por tipo de evento
COLUMNAS_MORTALIDAD = [
    'A. Nombres y Apellidos', 'B. Tipo ID', 'C. Número ID',
    '5.1 Sitio de Defunción', '6.1 Convivencia', '6.3 Escolaridad',
    '6.4 Regulación Fecundidad', '6.5 Gestaciones', '6.6 Partos Vaginales',
    '6.7 Cesáreas', '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
    '8.1 No. CPN', '8.2 Semana inicio CPN', '9.1 Momento de la muerte',
    '9.2 Semana gestación', '9.4 Tipo de parto', '10.1 Causa básica CIE-10',
    '10.3.1 Demora 1', '10.3.2 Demora 2', '10.3.3 Demora 3', '10.3.4 Demora 4',
]

COLUMNAS_MORBILIDAD = [
    'Nombres y apellidos', 'Tipo de ID', 'N° identificación',
    'N° gestaciones', 'Partos vaginales', 'Cesáreas', 'Abortos',
    'N° controles prenatales', 'Semanas inicio CPN',
    'Edad gestacional ocurrencia (sem)', 'Momento ocurrencia',
    'Eclampsia', 'Sepsis sistémica severa', 'Hemorragia obstétrica severa',
    'Preeclampsia', 'Ruptura uterina', 'Ingreso UCI', 'Cirugía adicional',
    'Transfusión', 'Total criterios', 'Causa principal CIE-10',
    'Días estancia hospitalaria', 'Días estancia UCI',
]

COLUMNAS_REQUERIDAS = {
    'mortalidad': COLUMNAS_MORTALIDAD,
    'morbilidad': COLUMNAS_MORBILIDAD,
}


def leer_columnas_excel(archivo):
    """Lee la primera fila del archivo Excel y retorna la lista de columnas."""
    try:
        wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        ws = wb.active
        headers = [str(cell.value).strip() for cell in next(ws.iter_rows(min_row=1, max_row=1)) if cell.value is not None]
        wb.close()
        return headers
    except Exception:
        return None


def calcular_resumen(archivo, tipo):
    """Lee el archivo Excel y calcula estadísticas básicas usando pandas."""
    try:
        df = pd.read_excel(archivo, engine='openpyxl')
        resumen = {
            'total_registros': len(df),
        }

        if tipo == 'mortalidad':
            if '9.1 Momento de la muerte' in df.columns:
                resumen['distribucion_momento'] = (
                    df['9.1 Momento de la muerte'].value_counts().to_dict()
                )
            if '10.1 Causa básica CIE-10' in df.columns:
                top5 = df['10.1 Causa básica CIE-10'].value_counts().head(5).to_dict()
                resumen['top5_causas'] = {str(k): int(v) for k, v in top5.items()}

        elif tipo == 'morbilidad':
            criterios_cols = ['Eclampsia', 'Sepsis sistémica severa',
                              'Hemorragia obstétrica severa', 'Preeclampsia', 'Ruptura uterina']
            presentes = [c for c in criterios_cols if c in df.columns]
            if presentes:
                resumen['criterios_frecuencia'] = {
                    c: int(df[c].notna().sum()) for c in presentes
                }

        return resumen
    except Exception:
        return {}


@api_view(['POST'])
@permission_classes([AllowAny])
def subir_archivo(request):
    """
    POST /api/subir/
    Recibe un archivo Excel (mortalidad o morbilidad), valida columnas
    y guarda el análisis en base de datos.
    """
    serializer = UploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tipo = serializer.validated_data['tipo']
    archivo = serializer.validated_data['archivo']

    # Validar columnas
    columnas_archivo = leer_columnas_excel(archivo)
    if columnas_archivo is None:
        return Response(
            {'error': 'No se pudo leer el archivo. Verifica que sea un Excel válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    requeridas = COLUMNAS_REQUERIDAS[tipo]
    archivo_lower = [c.lower() for c in columnas_archivo]
    faltantes = [c for c in requeridas if c.lower() not in archivo_lower]

    if faltantes:
        return Response(
            {'error': 'Faltan columnas requeridas.', 'columnas_faltantes': faltantes},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Calcular resumen
    archivo.seek(0)
    resumen = calcular_resumen(archivo, tipo)
    total_registros = resumen.pop('total_registros', 0)

    # Guardar en base de datos
    archivo.seek(0)
    analisis = Analisis.objects.create(
        tipo=tipo,
        nombre_archivo=archivo.name,
        archivo=archivo,
        total_registros=total_registros,
        resumen=resumen,
    )

    return Response(AnalisisSerializer(analisis).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def listar_analisis(request):
    """
    GET /api/analisis/
    Retorna todos los análisis guardados (sin el archivo).
    
    POST /api/analisis/
    Recibe un archivo Excel (mortalidad o morbilidad), valida columnas
    y guarda el análisis en base de datos.
    """
    if request.method == 'GET':
        analisis = Analisis.objects.all()
        serializer = AnalisisSerializer(analisis, many=True)
        return Response(serializer.data)
    
    # POST - Crear nuevo análisis
    serializer = UploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tipo = serializer.validated_data['tipo']
    archivo = serializer.validated_data['archivo']

    # Validar columnas
    columnas_archivo = leer_columnas_excel(archivo)
    if columnas_archivo is None:
        return Response(
            {'error': 'No se pudo leer el archivo. Verifica que sea un Excel válido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    requeridas = COLUMNAS_REQUERIDAS[tipo]
    archivo_lower = [c.lower() for c in columnas_archivo]
    faltantes = [c for c in requeridas if c.lower() not in archivo_lower]

    if faltantes:
        return Response(
            {'error': 'Faltan columnas requeridas.', 'columnas_faltantes': faltantes},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Calcular resumen
    archivo.seek(0)
    resumen = calcular_resumen(archivo, tipo)
    total_registros = resumen.pop('total_registros', 0)

    # Guardar en base de datos
    archivo.seek(0)
    analisis = Analisis.objects.create(
        tipo=tipo,
        nombre_archivo=archivo.name,
        archivo=archivo,
        total_registros=total_registros,
        resumen=resumen,
    )

    return Response(AnalisisSerializer(analisis).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def detalle_analisis(request, pk):
    """
    GET /api/analisis/<id>/
    Retorna el detalle de un análisis específico.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': 'Análisis no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(AnalisisSerializer(analisis).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def analisis_completo(request, pk):
    """
    GET /api/analisis/<id>/completo/
    Genera análisis completo con estadísticas, clustering y visualizaciones.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': 'Análisis no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    # Leer archivo y procesar
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        
        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            resultado = {
                'tipo': 'mortalidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'momento_muerte': processor.analizar_momento_muerte(),
                'demoras': processor.analizar_demoras(),
                'causas_cie10': processor.analizar_causas_cie10(top_n=15),
            }
        else:  # morbilidad
            processor = MorbilidadProcessor(df)
            resultado = {
                'tipo': 'morbilidad',
                'id': analisis.id,
                'nombre_archivo': analisis.nombre_archivo,
                'fecha_carga': analisis.fecha_carga,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'criterios_inclusion': processor.analizar_criterios_inclusion(),
                'momento_ocurrencia': processor.analizar_momento_ocurrencia(),
            }
        
        return Response(resultado)
    
    except Exception as e:
        return Response(
            {'error': f'Error al procesar el análisis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def clustering_analisis(request, pk):
    """
    POST /api/analisis/<id>/clustering/
    Realiza análisis de clustering sobre los datos.
    
    Body:
        {
            "tipo_clustering": "kmeans" | "jerarquico",
            "n_clusters": 3  (opcional, default 3)
        }
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': 'Análisis no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    tipo_clustering = request.data.get('tipo_clustering', 'kmeans')
    n_clusters = request.data.get('n_clusters', 3)
    
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        
        if analisis.tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            
            if tipo_clustering == 'jerarquico':
                resultado = processor.clustering_jerarquico()
            else:  # kmeans por defecto
                resultado = processor.clustering_factores_riesgo(n_clusters=n_clusters)
        
        else:  # morbilidad
            processor = MorbilidadProcessor(df)
            resultado = processor.clustering_perfiles_morbilidad(n_clusters=n_clusters)
        
        resultado['analisis_id'] = analisis.id
        resultado['tipo_analisis'] = analisis.tipo
        resultado['tipo_clustering'] = tipo_clustering
        
        return Response(resultado)
    
    except Exception as e:
        return Response(
            {'error': f'Error en clustering: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_correlacion(request, pk):
    """
    GET /api/analisis/<id>/heatmap/
    Genera matriz de correlación para heatmap.
    Solo disponible para morbilidad.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': 'Análisis no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    
    if analisis.tipo != 'morbilidad':
        return Response(
            {'error': 'Heatmap solo disponible para análisis de morbilidad'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl')
        processor = MorbilidadProcessor(df)
        resultado = processor.heatmap_correlacion()
        
        resultado['analisis_id'] = analisis.id
        
        return Response(resultado)
    
    except Exception as e:
        return Response(
            {'error': f'Error al generar heatmap: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


