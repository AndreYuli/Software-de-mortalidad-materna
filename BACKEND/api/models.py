"""Modelos de persistencia para análisis e importaciones SIVIGILA.

Define los modelos principales usados por la API para almacenar
análisis, historial de importaciones y usuarios del sistema.
"""
from django.db import models


class Analisis(models.Model):
    """Representa un análisis cargado desde un archivo Excel SIVIGILA.

    Attributes:
        tipo: Tipo de análisis ('mortalidad' o 'morbilidad').
        nombre_archivo: Nombre del archivo cargado por el usuario.
        archivo_hash: SHA-256 del archivo para trazabilidad.
        archivo: Archivo físico almacenado en media.
        fecha_carga: Fecha y hora de carga (auto).
        total_registros: Cantidad de registros procesados.
        resumen: Metadatos de resumen en formato JSON.
    """

    TIPO_CHOICES = [
        ('mortalidad', 'Mortalidad Materna'),
        ('morbilidad', 'Morbilidad Materna Extrema'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre_archivo = models.CharField(max_length=255)
    archivo_hash = models.CharField(max_length=64, blank=True, db_index=True)
    archivo = models.FileField(upload_to='uploads/%Y/%m/')
    fecha_carga = models.DateTimeField(auto_now_add=True)
    total_registros = models.PositiveIntegerField(default=0)
    resumen = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-fecha_carga']
        verbose_name = 'Análisis'
        verbose_name_plural = 'Análisis'

    def save(self, *args, **kwargs):
        """Invalida el caché de análisis al guardar cualquier cambio.

        Se usa LocMemCache para cachear los resultados procesados;
        al actualizar un análisis los resultados previos quedan obsoletos.
        """
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.clear()

    def __str__(self):
        """Retorna una representación legible del análisis."""
        return (
            f'{self.get_tipo_display()} — '
            f'{self.nombre_archivo} ({self.fecha_carga:%d/%m/%Y})'
        )


class SivigilaImportacion(models.Model):
    """Registra eventos de importación procesados desde SIVIGILA.

    Cada fila del Excel importado genera un registro aquí para
    deduplicación basada en hash y para trazabilidad de la carga.

    Attributes:
        tipo: Tipo de evento importado ('mortalidad' o 'morbilidad').
        row_hash: Hash único de la fila para deduplicación.
        event_hash: Hash del evento para agrupación y consulta.
        caso_id: Identificador interno del caso.
        numero_id: Número de identificación de la persona.
        tipo_identificacion: Tipo de documento de identificación.
        creado_en: Fecha y hora de creación del registro (auto).
    """

    tipo = models.CharField(max_length=20)
    row_hash = models.CharField(max_length=64, unique=True)
    event_hash = models.CharField(max_length=64, db_index=True)
    caso_id = models.PositiveIntegerField()
    numero_id = models.CharField(max_length=30)
    tipo_identificacion = models.CharField(max_length=5)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Importación SIVIGILA'
        verbose_name_plural = 'Importaciones SIVIGILA'


class Usuario(models.Model):
    """Almacena usuarios del sistema con contraseña en hash Django.

    Attributes:
        nombre: Nombre completo del usuario.
        email: Correo electrónico único del usuario.
        password_hash: Hash de la contraseña (make_password de Django).
        fecha_registro: Fecha y hora de registro (auto).
    """

    nombre = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        """Retorna una representación legible del usuario."""
        return f'{self.nombre} <{self.email}>'


from .sivigila_models import (  # noqa: E402
    AntecedenteMaterno,
    AntecedentePartoPuerperio,
    AntecedenteRiesgo,
    AntecedentesObstetricos,
    CasoMorbilidad,
    CasoMortalidad,
    CatConvivencia,
    CatEscolaridad,
    CatFuenteCausaMuerte,
    CatGrupoCausa,
    CatMomentoMuerte,
    CatNivelAtencion,
    CatPersonalSalud,
    CatRegulacionFecundidad,
    CatRemisiones,
    CatSitioDefuncion,
    CatTerminacionGestacion,
    CatTipoId,
    CatTipoParto,
    CausaMuerte,
    CausasMorbilidad,
    ComplicacionEmbarazo,
    ControlPrenatal,
    CriteriosEnfermedad,
    CriteriosFallaOrganica,
    CriteriosManejo,
    ManejoHospitalario,
    Paciente,
    Referencia,
    VMorbilidadCompleta,
    VMortalidadCompleta,
)
