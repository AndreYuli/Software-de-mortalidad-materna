from rest_framework import serializers
from .models import Analisis


class AnalisisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisis
        fields = ['id', 'tipo', 'nombre_archivo', 'archivo', 'fecha_carga', 'total_registros', 'resumen']
        read_only_fields = ['fecha_carga', 'total_registros', 'resumen']


class UploadSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=['mortalidad', 'morbilidad'])
    archivo = serializers.FileField()
