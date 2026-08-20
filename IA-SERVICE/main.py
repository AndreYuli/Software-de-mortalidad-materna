"""Punto de entrada del microservicio de IA generativa."""

from fastapi import FastAPI

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
