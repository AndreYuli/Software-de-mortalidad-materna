"""Schemas Pydantic para análisis, clustering y datos de pacientes."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalisisResponse(BaseModel):
    """Respuesta con los datos de un análisis cargado.

    Attributes:
        id: Identificador del análisis.
        tipo: Tipo de análisis (mortalidad o morbilidad).
        nombre_archivo: Nombre original del archivo cargado.
        archivo: Ruta del archivo almacenado.
        fecha_carga: Fecha y hora de la carga.
        total_registros: Total de registros procesados.
        resumen: Metadatos y estadísticas del proceso.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    nombre_archivo: str
    archivo: str
    fecha_carga: datetime
    total_registros: int
    resumen: dict[str, Any]


class ClusteringRequest(BaseModel):
    """Parámetros para una solicitud de clustering.

    Attributes:
        tipo_clustering: Algoritmo a usar (kmeans por defecto).
        n_clusters: Número de clusters deseados.
    """

    tipo_clustering: str = Field(default="kmeans")
    n_clusters: int = Field(default=3, ge=2, le=20)


class PacienteResponse(BaseModel):
    """Respuesta con los datos de identificación de un paciente.

    Attributes:
        id_paciente: Identificador del paciente.
        nombres_apellidos: Nombre completo.
        tipo_identificacion: Código del tipo de documento.
        descripcion_tipo_identificacion: Descripción del tipo de documento.
        numero_id: Número de documento.
        fecha_nacimiento: Fecha de nacimiento.
        creado_en: Fecha de registro en el sistema.
    """

    model_config = ConfigDict(from_attributes=True)

    id_paciente: int
    nombres_apellidos: str
    tipo_identificacion: str | None = None
    descripcion_tipo_identificacion: str | None = None
    numero_id: str
    fecha_nacimiento: date | None = None
    creado_en: datetime | None = None
