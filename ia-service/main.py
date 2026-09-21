"""Punto de entrada del microservicio de IA generativa."""

from fastapi import FastAPI, HTTPException, status

from core.config import Config
from ollama_client import OllamaUnavailableError, chatear, generar
from prompts import chat_datos, construir_prompt
from schemas import ChatRequest, ChatResponse, NarrativaRequest, NarrativaResponse

app = FastAPI(
    title='IA Generativa — Mortalidad Materna',
    description='Microservicio aislado que genera narrativas en lenguaje natural a partir de indicadores agregados.',
    version='1.0.0',
)


@app.get('/health', tags=['health'])
def health() -> dict[str, str]:
    """Verifica que el microservicio está en funcionamiento.

    Returns:
        Diccionario con status 'ok'.
    """
    resultado: dict[str, str] = {'status': 'ok'}
    return resultado


@app.post('/generar-narrativa', response_model=NarrativaResponse)
def generar_narrativa(payload: NarrativaRequest) -> NarrativaResponse:
    """Genera una narrativa en lenguaje natural a partir de indicadores agregados.

    Args:
        payload: Tipo de narrativa, tipo de análisis e indicadores ya agregados.

    Returns:
        La narrativa generada y el nombre del modelo usado.

    Raises:
        HTTPException: 503 si Ollama no está disponible o falla la generación.
    """
    prompt = construir_prompt(
        payload.tipo_narrativa, payload.indicadores, payload.tipo_analisis
    )
    try:
        texto = generar(prompt)
    except OllamaUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return NarrativaResponse(narrativa=texto, modelo=Config.ollama_model)


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Procesa una pregunta del usuario y devuelve la respuesta del LLM.

    Args:
        payload: Pregunta, historial, tipo de análisis y contexto.

    Returns:
        La respuesta generada y el modelo usado.

    Raises:
        HTTPException: 503 si Ollama no está disponible.
    """
    messages = chat_datos.construir(
        pregunta=payload.pregunta,
        historial=payload.historial,
        contexto=payload.contexto,
        tipo_analisis=payload.tipo_analisis,
    )
    try:
        texto = chatear(messages)
    except OllamaUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return ChatResponse(respuesta=texto, modelo=Config.ollama_model)
