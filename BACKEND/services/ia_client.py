"""Cliente HTTP hacia IA-SERVICE (microservicio de generación de narrativas)."""

from typing import Any

import httpx

from core.config import Config


class IAServiceUnavailableError(Exception):
    """Se lanza cuando IA-SERVICE no responde, da timeout o devuelve un error."""


def generar_narrativa(
    tipo_narrativa: str,
    tipo_analisis: str,
    indicadores: dict[str, Any],
) -> dict[str, str]:
    """Solicita a IA-SERVICE la generación de una narrativa.

    Args:
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        tipo_analisis: 'mortalidad' o 'morbilidad'.
        indicadores: Datos ya agregados (nunca filas de pacientes).

    Returns:
        Dict con `narrativa` (texto generado) y `modelo` (nombre del modelo LLM
        realmente usado por IA-SERVICE, no asumido en el backend).

    Raises:
        IAServiceUnavailableError: Si IA-SERVICE no responde, da timeout,
            rechaza la conexión o devuelve un status distinto de 200.
    """
    try:
        with httpx.Client(timeout=35.0) as client:
            response = client.post(
                f"{Config.ia_service_url}/generar-narrativa",
                json={
                    "tipo_narrativa": tipo_narrativa,
                    "tipo_analisis": tipo_analisis,
                    "indicadores": indicadores,
                },
            )
    except httpx.TimeoutException as exc:
        raise IAServiceUnavailableError(
            f"Timeout esperando respuesta de IA-SERVICE: {exc}"
        ) from exc
    except httpx.ConnectError as exc:
        raise IAServiceUnavailableError(f"No se pudo conectar a IA-SERVICE: {exc}") from exc

    if response.status_code != 200:
        raise IAServiceUnavailableError(
            f"IA-SERVICE devolvió status {response.status_code}: {response.text}"
        )

    body = response.json()
    return {"narrativa": body["narrativa"], "modelo": body["modelo"]}
