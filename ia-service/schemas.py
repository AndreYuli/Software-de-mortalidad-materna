"""Schemas Pydantic para request/response de generación de narrativas."""

from typing import Any, Literal

from pydantic import BaseModel

TipoNarrativa = Literal['resumen_ejecutivo', 'demoras', 'clustering', 'tendencias']
TipoAnalisis = Literal['mortalidad', 'morbilidad']


class NarrativaRequest(BaseModel):
    """Solicitud de generación de narrativa.

    Attributes:
        tipo_narrativa: Tipo de narrativa a generar.
        tipo_analisis: Tipo de análisis del que provienen los indicadores.
        indicadores: Datos ya agregados (nunca filas de pacientes).
    """

    tipo_narrativa: TipoNarrativa
    tipo_analisis: TipoAnalisis
    indicadores: dict[str, Any]


class NarrativaResponse(BaseModel):
    """Respuesta con la narrativa generada.

    Attributes:
        narrativa: Texto generado en lenguaje natural.
        modelo: Nombre del modelo LLM usado.
    """

    narrativa: str
    modelo: str


class ChatMensaje(BaseModel):
    """Mensaje individual en el historial de chat."""

    rol: Literal['usuario', 'asistente']
    contenido: str


class ChatRequest(BaseModel):
    """Solicitud de chat.

    Attributes:
        pregunta: La pregunta actual del usuario.
        historial: Mensajes previos en la conversación.
        tipo_analisis: Tipo de análisis del que provienen los indicadores.
        contexto: Datos ya agregados (nunca filas de pacientes).
    """

    pregunta: str
    historial: list[ChatMensaje]
    tipo_analisis: TipoAnalisis
    contexto: dict[str, Any]


class ChatResponse(BaseModel):
    """Respuesta del chatbot.

    Attributes:
        respuesta: Texto de la respuesta generada.
        modelo: Nombre del modelo LLM usado.
    """

    respuesta: str
    modelo: str
