from django.db import models


class Analisis(models.Model):
    TIPO_CHOICES = [
        ('mortalidad', 'Mortalidad Materna'),
        ('morbilidad', 'Morbilidad Materna Extrema'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nombre_archivo = models.CharField(max_length=255)
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

