from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date, time
from typing import Optional, Dict, Any, List

class UsuarioRegister(BaseModel):
    nombre: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class AnalisisResponse(BaseModel):
    id: int
    tipo: str
    nombre_archivo: str
    archivo: str
    fecha_carga: datetime
    total_registros: int
    resumen: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class ClusteringRequest(BaseModel):
    tipo_clustering: str = "kmeans"
    n_clusters: int = 3

class PacienteResponse(BaseModel):
    id_paciente: int
    nombres_apellidos: str
    tipo_identificacion: Optional[str] = None
    descripcion_tipo_identificacion: Optional[str] = None
    numero_id: str
    fecha_nacimiento: Optional[date] = None
    creado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
