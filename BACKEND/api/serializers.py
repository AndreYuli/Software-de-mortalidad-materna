"""Serializadores DRF para los modelos de la API.

Convierten instancias de modelo a/desde representaciones JSON
para los endpoints de la API REST.
"""
from rest_framework import serializers

from .models import Analisis, Paciente, VMorbilidadCompleta, VMortalidadCompleta


class AnalisisSerializer(serializers.ModelSerializer):
    """Serializa el modelo Analisis para listado y detalle."""

    class Meta:
        model = Analisis
        fields = [
            'id', 'tipo', 'nombre_archivo', 'archivo',
            'fecha_carga', 'total_registros', 'resumen',
        ]
        read_only_fields = ['fecha_carga', 'total_registros', 'resumen']


class UploadSerializer(serializers.Serializer):
    """Valida los campos del formulario de carga de archivos Excel."""

    tipo = serializers.ChoiceField(choices=['mortalidad', 'morbilidad'])
    archivo = serializers.FileField()


class PacienteSerializer(serializers.ModelSerializer):
    """Serializa pacientes SIVIGILA con datos de tipo de identificación."""

    tipo_identificacion = serializers.CharField(
        source='id_tipo.codigo', read_only=True,
    )
    descripcion_tipo_identificacion = serializers.CharField(
        source='id_tipo.descripcion', read_only=True,
    )

    class Meta:
        model = Paciente
        fields = [
            'id_paciente',
            'nombres_apellidos',
            'tipo_identificacion',
            'descripcion_tipo_identificacion',
            'numero_id',
            'fecha_nacimiento',
            'creado_en',
        ]


class MorbilidadCompletaSerializer(serializers.ModelSerializer):
    """Serializa la vista completa de morbilidad materna extrema."""

    class Meta:
        model = VMorbilidadCompleta
        fields = '__all__'


class MortalidadCompletaSerializer(serializers.ModelSerializer):
    """Serializa la vista completa de mortalidad materna."""

    class Meta:
        model = VMortalidadCompleta
        fields = '__all__'
