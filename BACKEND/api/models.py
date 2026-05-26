from django.db import models


class Analisis(models.Model):
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

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.nombre_archivo} ({self.fecha_carga:%d/%m/%Y})'


class SivigilaImportacion(models.Model):
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

