# Microservicio de IA generativa — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar 4 narrativas en lenguaje natural (resumen ejecutivo, demoras/tiempo de remisión, clustering, tendencias) a partir de indicadores agregados, usando un microservicio FastAPI aislado que llama a Ollama local, con cache en Postgres y consumo bajo demanda desde el frontend.

**Architecture:** `IA-SERVICE/` (FastAPI, :8001, sin BD) recibe indicadores agregados y devuelve texto generado por Ollama. `BACKEND/` (FastAPI, :8000) cachea narrativas en la tabla `narrativa_ia` y llama a IA-SERVICE solo en cache-miss o `regenerar=True`. `FRONTED/` consume vía `NarrativaIA.tsx`, oculto silenciosamente si el servicio no responde.

**Tech Stack:** FastAPI, httpx, Ollama (modelo `qwen2.5`), SQLAlchemy, pytest + pytest-mock, React + TypeScript + vitest.

**Precondición:** requiere `docs/superpowers/plans/2026-08-20-migracion-typescript-frontend.md` ya ejecutado (el frontend de este plan se escribe en `.tsx`).

---

## Nota de verificación (hallazgos durante el mapeo del código, no asumidos)

- `BACKEND/` **no tiene ningún test hoy**, ni `pytest` en `requirements.txt`, ni carpeta `tests/`.
- **Ninguna tabla `api_*` se crea automáticamente** — no hay `Base.metadata.create_all()` en ningún archivo ni Alembic configurado. El script `sivigila_maternidad_postgres.sql` solo cubre las tablas del dominio SIVIGILA (`paciente`, `caso_*`, `cat_*`), no `api_analisis`/`api_usuario`/`api_sivigilaimportacion`. Este plan agrega `Base.metadata.create_all()` al arranque (Task 6) — resuelve esta brecha existente como efecto colateral necesario para que `narrativa_ia` se cree, y es coherente con no tener Alembic en el proyecto.
- `httpx` no está en `requirements.txt` (lo necesita tanto `TestClient` de FastAPI como `ia_client.py`).
- El resultado de `ejecutar_clustering` incluye arrays grandes por-registro (`pca_2d`, `pca_3d`, `clusters`) que **no deben enviarse al LLM** — la spec exige "solo agregados"; `narrativa_service.py` filtra a `{n_clusters, n_samples, features_used, cluster_sizes, cluster_profiles}` antes de llamar a IA-SERVICE.
- `AnalysisHomeSection` en `DashboardOKD.jsx` tiene un caso `segmento === 'ambos'` que mezcla datos de mortalidad y morbilidad sin un único `analisis_id`. Como IA-SERVICE opera sobre un `tipo_analisis` a la vez, la integración muestra **dos tarjetas `NarrativaIA`** (una por tipo) cuando `segmento === 'ambos'`, en vez de inventar una narrativa combinada fuera de diseño.

---

## File Structure

```
IA-SERVICE/                        ← NUEVO, hermano de BACKEND/ y FRONTED/
├── main.py
├── core/
│   ├── __init__.py
│   └── config.py
├── schemas.py
├── ollama_client.py
├── prompts/
│   ├── __init__.py
│   ├── resumen_ejecutivo.py
│   ├── demoras.py
│   ├── clustering.py
│   └── tendencias.py
├── requirements.txt
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_prompts.py
    ├── test_ollama_client.py
    └── test_main.py

BACKEND/
├── main.py                        ← MODIFICADO (create_all al arranque)
├── requirements.txt                ← MODIFICADO (+httpx, pytest, pytest-mock)
├── core/config.py                  ← MODIFICADO (+ia_service_url)
├── db/models_sqlalchemy.py         ← MODIFICADO (+NarrativaIA, +UniqueConstraint import)
├── services/
│   ├── ia_client.py                ← NUEVO
│   └── narrativa_service.py        ← NUEVO
├── api/routers/analisis.py         ← MODIFICADO (+endpoint narrativa)
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── fixtures_sivigila.py
    ├── test_mortalidad_processor.py    ← NUEVO (red de seguridad, código existente)
    ├── test_morbilidad_processor.py    ← NUEVO (red de seguridad, código existente)
    ├── test_ia_client.py
    ├── test_narrativa_service.py
    └── test_analisis_router_narrativa.py

FRONTED/maternanalytics/src/
├── api.ts                          ← MODIFICADO (+obtenerNarrativa, +tipos)
├── api.test.ts                     ← MODIFICADO (+casos narrativa)
├── types.ts                        ← MODIFICADO (+NarrativaResponse, TipoNarrativa)
└── components/
    ├── NarrativaIA.tsx              ← NUEVO
    ├── NarrativaIA.test.tsx         ← NUEVO
    ├── DashboardOKD.tsx             ← MODIFICADO (reemplaza getAIInsight)
    └── AnalisisView.tsx             ← MODIFICADO (+narrativas en overview y clustering)
```

---

## Parte 1 — IA-SERVICE

### Task 1: Scaffold de IA-SERVICE con health check

**Files:**
- Create: `IA-SERVICE/requirements.txt`
- Create: `IA-SERVICE/core/__init__.py`
- Create: `IA-SERVICE/core/config.py`
- Create: `IA-SERVICE/main.py`
- Create: `IA-SERVICE/tests/__init__.py`
- Create: `IA-SERVICE/tests/test_main.py`

- [ ] **Step 1: Crear estructura de carpetas y `requirements.txt`**

```bash
mkdir -p IA-SERVICE/core IA-SERVICE/prompts IA-SERVICE/tests
touch IA-SERVICE/core/__init__.py IA-SERVICE/tests/__init__.py IA-SERVICE/prompts/__init__.py
```

`IA-SERVICE/requirements.txt`:
```
fastapi==0.111.0
uvicorn==0.30.1
httpx==0.27.0
pydantic==2.7.4
pydantic-settings==2.14.1
pytest==8.2.2
pytest-mock==3.14.0
```

- [ ] **Step 2: Crear `IA-SERVICE/core/config.py`**

```python
"""Configuración centralizada de IA-SERVICE, cargada desde variables de entorno."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    """Configuración de conexión a Ollama y del servidor."""

    model_config = SettingsConfigDict(
        env_file=Path.cwd() / '.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    ollama_host: str = 'http://localhost:11434'
    ollama_model: str = 'qwen2.5'
    ollama_timeout_s: float = 30.0


Config = _Settings()
```

- [ ] **Step 3: Crear `IA-SERVICE/main.py` (solo health check por ahora)**

```python
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
```

- [ ] **Step 4: Escribir test de health check**

`IA-SERVICE/tests/test_main.py`:
```python
"""Tests del endpoint de health check."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_devuelve_ok():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

- [ ] **Step 5: Instalar dependencias y correr el test**

Run (desde `IA-SERVICE/`):
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest tests/test_main.py -v
```
Expected: `test_health_devuelve_ok PASSED`.

- [ ] **Step 6: Commit**

```bash
git add IA-SERVICE/
git commit -m "feat: scaffold de IA-SERVICE con health check"
```

---

### Task 2: Schemas y plantillas de prompt

**Files:**
- Create: `IA-SERVICE/schemas.py`
- Create: `IA-SERVICE/prompts/resumen_ejecutivo.py`
- Create: `IA-SERVICE/prompts/demoras.py`
- Create: `IA-SERVICE/prompts/clustering.py`
- Create: `IA-SERVICE/prompts/tendencias.py`
- Create: `IA-SERVICE/prompts/__init__.py`
- Create: `IA-SERVICE/tests/test_prompts.py`

- [ ] **Step 1: Crear `IA-SERVICE/schemas.py`**

```python
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
```

- [ ] **Step 2: Escribir la primera plantilla — `IA-SERVICE/prompts/resumen_ejecutivo.py`**

```python
"""Plantilla de prompt para el resumen ejecutivo."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que redacta resúmenes epidemiológicos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de resumen ejecutivo a partir de indicadores agregados.

    Args:
        indicadores: Subconjunto agregado con estadísticas básicas y causas/criterios principales.
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = 'Mortalidad Materna' if tipo_analisis == 'mortalidad' else 'Morbilidad Materna Extrema'
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Escribe un resumen ejecutivo del análisis de {evento} con los siguientes datos agregados:\n'
        f'{indicadores}\n\n'
        'Estructura el resumen en: (1) panorama general con las cifras clave, '
        '(2) el hallazgo más relevante, (3) una recomendación de salud pública derivada de los datos.'
    )
    return prompt
```

- [ ] **Step 3: Escribir `IA-SERVICE/prompts/demoras.py`**

```python
"""Plantilla de prompt para demoras (mortalidad) / tiempo de remisión (morbilidad)."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que interpreta demoras en la atención obstétrica. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de demoras/tiempo de remisión a partir de indicadores agregados.

    Args:
        indicadores: Para mortalidad, el dict de `analizar_demoras()` (4 demoras obstétricas).
            Para morbilidad, el dict de `analizar_tiempo_remision()` (boxplot de horas).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    if tipo_analisis == 'mortalidad':
        contexto = (
            'Los datos describen la proporción de casos con presencia de cada una de las '
            'cuatro demoras del modelo de las tres demoras obstétricas ampliado a cuatro: '
            'reconocimiento del problema, decisión de buscar atención, acceso al centro de salud '
            'y calidad de la atención recibida.'
        )
    else:
        contexto = (
            'Los datos describen la distribución estadística (mínimo, cuartiles, mediana, máximo) '
            'del tiempo de remisión entre instituciones, en horas.'
        )
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'{contexto}\n\n'
        f'Datos agregados:\n{indicadores}\n\n'
        'Interpreta cuál es la demora o el rango de tiempo más crítico y sugiere una '
        'acción concreta de salud pública para mitigarlo.'
    )
    return prompt
```

- [ ] **Step 4: Escribir `IA-SERVICE/prompts/clustering.py`**

```python
"""Plantilla de prompt para perfiles de clustering."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que interpreta resultados de clustering (K-means o jerárquico) '
    'sobre casos obstétricos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de interpretación de clusters a partir de perfiles agregados.

    Args:
        indicadores: Dict con `n_clusters`, `n_samples`, `features_used`,
            `cluster_sizes` y `cluster_profiles` (promedios de features por cluster).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = 'mortalidad materna' if tipo_analisis == 'mortalidad' else 'morbilidad materna extrema'
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Se agruparon casos de {evento} en clusters según similitud de características clínicas. '
        f'Perfiles obtenidos:\n{indicadores}\n\n'
        'Describe qué caracteriza a cada cluster (usa los promedios de features de cada uno) '
        'y qué perfil de paciente representa el grupo de mayor tamaño.'
    )
    return prompt
```

- [ ] **Step 5: Escribir `IA-SERVICE/prompts/tendencias.py`**

```python
"""Plantilla de prompt para alertas de tendencias mensuales."""

from typing import Any

_INSTRUCCIONES = (
    'Eres un asistente de salud pública que interpreta tendencias temporales de casos obstétricos. '
    'Responde en español, en un tono profesional dirigido a personal de salud pública. '
    'Usa entre 150 y 250 palabras. '
    'No inventes cifras que no estén en los datos proporcionados. '
    'No menciones nombres propios ni identificadores de personas.'
)


def construir(indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Arma el prompt de alertas de tendencias a partir de la distribución mensual.

    Args:
        indicadores: Dict `distribucion_mensual` (conteo de casos por mes/año).
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.
    """
    evento = 'mortalidad materna' if tipo_analisis == 'mortalidad' else 'morbilidad materna extrema'
    prompt = (
        f'{_INSTRUCCIONES}\n\n'
        f'Distribución mensual de casos de {evento}:\n{indicadores}\n\n'
        'Identifica si hay una tendencia al alza, a la baja, o picos puntuales, '
        'y si el patrón amerita una alerta de vigilancia epidemiológica.'
    )
    return prompt
```

- [ ] **Step 6: Crear el dispatcher `IA-SERVICE/prompts/__init__.py`**

```python
"""Dispatcher de plantillas de prompt por tipo de narrativa."""

from typing import Any, Callable

from prompts import clustering, demoras, resumen_ejecutivo, tendencias

_CONSTRUCTORES: dict[str, Callable[[dict[str, Any], str], str]] = {
    'resumen_ejecutivo': resumen_ejecutivo.construir,
    'demoras': demoras.construir,
    'clustering': clustering.construir,
    'tendencias': tendencias.construir,
}


def construir_prompt(tipo_narrativa: str, indicadores: dict[str, Any], tipo_analisis: str) -> str:
    """Selecciona la plantilla según `tipo_narrativa` y arma el prompt.

    Args:
        tipo_narrativa: Uno de 'resumen_ejecutivo', 'demoras', 'clustering', 'tendencias'.
        indicadores: Datos agregados relevantes para esa narrativa.
        tipo_analisis: 'mortalidad' o 'morbilidad'.

    Returns:
        Prompt completo listo para enviar al LLM.

    Raises:
        KeyError: Si `tipo_narrativa` no tiene plantilla registrada.
    """
    constructor = _CONSTRUCTORES[tipo_narrativa]
    return constructor(indicadores, tipo_analisis)
```

- [ ] **Step 7: Escribir tests de las plantillas**

`IA-SERVICE/tests/test_prompts.py`:
```python
"""Tests de las plantillas de prompt: no truenan con datos vacíos o parciales."""

import pytest

from prompts import construir_prompt

_TIPOS = ['resumen_ejecutivo', 'demoras', 'clustering', 'tendencias']


@pytest.mark.parametrize('tipo_narrativa', _TIPOS)
@pytest.mark.parametrize('tipo_analisis', ['mortalidad', 'morbilidad'])
def test_construir_prompt_con_indicadores_vacios(tipo_narrativa, tipo_analisis):
    prompt = construir_prompt(tipo_narrativa, {}, tipo_analisis)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_construir_prompt_resumen_ejecutivo_incluye_datos():
    indicadores = {'total_casos': 42, 'edad_promedio': 27.5}
    prompt = construir_prompt('resumen_ejecutivo', indicadores, 'mortalidad')
    assert '42' in prompt
    assert '27.5' in prompt


def test_construir_prompt_tipo_narrativa_invalido_lanza_keyerror():
    with pytest.raises(KeyError):
        construir_prompt('inexistente', {}, 'mortalidad')
```

- [ ] **Step 8: Correr los tests**

Run: `pytest tests/test_prompts.py -v` (desde `IA-SERVICE/`, venv activo)
Expected: 10 tests PASSED (4 tipos × 2 tipo_analisis + 2 tests específicos).

- [ ] **Step 9: Commit**

```bash
git add IA-SERVICE/schemas.py IA-SERVICE/prompts/ IA-SERVICE/tests/test_prompts.py
git commit -m "feat: schemas y plantillas de prompt para las 4 narrativas de IA-SERVICE"
```

---

### Task 3: Cliente de Ollama

**Files:**
- Create: `IA-SERVICE/ollama_client.py`
- Create: `IA-SERVICE/tests/test_ollama_client.py`

- [ ] **Step 1: Escribir el test con `httpx` mockeado (éxito)**

`IA-SERVICE/tests/test_ollama_client.py`:
```python
"""Tests del cliente HTTP hacia Ollama, con httpx mockeado."""

import httpx
import pytest

from ollama_client import OllamaUnavailableError, generar


def test_generar_devuelve_texto_en_exito(mocker):
    respuesta_mock = httpx.Response(
        200, json={'response': 'Texto generado por el modelo.'},
        request=httpx.Request('POST', 'http://localhost:11434/api/generate'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    texto = generar('un prompt de prueba')

    assert texto == 'Texto generado por el modelo.'


def test_generar_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.ConnectError('connection refused'))

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')


def test_generar_lanza_error_en_status_no_200(mocker):
    respuesta_mock = httpx.Response(
        500, json={'error': 'modelo no encontrado'},
        request=httpx.Request('POST', 'http://localhost:11434/api/generate'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    with pytest.raises(OllamaUnavailableError):
        generar('un prompt de prueba')
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `pytest tests/test_ollama_client.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'ollama_client'`.

- [ ] **Step 3: Implementar `IA-SERVICE/ollama_client.py`**

```python
"""Cliente HTTP hacia la API local de Ollama."""

import httpx

from core.config import Config


class OllamaUnavailableError(Exception):
    """Se lanza cuando Ollama no responde, da timeout o devuelve un error."""


def generar(prompt: str) -> str:
    """Envía un prompt a Ollama y devuelve el texto generado.

    Args:
        prompt: Prompt completo ya construido por una plantilla.

    Returns:
        Texto generado por el modelo.

    Raises:
        OllamaUnavailableError: Si Ollama no responde, da timeout, rechaza la
            conexión o devuelve un status distinto de 200.
    """
    try:
        with httpx.Client(timeout=Config.ollama_timeout_s) as client:
            response = client.post(
                f'{Config.ollama_host}/api/generate',
                json={'model': Config.ollama_model, 'prompt': prompt, 'stream': False},
            )
    except httpx.TimeoutException as exc:
        raise OllamaUnavailableError(f'Timeout esperando respuesta de Ollama: {exc}') from exc
    except httpx.ConnectError as exc:
        raise OllamaUnavailableError(f'No se pudo conectar a Ollama: {exc}') from exc

    if response.status_code != 200:
        raise OllamaUnavailableError(f'Ollama devolvió status {response.status_code}: {response.text}')

    return response.json()['response']
```

- [ ] **Step 4: Correr los tests de nuevo**

Run: `pytest tests/test_ollama_client.py -v`
Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add IA-SERVICE/ollama_client.py IA-SERVICE/tests/test_ollama_client.py
git commit -m "feat: cliente HTTP hacia Ollama con manejo de timeout/conexión"
```

---

### Task 4: Endpoint `/generar-narrativa`

**Files:**
- Modify: `IA-SERVICE/main.py`
- Modify: `IA-SERVICE/tests/test_main.py`

- [ ] **Step 1: Escribir los tests del endpoint (fallarán hasta implementarlo)**

Agregar a `IA-SERVICE/tests/test_main.py`:
```python
def test_generar_narrativa_devuelve_200_en_exito(mocker):
    mocker.patch('main.generar', return_value='Narrativa generada de prueba.')

    response = client.post('/generar-narrativa', json={
        'tipo_narrativa': 'resumen_ejecutivo',
        'tipo_analisis': 'mortalidad',
        'indicadores': {'total_casos': 10},
    })

    assert response.status_code == 200
    body = response.json()
    assert body['narrativa'] == 'Narrativa generada de prueba.'
    assert body['modelo'] == 'qwen2.5'


def test_generar_narrativa_devuelve_422_con_tipo_invalido():
    response = client.post('/generar-narrativa', json={
        'tipo_narrativa': 'no_existe',
        'tipo_analisis': 'mortalidad',
        'indicadores': {},
    })
    assert response.status_code == 422


def test_generar_narrativa_devuelve_503_si_ollama_no_disponible(mocker):
    from ollama_client import OllamaUnavailableError
    mocker.patch('main.generar', side_effect=OllamaUnavailableError('no disponible'))

    response = client.post('/generar-narrativa', json={
        'tipo_narrativa': 'resumen_ejecutivo',
        'tipo_analisis': 'mortalidad',
        'indicadores': {'total_casos': 10},
    })

    assert response.status_code == 503
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `pytest tests/test_main.py -v`
Expected: los 3 tests nuevos FAIL (404, endpoint no existe).

- [ ] **Step 3: Implementar el endpoint en `IA-SERVICE/main.py`**

```python
"""Punto de entrada del microservicio de IA generativa."""

from fastapi import FastAPI, HTTPException, status

from core.config import Config
from ollama_client import OllamaUnavailableError, generar
from prompts import construir_prompt
from schemas import NarrativaRequest, NarrativaResponse

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
    prompt = construir_prompt(payload.tipo_narrativa, payload.indicadores, payload.tipo_analisis)
    try:
        texto = generar(prompt)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return NarrativaResponse(narrativa=texto, modelo=Config.ollama_model)
```

- [ ] **Step 4: Correr todos los tests de IA-SERVICE**

Run: `pytest tests/ -v` (desde `IA-SERVICE/`)
Expected: todos PASSED (health + 10 de prompts + 4 de ollama_client + 3 nuevos = 18 tests).

- [ ] **Step 5: Commit**

```bash
git add IA-SERVICE/main.py IA-SERVICE/tests/test_main.py
git commit -m "feat: endpoint POST /generar-narrativa en IA-SERVICE"
```

---

## Parte 2 — BACKEND

### Task 5: Dependencias de testing + red de seguridad sobre código existente

**Files:**
- Modify: `BACKEND/requirements.txt`
- Create: `BACKEND/tests/__init__.py`
- Create: `BACKEND/tests/conftest.py`
- Create: `BACKEND/tests/fixtures_sivigila.py`
- Create: `BACKEND/tests/test_mortalidad_processor.py`
- Create: `BACKEND/tests/test_morbilidad_processor.py`

Antes de tocar el pipeline de cálculo existente, se agregan tests de regresión que hoy no existen — para detectar si algo de lo que viene se rompe.

- [ ] **Step 1: Agregar dependencias de testing a `BACKEND/requirements.txt`**

Agregar al final del archivo:
```
httpx==0.27.0
pytest==8.2.2
pytest-mock==3.14.0
```

- [ ] **Step 2: Instalar**

Run (desde `BACKEND/`, venv activo):
```bash
pip install -r requirements.txt
```

- [ ] **Step 3: Crear `BACKEND/tests/__init__.py`** (vacío)

- [ ] **Step 4: Crear el fixture sintético `BACKEND/tests/fixtures_sivigila.py`**

```python
"""DataFrames sintéticos de ejemplo para tests de regresión de los processors."""

import pandas as pd


def df_mortalidad_ejemplo() -> pd.DataFrame:
    """Construye un DataFrame sintético de 6 casos de mortalidad con columnas SIVIGILA 550.

    Returns:
        DataFrame con columnas suficientes para ejercitar estadísticas básicas,
        momento de muerte, demoras y causas CIE-10.
    """
    return pd.DataFrame({
        'Edad': [22, 31, 27, 19, 35, 24],
        '6.5 Gestaciones': [2, 3, 1, 1, 4, 2],
        '8.1 No. CPN': [4, 6, 2, 0, 8, 5],
        '9.1 Momento de la muerte': [1, 2, 3, 1, 4, 2],
        '10.1 Causa básica CIE-10': ['O14.1', 'O72.1', 'O14.1', 'O99.4', 'O72.1', 'O14.1'],
        '10.3.1 Demora 1': [1, 0, 1, 1, 0, 0],
        '10.3.2 Demora 2': [1, 0, 0, 1, 0, 1],
        '10.3.3 Demora 3': [0, 0, 1, 1, 0, 0],
        '10.3.4 Demora 4': [1, 1, 0, 1, 0, 0],
    })


def df_morbilidad_ejemplo() -> pd.DataFrame:
    """Construye un DataFrame sintético de 6 casos de morbilidad con columnas SIVIGILA 549.

    Returns:
        DataFrame con columnas suficientes para ejercitar estadísticas básicas,
        criterios de inclusión y tiempo de remisión.
    """
    return pd.DataFrame({
        'Edad': [24, 29, 33, 20, 27, 31],
        'N° gestaciones': [1, 2, 3, 1, 2, 4],
        'Partos vaginales': [0, 1, 2, 0, 1, 3],
        'Cesáreas': [1, 0, 1, 1, 0, 0],
        'N° controles prenatales': [3, 5, 6, 1, 4, 7],
        'Edad gestacional ocurrencia (sem)': [32, 28, 36, 24, 30, 34],
        'Eclampsia': [1, 0, 0, 0, 1, 0],
        'Preeclampsia': [0, 1, 1, 0, 0, 1],
        'Total criterios': [1, 1, 2, 0, 1, 1],
        'Días estancia hospitalaria': [3, 5, 8, 2, 4, 6],
        'Tiempo remisión (h)': [2.5, 1.0, 4.0, 0.5, 3.0, 6.0],
    })
```

- [ ] **Step 5: Escribir `BACKEND/tests/test_mortalidad_processor.py`**

```python
"""Tests de regresión sobre MortalidadProcessor (código existente, sin tests previos)."""

from services._mortalidad_processor import MortalidadProcessor
from tests.fixtures_sivigila import df_mortalidad_ejemplo


def test_calcular_estadisticas_basicas_con_datos_sinteticos():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    stats = p.calcular_estadisticas_basicas()
    assert stats['total_casos'] == 6
    assert stats['edad_promedio'] == (22 + 31 + 27 + 19 + 35 + 24) / 6
    assert stats['gestaciones_promedio'] == (2 + 3 + 1 + 1 + 4 + 2) / 6


def test_analizar_momento_muerte_distribuye_correctamente():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_momento_muerte()
    assert resultado['total'] == 6
    assert resultado['distribucion']['Durante el embarazo'] == 2
    assert resultado['distribucion']['Durante el parto'] == 2


def test_analizar_demoras_calcula_porcentajes():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_demoras()
    assert resultado['demora_1']['casos_con_demora'] == 3
    assert resultado['demora_1']['porcentaje'] == 50.0


def test_analizar_causas_cie10_top_causas():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_causas_cie10(top_n=5)
    assert resultado['total_causas_unicas'] == 3
    top = {c['codigo']: c['casos'] for c in resultado['top_causas']}
    assert top['O14.1'] == 3


def test_clustering_factores_riesgo_no_truena_con_datos_suficientes():
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.clustering_factores_riesgo(n_clusters=2)
    assert resultado['n_clusters'] == 2
    assert resultado['n_samples'] > 0
    assert len(resultado['cluster_profiles']) == 2
```

- [ ] **Step 6: Escribir `BACKEND/tests/test_morbilidad_processor.py`**

```python
"""Tests de regresión sobre MorbilidadProcessor (código existente, sin tests previos)."""

from services._morbilidad_processor import MorbilidadProcessor
from tests.fixtures_sivigila import df_morbilidad_ejemplo


def test_calcular_estadisticas_basicas_con_datos_sinteticos():
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    stats = p.calcular_estadisticas_basicas()
    assert stats['total_casos'] == 6


def test_analizar_tiempo_remision_calcula_boxplot():
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_tiempo_remision()
    assert resultado['total'] == 6
    assert resultado['min'] == 0.5
    assert resultado['max'] == 6.0


def test_clustering_perfiles_morbilidad_no_truena_con_datos_suficientes():
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.clustering_perfiles_morbilidad(n_clusters=2)
    assert resultado['n_clusters'] == 2
    assert len(resultado['cluster_profiles']) == 2
```

- [ ] **Step 7: Correr los tests (requieren solo `BACKEND/` en el path, sin BD)**

Run (desde `BACKEND/`):
```bash
pytest tests/test_mortalidad_processor.py tests/test_morbilidad_processor.py -v
```
Expected: 8 tests PASSED.

- [ ] **Step 8: Commit**

```bash
git add BACKEND/requirements.txt BACKEND/tests/__init__.py BACKEND/tests/fixtures_sivigila.py BACKEND/tests/test_mortalidad_processor.py BACKEND/tests/test_morbilidad_processor.py
git commit -m "test: agregar pytest y red de seguridad de regresión sobre los processors existentes"
```

---

### Task 6: `conftest.py` con SQLite en memoria + `create_all()` en el arranque

**Files:**
- Create: `BACKEND/tests/conftest.py`
- Modify: `BACKEND/main.py`

- [ ] **Step 1: Agregar `Base.metadata.create_all()` al arranque de la app**

En `BACKEND/main.py`, después del bloque de imports y antes de `# --- CORS ---`, agregar:

```python
from db.database import Base, engine
from db.models_sqlalchemy import Analisis, SivigilaImportacion, Usuario  # noqa: F401
```

(el import de los modelos es necesario para que `Base.metadata` los conozca antes de `create_all`; `NarrativaIA` todavía no existe en este punto del plan — se agrega a este mismo import en el Task 7, cuando se define esa clase)

Y después de la sección de archivos estáticos, antes de `# --- Routers ---`, agregar:

```python
# ---------------------------------------------------------------------------
# Creación de tablas propias de la API (no gestionadas por el script SQL)
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)
```

- [ ] **Step 2: Crear `BACKEND/tests/conftest.py` con sesión de BD de test en SQLite**

```python
"""Fixtures compartidos de pytest: sesión de base de datos en SQLite en memoria."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.database import Base


@pytest.fixture
def db_session():
    """Provee una sesión de BD SQLite en memoria, aislada por test.

    Yields:
        Sesión de SQLAlchemy con todas las tablas creadas.
    """
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 3: Verificar que el backend sigue arrancando**

Run (desde `BACKEND/`, con Postgres corriendo y configurado como hoy):
```bash
python -m uvicorn main:app --reload
```
Expected: arranca sin error; `GET http://localhost:8000/health` responde `{"status": "ok"}`. Detener con Ctrl+C.

- [ ] **Step 4: Commit**

```bash
git add BACKEND/main.py BACKEND/tests/conftest.py
git commit -m "feat: crear tablas de la API al arranque + fixture de BD de test en SQLite"
```

---

### Task 7: Modelo `NarrativaIA` + configuración de `ia_service_url`

**Files:**
- Modify: `BACKEND/db/models_sqlalchemy.py`
- Modify: `BACKEND/core/config.py`
- Modify: `BACKEND/main.py`
- Create: `BACKEND/tests/test_narrativa_ia_model.py`

- [ ] **Step 1: Agregar el modelo en `BACKEND/db/models_sqlalchemy.py`**

Cambiar el import del inicio del archivo (línea 3-6) de:
```python
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, JSON, Numeric, String, Text, Time,
)
```
a:
```python
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, JSON, Numeric, String, Text, Time, UniqueConstraint,
)
```

Y agregar, después de la clase `Analisis` (después de su línea `resumen = Column(JSON, nullable=False)`):

```python
class NarrativaIA(Base):
    """Narrativa en lenguaje natural generada por IA-SERVICE, cacheada por análisis.

    Attributes:
        analisis_id: FK al análisis del que provienen los indicadores.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        filtros_hash: Hash de los filtros activos (year, month, tipo_clustering, n_clusters).
        contenido: Texto generado.
        modelo: Nombre del modelo LLM usado.
        generado_en: Fecha y hora de generación.
    """

    __tablename__ = 'narrativa_ia'
    __table_args__ = (UniqueConstraint('analisis_id', 'tipo_narrativa', 'filtros_hash'),)

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    analisis_id = Column(Integer, ForeignKey('api_analisis.id'), nullable=False)
    tipo_narrativa = Column(String(30), nullable=False)
    filtros_hash = Column(String(64), nullable=False)
    contenido = Column(Text, nullable=False)
    modelo = Column(String(50), nullable=False)
    generado_en = Column(DateTime, nullable=False)
```

- [ ] **Step 2: Agregar `ia_service_url` a `BACKEND/core/config.py`**

En la clase `_Settings`, después del bloque `# --- CORS ---` y su `cors_origins`, agregar:

```python
    # --- IA generativa ---
    ia_service_url: str = 'http://localhost:8001'
```

- [ ] **Step 3: Completar el import de modelos en `BACKEND/main.py` (ahora que `NarrativaIA` ya existe)**

En `BACKEND/main.py`, la línea agregada en el Task 6:
```python
from db.models_sqlalchemy import Analisis, SivigilaImportacion, Usuario  # noqa: F401
```
cambiarla a:
```python
from db.models_sqlalchemy import Analisis, NarrativaIA, SivigilaImportacion, Usuario  # noqa: F401
```

- [ ] **Step 4: Verificar que el backend arranca y crea la tabla `narrativa_ia`**

Run (desde `BACKEND/`, con Postgres corriendo y configurado como hoy):
```bash
python -m uvicorn main:app --reload
```
Expected: arranca sin error. Verificar en la BD (`psql` o pgAdmin) que la tabla `narrativa_ia` fue creada. Detener con Ctrl+C.

- [ ] **Step 5: Escribir test de que la tabla se crea correctamente**

`BACKEND/tests/test_narrativa_ia_model.py`:
```python
"""Test de que el modelo NarrativaIA se mapea y persiste correctamente."""

from datetime import datetime, timezone

from db.models_sqlalchemy import Analisis, NarrativaIA


def test_narrativa_ia_se_guarda_y_recupera(db_session):
    analisis = Analisis(
        tipo='mortalidad', nombre_archivo='test.xlsx', archivo_hash='abc123',
        archivo='media/test.xlsx', fecha_carga=datetime.now(timezone.utc),
        total_registros=5, resumen={},
    )
    db_session.add(analisis)
    db_session.commit()

    narrativa = NarrativaIA(
        analisis_id=analisis.id, tipo_narrativa='resumen_ejecutivo',
        filtros_hash='hash1', contenido='Texto de prueba.',
        modelo='qwen2.5', generado_en=datetime.now(timezone.utc),
    )
    db_session.add(narrativa)
    db_session.commit()

    guardada = db_session.query(NarrativaIA).filter_by(analisis_id=analisis.id).first()
    assert guardada is not None
    assert guardada.contenido == 'Texto de prueba.'


def test_narrativa_ia_unique_constraint_impide_duplicados(db_session):
    analisis = Analisis(
        tipo='mortalidad', nombre_archivo='test.xlsx', archivo_hash='abc123',
        archivo='media/test.xlsx', fecha_carga=datetime.now(timezone.utc),
        total_registros=5, resumen={},
    )
    db_session.add(analisis)
    db_session.commit()

    db_session.add(NarrativaIA(
        analisis_id=analisis.id, tipo_narrativa='resumen_ejecutivo',
        filtros_hash='hash1', contenido='v1', modelo='qwen2.5',
        generado_en=datetime.now(timezone.utc),
    ))
    db_session.commit()

    db_session.add(NarrativaIA(
        analisis_id=analisis.id, tipo_narrativa='resumen_ejecutivo',
        filtros_hash='hash1', contenido='v2', modelo='qwen2.5',
        generado_en=datetime.now(timezone.utc),
    ))
    try:
        db_session.commit()
        assert False, 'Debió lanzar un error de unique constraint'
    except Exception:
        db_session.rollback()
```

- [ ] **Step 6: Correr el test**

Run: `pytest tests/test_narrativa_ia_model.py -v`
Expected: 2 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add BACKEND/db/models_sqlalchemy.py BACKEND/core/config.py BACKEND/main.py BACKEND/tests/test_narrativa_ia_model.py
git commit -m "feat: modelo NarrativaIA con cache por analisis+tipo+filtros"
```

---

### Task 8: `services/ia_client.py`

**Files:**
- Create: `BACKEND/services/ia_client.py`
- Create: `BACKEND/tests/test_ia_client.py`

- [ ] **Step 1: Escribir los tests (fallarán hasta implementar)**

`BACKEND/tests/test_ia_client.py`:
```python
"""Tests del cliente hacia IA-SERVICE, con httpx mockeado."""

import httpx
import pytest

from services.ia_client import IAServiceUnavailableError, generar_narrativa


def test_generar_narrativa_devuelve_narrativa_y_modelo_en_exito(mocker):
    respuesta_mock = httpx.Response(
        200, json={'narrativa': 'Texto generado.', 'modelo': 'qwen2.5'},
        request=httpx.Request('POST', 'http://localhost:8001/generar-narrativa'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    resultado = generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})

    assert resultado == {'narrativa': 'Texto generado.', 'modelo': 'qwen2.5'}


def test_generar_narrativa_lanza_error_en_timeout(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.TimeoutException('timeout'))

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})


def test_generar_narrativa_lanza_error_en_conexion_rechazada(mocker):
    mocker.patch('httpx.Client.post', side_effect=httpx.ConnectError('connection refused'))

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})


def test_generar_narrativa_lanza_error_en_503_de_ia_service(mocker):
    respuesta_mock = httpx.Response(
        503, json={'detail': 'Ollama no disponible'},
        request=httpx.Request('POST', 'http://localhost:8001/generar-narrativa'),
    )
    mocker.patch('httpx.Client.post', return_value=respuesta_mock)

    with pytest.raises(IAServiceUnavailableError):
        generar_narrativa('resumen_ejecutivo', 'mortalidad', {'total_casos': 5})
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `pytest tests/test_ia_client.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'services.ia_client'`.

- [ ] **Step 3: Implementar `BACKEND/services/ia_client.py`**

```python
"""Cliente HTTP hacia IA-SERVICE (microservicio de generación de narrativas)."""

from typing import Any

import httpx

from core.config import Config


class IAServiceUnavailableError(Exception):
    """Se lanza cuando IA-SERVICE no responde, da timeout o devuelve un error."""


def generar_narrativa(tipo_narrativa: str, tipo_analisis: str, indicadores: dict[str, Any]) -> dict[str, str]:
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
                f'{Config.ia_service_url}/generar-narrativa',
                json={
                    'tipo_narrativa': tipo_narrativa,
                    'tipo_analisis': tipo_analisis,
                    'indicadores': indicadores,
                },
            )
    except httpx.TimeoutException as exc:
        raise IAServiceUnavailableError(f'Timeout esperando respuesta de IA-SERVICE: {exc}') from exc
    except httpx.ConnectError as exc:
        raise IAServiceUnavailableError(f'No se pudo conectar a IA-SERVICE: {exc}') from exc

    if response.status_code != 200:
        raise IAServiceUnavailableError(f'IA-SERVICE devolvió status {response.status_code}: {response.text}')

    body = response.json()
    return {'narrativa': body['narrativa'], 'modelo': body['modelo']}
```

- [ ] **Step 4: Correr los tests de nuevo**

Run: `pytest tests/test_ia_client.py -v`
Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add BACKEND/services/ia_client.py BACKEND/tests/test_ia_client.py
git commit -m "feat: cliente HTTP del backend hacia IA-SERVICE"
```

---

### Task 9: `services/narrativa_service.py` (cache + filtrado de indicadores)

**Files:**
- Create: `BACKEND/services/narrativa_service.py`
- Create: `BACKEND/tests/test_narrativa_service.py`

- [ ] **Step 1: Escribir los tests**

`BACKEND/tests/test_narrativa_service.py`:
```python
"""Tests de narrativa_service: cache hit/miss, regenerar, filtros_hash."""

from datetime import datetime, timezone

from db.models_sqlalchemy import Analisis, NarrativaIA
from services.narrativa_service import calcular_filtros_hash, obtener_narrativa


def _crear_analisis(db_session) -> Analisis:
    analisis = Analisis(
        tipo='mortalidad', nombre_archivo='test.xlsx', archivo_hash='abc123',
        archivo='media/test.xlsx', fecha_carga=datetime.now(timezone.utc),
        total_registros=5, resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    return analisis


def test_calcular_filtros_hash_distingue_filtros_distintos():
    hash1 = calcular_filtros_hash({'year': '2026', 'month': None})
    hash2 = calcular_filtros_hash({'year': '2025', 'month': None})
    assert hash1 != hash2


def test_calcular_filtros_hash_es_estable_para_mismos_filtros():
    hash1 = calcular_filtros_hash({'year': '2026', 'month': '05'})
    hash2 = calcular_filtros_hash({'year': '2026', 'month': '05'})
    assert hash1 == hash2


def test_obtener_narrativa_usa_cache_si_existe(db_session, mocker):
    analisis = _crear_analisis(db_session)
    filtros_hash = calcular_filtros_hash({'year': None, 'month': None})
    db_session.add(NarrativaIA(
        analisis_id=analisis.id, tipo_narrativa='resumen_ejecutivo',
        filtros_hash=filtros_hash, contenido='Narrativa cacheada.',
        modelo='qwen2.5', generado_en=datetime.now(timezone.utc),
    ))
    db_session.commit()

    mock_ia_client = mocker.patch('services.narrativa_service.ia_client.generar_narrativa')

    resultado = obtener_narrativa(
        db_session, analisis, 'resumen_ejecutivo',
        indicadores={'total_casos': 99}, filtros={'year': None, 'month': None}, regenerar=False,
    )

    assert resultado['narrativa'] == 'Narrativa cacheada.'
    assert resultado['desde_cache'] is True
    mock_ia_client.assert_not_called()


def test_obtener_narrativa_llama_ia_client_si_no_hay_cache(db_session, mocker):
    analisis = _crear_analisis(db_session)
    mock_ia_client = mocker.patch(
        'services.narrativa_service.ia_client.generar_narrativa',
        return_value={'narrativa': 'Narrativa nueva.', 'modelo': 'qwen2.5'},
    )

    resultado = obtener_narrativa(
        db_session, analisis, 'resumen_ejecutivo',
        indicadores={'total_casos': 10}, filtros={'year': None, 'month': None}, regenerar=False,
    )

    assert resultado['narrativa'] == 'Narrativa nueva.'
    assert resultado['modelo'] == 'qwen2.5'
    assert resultado['desde_cache'] is False
    mock_ia_client.assert_called_once_with('resumen_ejecutivo', 'mortalidad', {'total_casos': 10})


def test_obtener_narrativa_regenerar_llama_ia_client_aunque_haya_cache(db_session, mocker):
    analisis = _crear_analisis(db_session)
    filtros_hash = calcular_filtros_hash({'year': None, 'month': None})
    db_session.add(NarrativaIA(
        analisis_id=analisis.id, tipo_narrativa='resumen_ejecutivo',
        filtros_hash=filtros_hash, contenido='Narrativa vieja.',
        modelo='qwen2.5', generado_en=datetime.now(timezone.utc),
    ))
    db_session.commit()

    mock_ia_client = mocker.patch(
        'services.narrativa_service.ia_client.generar_narrativa',
        return_value={'narrativa': 'Narrativa regenerada.', 'modelo': 'qwen2.5'},
    )

    resultado = obtener_narrativa(
        db_session, analisis, 'resumen_ejecutivo',
        indicadores={'total_casos': 10}, filtros={'year': None, 'month': None}, regenerar=True,
    )

    assert resultado['narrativa'] == 'Narrativa regenerada.'
    assert resultado['desde_cache'] is False
    mock_ia_client.assert_called_once()
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `pytest tests/test_narrativa_service.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'services.narrativa_service'`.

- [ ] **Step 3: Implementar `BACKEND/services/narrativa_service.py`**

```python
"""Orquesta la generación y cache de narrativas de IA a partir de indicadores agregados."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from db.models_sqlalchemy import Analisis, NarrativaIA
from services import ia_client


def calcular_filtros_hash(filtros: dict[str, Any]) -> str:
    """Calcula un hash estable de los filtros activos para usar como clave de cache.

    Args:
        filtros: Diccionario de filtros (year, month, tipo_clustering, n_clusters, etc.).

    Returns:
        Hash SHA-256 hexadecimal de los filtros serializados de forma determinista.
    """
    filtros_serializados = json.dumps(filtros, sort_keys=True, default=str)
    return hashlib.sha256(filtros_serializados.encode('utf-8')).hexdigest()


def obtener_narrativa(
    db: Session,
    analisis: Analisis,
    tipo_narrativa: str,
    indicadores: dict[str, Any],
    filtros: dict[str, Any],
    regenerar: bool,
) -> dict[str, Any]:
    """Obtiene la narrativa desde cache, o la genera y la cachea si no existe.

    Args:
        db: Sesión de base de datos.
        analisis: Instancia del análisis al que pertenece la narrativa.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        indicadores: Datos agregados relevantes ya calculados por el llamador.
        filtros: Filtros activos (year, month, tipo_clustering, n_clusters) usados para la clave de cache.
        regenerar: Si es True, ignora la cache y fuerza una nueva llamada a IA-SERVICE.

    Returns:
        Dict con `narrativa`, `modelo`, `generado_en` y `desde_cache`.

    Raises:
        services.ia_client.IAServiceUnavailableError: Si IA-SERVICE no está disponible.
    """
    filtros_hash = calcular_filtros_hash(filtros)

    if not regenerar:
        existente = db.query(NarrativaIA).filter_by(
            analisis_id=analisis.id, tipo_narrativa=tipo_narrativa, filtros_hash=filtros_hash,
        ).first()
        if existente is not None:
            return {
                'narrativa': existente.contenido, 'modelo': existente.modelo,
                'generado_en': existente.generado_en, 'desde_cache': True,
            }

    resultado_ia = ia_client.generar_narrativa(tipo_narrativa, analisis.tipo, indicadores)
    texto = resultado_ia['narrativa']
    modelo = resultado_ia['modelo']
    ahora = datetime.now(timezone.utc)

    registro = db.query(NarrativaIA).filter_by(
        analisis_id=analisis.id, tipo_narrativa=tipo_narrativa, filtros_hash=filtros_hash,
    ).first()
    if registro is not None:
        registro.contenido = texto
        registro.modelo = modelo
        registro.generado_en = ahora
    else:
        registro = NarrativaIA(
            analisis_id=analisis.id, tipo_narrativa=tipo_narrativa, filtros_hash=filtros_hash,
            contenido=texto, modelo=modelo, generado_en=ahora,
        )
        db.add(registro)
    db.commit()

    return {'narrativa': texto, 'modelo': modelo, 'generado_en': ahora, 'desde_cache': False}


def extraer_indicadores_para_narrativa(
    tipo_narrativa: str, analisis_completo: dict[str, Any] | None, clustering_resultado: dict[str, Any] | None,
) -> dict[str, Any]:
    """Filtra el dict completo de indicadores al subconjunto relevante para cada narrativa.

    Nunca reenvía columnas por-registro (p. ej. `pca_2d`, `pca_3d`, `clusters` de
    clustering) — solo agregados ya resumidos, para no sobrecargar el prompt ni
    exponer datos con granularidad de caso individual.

    Args:
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        analisis_completo: Resultado de `calcular_completo`, o None si no aplica.
        clustering_resultado: Resultado de `ejecutar_clustering`, o None si no aplica.

    Returns:
        Subconjunto de indicadores agregados relevante para la narrativa pedida.

    Raises:
        ValueError: Si `tipo_narrativa` es inválido, o si falta el resultado necesario.
    """
    if tipo_narrativa == 'resumen_ejecutivo':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para resumen_ejecutivo')
        claves = ['estadisticas_basicas', 'causas_cie10', 'criterios_inclusion']
        return {k: analisis_completo[k] for k in claves if k in analisis_completo}

    if tipo_narrativa == 'demoras':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para demoras')
        if 'demoras' in analisis_completo:
            return {'demoras': analisis_completo['demoras']}
        return {'tiempo_remision': analisis_completo.get('tiempo_remision', {})}

    if tipo_narrativa == 'tendencias':
        if analisis_completo is None:
            raise ValueError('Se requiere analisis_completo para tendencias')
        return {'distribucion_mensual': analisis_completo.get('distribucion_mensual', {})}

    if tipo_narrativa == 'clustering':
        if clustering_resultado is None:
            raise ValueError('Se requiere clustering_resultado para clustering')
        claves = ['n_clusters', 'n_samples', 'features_used', 'cluster_sizes', 'cluster_profiles']
        return {k: clustering_resultado[k] for k in claves if k in clustering_resultado}

    raise ValueError(f'tipo_narrativa inválido: {tipo_narrativa}')
```

- [ ] **Step 4: Correr los tests**

Run: `pytest tests/test_narrativa_service.py -v`
Expected: 5 tests PASSED.

- [ ] **Step 5: Escribir test de `extraer_indicadores_para_narrativa` (filtrado, sin arrays por-registro)**

Agregar a `BACKEND/tests/test_narrativa_service.py`:
```python
from services.narrativa_service import extraer_indicadores_para_narrativa


def test_extraer_indicadores_clustering_excluye_arrays_por_registro():
    clustering_resultado = {
        'n_clusters': 2, 'n_samples': 50, 'features_used': ['Edad'],
        'cluster_sizes': [30, 20], 'cluster_profiles': [{'cluster_id': 0, 'size': 30}],
        'pca_2d': {'x': [1, 2, 3], 'y': [4, 5, 6]}, 'clusters': [0, 1, 0],
    }
    resultado = extraer_indicadores_para_narrativa('clustering', None, clustering_resultado)
    assert 'pca_2d' not in resultado
    assert 'clusters' not in resultado
    assert resultado['n_clusters'] == 2
    assert resultado['cluster_sizes'] == [30, 20]


def test_extraer_indicadores_tipo_invalido_lanza_valueerror():
    try:
        extraer_indicadores_para_narrativa('no_existe', {}, None)
        assert False, 'Debió lanzar ValueError'
    except ValueError:
        pass
```

- [ ] **Step 6: Correr todos los tests de narrativa_service**

Run: `pytest tests/test_narrativa_service.py -v`
Expected: 7 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add BACKEND/services/narrativa_service.py BACKEND/tests/test_narrativa_service.py
git commit -m "feat: narrativa_service con cache por filtros_hash y filtrado de indicadores agregados"
```

---

### Task 10: Endpoint del router

**Files:**
- Modify: `BACKEND/api/routers/analisis.py`
- Create: `BACKEND/tests/test_analisis_router_narrativa.py`

- [ ] **Step 1: Escribir el test del endpoint**

`BACKEND/tests/test_analisis_router_narrativa.py`:
```python
"""Tests del endpoint GET /api/analisis/{pk}/narrativa/{tipo}/."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from db.database import get_db
from db.models_sqlalchemy import Analisis
from main import app


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _crear_analisis(db_session) -> Analisis:
    analisis = Analisis(
        tipo='mortalidad', nombre_archivo='test.xlsx', archivo_hash='abc123',
        archivo='media/test.xlsx', fecha_carga=datetime.now(timezone.utc),
        total_registros=5, resumen={},
    )
    db_session.add(analisis)
    db_session.commit()
    db_session.refresh(analisis)
    return analisis


def test_narrativa_devuelve_404_si_analisis_no_existe(client):
    response = client.get('/api/analisis/9999/narrativa/resumen_ejecutivo/')
    assert response.status_code == 404


def test_narrativa_devuelve_503_si_ia_service_no_disponible(client, db_session, mocker, tmp_path):
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={'estadisticas_basicas': {'total_casos': 5}, 'tipo': 'mortalidad'},
    )
    from services.ia_client import IAServiceUnavailableError
    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        side_effect=IAServiceUnavailableError('no disponible'),
    )

    response = client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    assert response.status_code == 503


def test_narrativa_devuelve_200_con_narrativa_generada(client, db_session, mocker):
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={'estadisticas_basicas': {'total_casos': 5}, 'tipo': 'mortalidad'},
    )
    mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        return_value={
            'narrativa': 'Texto de prueba.', 'modelo': 'qwen2.5',
            'generado_en': datetime.now(timezone.utc), 'desde_cache': False,
        },
    )

    response = client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    assert response.status_code == 200
    body = response.json()
    assert body['narrativa'] == 'Texto de prueba.'
    assert body['desde_cache'] is False


def test_narrativa_no_envia_columnas_identificables_a_ia_client(client, db_session, mocker):
    """Verifica que el payload hacia narrativa_service nunca incluye PII."""
    analisis = _crear_analisis(db_session)
    mocker.patch(
        'api.routers.analisis.analisis_service.calcular_completo',
        return_value={
            'estadisticas_basicas': {'total_casos': 5},
            'tipo': 'mortalidad',
            'nombre_archivo': 'test.xlsx',
        },
    )
    mock_obtener = mocker.patch(
        'api.routers.analisis.narrativa_service.obtener_narrativa',
        return_value={
            'narrativa': 'ok', 'modelo': 'qwen2.5',
            'generado_en': datetime.now(timezone.utc), 'desde_cache': False,
        },
    )

    client.get(f'/api/analisis/{analisis.id}/narrativa/resumen_ejecutivo/')

    indicadores_enviados = mock_obtener.call_args.kwargs.get('indicadores') or mock_obtener.call_args[0][3]
    campos_prohibidos = {'nombres_apellidos', 'numero_id', 'nombre_archivo', 'A. Nombres y Apellidos'}
    assert not (campos_prohibidos & set(indicadores_enviados.keys()))
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `pytest tests/test_analisis_router_narrativa.py -v`
Expected: FAIL (404 en todos, endpoint no existe todavía / primer test puede pasar por casualidad pero los demás fallan).

- [ ] **Step 3: Agregar el endpoint a `BACKEND/api/routers/analisis.py`**

Agregar el import al inicio del archivo (junto a `from services import analisis_service`):
```python
from services import analisis_service, narrativa_service
```

Y agregar al final del archivo (después del último `@router.get('/analisis/{pk}/extra-columna/')`):

```python
@router.get('/analisis/{pk}/narrativa/{tipo_narrativa}/')
def obtener_narrativa_ia(
    pk: int,
    tipo_narrativa: str,
    year: str | None = Query(default=None),
    month: str | None = Query(default=None),
    tipo_clustering: str = Query(default='kmeans'),
    n_clusters: int = Query(default=3, ge=2, le=20),
    regenerar: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Obtiene (o genera) la narrativa de IA para un análisis y tipo dados.

    Args:
        pk: ID del análisis.
        tipo_narrativa: 'resumen_ejecutivo', 'demoras', 'clustering' o 'tendencias'.
        year: Año para filtrar (opcional).
        month: Mes para filtrar (opcional).
        tipo_clustering: Algoritmo de clustering, solo relevante si tipo_narrativa='clustering'.
        n_clusters: Número de clusters, solo relevante si tipo_narrativa='clustering'.
        regenerar: Si es True, fuerza una nueva llamada a IA-SERVICE ignorando cache.
        db: Sesión de base de datos.

    Returns:
        Dict con narrativa, modelo, generado_en y desde_cache.

    Raises:
        HTTPException: 404 si el análisis no existe, 503 si IA-SERVICE no está disponible.
    """
    analisis = _get_analisis_or_404(pk, db)
    filtros: dict[str, Any] = {'year': year, 'month': month}

    with _errores_servicio():
        if tipo_narrativa == 'clustering':
            filtros.update({'tipo_clustering': tipo_clustering, 'n_clusters': n_clusters})
            clustering_resultado = analisis_service.ejecutar_clustering(analisis, tipo_clustering, n_clusters)
            indicadores = narrativa_service.extraer_indicadores_para_narrativa(
                tipo_narrativa, None, clustering_resultado,
            )
        else:
            analisis_completo = analisis_service.calcular_completo(analisis, year, month, db)
            indicadores = narrativa_service.extraer_indicadores_para_narrativa(
                tipo_narrativa, analisis_completo, None,
            )

        try:
            resultado = narrativa_service.obtener_narrativa(
                db, analisis, tipo_narrativa, indicadores, filtros, regenerar,
            )
        except IAServiceUnavailableError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return resultado
```

Agregar también el import de `Query` si no está ya en la línea de `from fastapi import ...` (verificar el import existente al inicio del archivo — ya incluye `Query` según el código actual, no duplicar) y el import de `IAServiceUnavailableError`:
```python
from services.ia_client import IAServiceUnavailableError
```

- [ ] **Step 4: Correr los tests**

Run: `pytest tests/test_analisis_router_narrativa.py -v`
Expected: 4 tests PASSED.

- [ ] **Step 5: Correr toda la suite de BACKEND**

Run (desde `BACKEND/`): `pytest tests/ -v`
Expected: todos los tests PASSED (regresión de processors + modelo + ia_client + narrativa_service + router).

- [ ] **Step 6: Commit**

```bash
git add BACKEND/api/routers/analisis.py BACKEND/tests/test_analisis_router_narrativa.py
git commit -m "feat: endpoint GET /api/analisis/{pk}/narrativa/{tipo}/ con cache y manejo de 503"
```

---

## Parte 3 — FRONTEND (TypeScript)

### Task 11: Tipos y cliente API

**Files:**
- Modify: `FRONTED/maternanalytics/src/types.ts`
- Modify: `FRONTED/maternanalytics/src/api.ts`
- Modify: `FRONTED/maternanalytics/src/api.test.ts`

- [ ] **Step 1: Agregar tipos de narrativa a `src/types.ts`**

Agregar al final del archivo:
```ts
export type TipoNarrativa = 'resumen_ejecutivo' | 'demoras' | 'clustering' | 'tendencias'

export interface FiltrosNarrativa {
  year?: string
  month?: string
  tipoClustering?: string
  nClusters?: number
}

export interface NarrativaResponse {
  narrativa: string
  modelo: string
  generado_en: string
  desde_cache: boolean
}
```

- [ ] **Step 2: Agregar `obtenerNarrativa` a `src/api.ts`**

```ts
import type { FiltrosNarrativa, NarrativaResponse, TipoNarrativa } from './types'

export const API_URL = 'http://localhost:8000/api'

export async function obtenerNarrativa(
  analisisId: number,
  tipo: TipoNarrativa,
  filtros: FiltrosNarrativa = {},
  regenerar = false,
): Promise<NarrativaResponse | null> {
  const params = new URLSearchParams()
  if (filtros.year) params.append('year', filtros.year)
  if (filtros.month) params.append('month', filtros.month)
  if (filtros.tipoClustering) params.append('tipo_clustering', filtros.tipoClustering)
  if (filtros.nClusters) params.append('n_clusters', String(filtros.nClusters))
  if (regenerar) params.append('regenerar', 'true')

  const response = await fetch(`${API_URL}/analisis/${analisisId}/narrativa/${tipo}/?${params.toString()}`)

  if (response.status === 503) return null
  if (!response.ok) throw new Error(`Error al obtener narrativa: ${response.status}`)

  return response.json() as Promise<NarrativaResponse>
}
```

- [ ] **Step 3: Escribir tests**

Agregar a `src/api.test.ts`:
```ts
import { obtenerNarrativa } from './api'

describe('obtenerNarrativa', () => {
  it('arma la URL con filtros y llama a fetch', async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ narrativa: 'texto', modelo: 'qwen2.5', generado_en: '2026-08-20', desde_cache: false }),
      } as Response)
    )
    vi.stubGlobal('fetch', fetchMock)

    const resultado = await obtenerNarrativa(1, 'resumen_ejecutivo', { year: '2026' })

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/analisis/1/narrativa/resumen_ejecutivo/?year=2026'))
    expect(resultado?.narrativa).toBe('texto')
  })

  it('devuelve null si el backend responde 503', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 503 } as Response)))

    const resultado = await obtenerNarrativa(1, 'resumen_ejecutivo')

    expect(resultado).toBeNull()
  })
})
```

Agregar `import { vi } from 'vitest'` al import existente de `vitest` en `src/api.test.ts` si no está ya.

- [ ] **Step 4: Correr los tests**

Run: `pnpm test` (desde `FRONTED/maternanalytics`)
Expected: todos PASSED.

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/types.ts FRONTED/maternanalytics/src/api.ts FRONTED/maternanalytics/src/api.test.ts
git commit -m "feat: cliente API tipado para obtener narrativas de IA"
```

---

### Task 12: Componente `NarrativaIA.tsx`

**Files:**
- Create: `FRONTED/maternanalytics/src/components/NarrativaIA.tsx`
- Create: `FRONTED/maternanalytics/src/components/NarrativaIA.test.tsx`

- [ ] **Step 1: Escribir los tests**

`src/components/NarrativaIA.test.tsx`:
```tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NarrativaIA from './NarrativaIA'
import * as api from '../api'

describe('NarrativaIA', () => {
  it('muestra el botón "Generar" en estado inicial', () => {
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)
    expect(screen.getByRole('button', { name: /generar/i })).toBeInTheDocument()
  })

  it('muestra la narrativa tras generar exitosamente', async () => {
    vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue({
      narrativa: 'Texto generado de prueba.', modelo: 'qwen2.5',
      generado_en: '2026-08-20T00:00:00Z', desde_cache: false,
    })
    const user = userEvent.setup()
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)

    await user.click(screen.getByRole('button', { name: /generar/i }))

    await waitFor(() => expect(screen.getByText('Texto generado de prueba.')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /regenerar/i })).toBeInTheDocument()
  })

  it('no renderiza nada si el backend devuelve null (503)', async () => {
    vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue(null)
    const user = userEvent.setup()
    const { container } = render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)

    await user.click(screen.getByRole('button', { name: /generar/i }))

    await waitFor(() => expect(container.querySelector('.narrativa-ia')).toBeNull())
  })

  it('el botón Regenerar vuelve a llamar a obtenerNarrativa con regenerar=true', async () => {
    const mock = vi.spyOn(api, 'obtenerNarrativa').mockResolvedValue({
      narrativa: 'Texto v1.', modelo: 'qwen2.5', generado_en: '2026-08-20T00:00:00Z', desde_cache: false,
    })
    const user = userEvent.setup()
    render(<NarrativaIA analisisId={1} tipo="resumen_ejecutivo" titulo="Resumen ejecutivo" />)
    await user.click(screen.getByRole('button', { name: /generar/i }))
    await waitFor(() => screen.getByText('Texto v1.'))

    await user.click(screen.getByRole('button', { name: /regenerar/i }))

    await waitFor(() => expect(mock).toHaveBeenLastCalledWith(1, 'resumen_ejecutivo', {}, true))
  })
})
```

- [ ] **Step 2: Correr para verificar que fallan**

Run: `pnpm test src/components/NarrativaIA.test.tsx`
Expected: FAIL, módulo no encontrado.

- [ ] **Step 3: Implementar `src/components/NarrativaIA.tsx`**

```tsx
import { useState } from 'react'
import { obtenerNarrativa } from '../api'
import type { FiltrosNarrativa, TipoNarrativa } from '../types'

interface NarrativaIAProps {
  analisisId: number
  tipo: TipoNarrativa
  titulo: string
  filtros?: FiltrosNarrativa
}

type Estado = 'idle' | 'loading' | 'success' | 'unavailable'

export default function NarrativaIA({ analisisId, tipo, titulo, filtros = {} }: NarrativaIAProps) {
  const [estado, setEstado] = useState<Estado>('idle')
  const [narrativa, setNarrativa] = useState('')

  const generar = async (regenerar: boolean) => {
    setEstado('loading')
    const resultado = await obtenerNarrativa(analisisId, tipo, filtros, regenerar)
    if (resultado === null) {
      console.debug(`NarrativaIA: IA-SERVICE no disponible para tipo=${tipo}, analisisId=${analisisId}`)
      setEstado('unavailable')
      return
    }
    setNarrativa(resultado.narrativa)
    setEstado('success')
  }

  if (estado === 'unavailable') return null

  return (
    <div className="narrativa-ia">
      <span className="ai-badge-pulsing">Inteligencia IA</span>
      <h3 className="ai-title">{titulo}</h3>

      {estado === 'idle' && (
        <button className="btn-mini-toggle" onClick={() => generar(false)}>
          Generar resumen IA
        </button>
      )}

      {estado === 'loading' && <p className="ai-no-data">Generando narrativa...</p>}

      {estado === 'success' && (
        <div className="ai-content">
          <p>{narrativa}</p>
          <button className="btn-mini-toggle" onClick={() => generar(true)}>
            Regenerar
          </button>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Correr los tests**

Run: `pnpm test src/components/NarrativaIA.test.tsx`
Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/NarrativaIA.tsx FRONTED/maternanalytics/src/components/NarrativaIA.test.tsx
git commit -m "feat: componente NarrativaIA con estados idle/loading/success/unavailable"
```

---

### Task 13: Integrar en `DashboardOKD.tsx` (reemplaza la tarjeta hardcodeada)

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/DashboardOKD.tsx`

- [ ] **Step 1: Eliminar `getAIInsight` y su uso**

En `DashboardOKD.tsx`, localizar y eliminar por completo esta función (definida dentro de `AnalysisHomeSection`; el número de línea exacto puede variar tras la migración a TS del Task 7 del plan de TypeScript, pero el contenido es este, verificado en el `.jsx` original):

```tsx
const getAIInsight = () => {
  const yearText = filterYear ? `en el año ${filterYear}` : 'en el acumulado histórico';
  const monthText = filterMonth ? `, mes ${filterMonth}` : '';

  if (segmento === 'mortalidad') {
    if (!mortalidadData || totalMortalidad === 0) {
      return <p className="ai-no-data">No hay casos de mortalidad registrados para el período seleccionado.</p>;
    }
    const cpn = mortalidadData.estadisticas_basicas?.controles_prenatales_promedio || 0;
    const topC = mortalidadData.causas_cie10?.top_causas?.[0]?.codigo || 'N/A';
    return (
      <div className="ai-content">
        <p>
          El análisis de Mortalidad Materna {yearText}{monthText} (total: <strong>{totalMortalidad}</strong> casos) detecta un promedio de <strong>{cpn.toFixed(1)}</strong> controles prenatales por caso.
        </p>
        <p>
          El principal diagnóstico asociado es <strong>{topC}</strong> ({getCie10Description(topC)}).
        </p>
        <div className="ai-recommendation-box">
          Recomendación: Ampliar cobertura prenatal en primer trimestre.
        </div>
      </div>
    );
  }

  if (segmento === 'morbilidad') {
    if (!morbilidadData || totalMorbilidad === 0) {
      return <p className="ai-no-data">No hay casos de morbilidad registrados para el período seleccionado.</p>;
    }
    const estancia = morbilidadData.estadisticas_basicas?.estancia_hospitalaria_promedio || 0;
    const crit = Object.values(morbilidadData.criterios_inclusion || {}).sort((a,b) => b.casos - a.casos)[0]?.nombre || 'Preeclampsia';
    return (
      <div className="ai-content">
        <p>
          En Morbilidad Materna Extrema {yearText}{monthText} (total: <strong>{totalMorbilidad}</strong> casos), el detonante predominante es la <strong>{crit}</strong>.
        </p>
        <p>
          La estancia promedio hospitalaria es de <strong>{estancia.toFixed(1)}</strong> días.
        </p>
        <div className="ai-recommendation-box">
          Recomendación: Reforzar guías de manejo de trastorno hipertensivo.
        </div>
      </div>
    );
  }

  // segmento === 'ambos'
  if (totalCasos === 0) {
    return <p className="ai-no-data">No hay casos registrados. Sube un archivo Excel desde el panel de carga para comenzar el análisis.</p>;
  }
  const morbCrit = morbilidadData ? Object.values(morbilidadData.criterios_inclusion || {}).sort((a,b) => b.casos - a.casos)[0]?.nombre : 'Trastornos hipertensivos';
  return (
    <div className="ai-content">
      <p>
        El diagnóstico integrado {yearText}{monthText} (<strong>{totalCasos}</strong> casos totales) reporta una <strong>tasa de letalidad del {tasaLetalidad}%</strong>.
      </p>
      <p>
        Se detectan dos perfiles de riesgo principales: pacientes obstétricas críticas ingresadas por <strong>{morbCrit}</strong> con estancia promedio prolongada, y casos de mortalidad correlacionados con fallas en la remisión oportuna.
      </p>
      <div className="ai-recommendation-box">
        Recomendación: Fortalecer red de transporte obstétrico de emergencia.
      </div>
    </div>
  );
};
```

`getCie10Description`, `totalMortalidad`, `totalMorbilidad`, `totalCasos` y `tasaLetalidad` siguen usándose en otras partes del componente (barras/paneles de estadísticas) — no eliminarlos, solo la función `getAIInsight` completa.

- [ ] **Step 2: Reemplazar el render de la tarjeta de IA**

Donde estaba:
```tsx
<div className="ai-insight-card-span-4">
  <span className="ai-badge-pulsing">Inteligencia IA</span>
  <h3 className="ai-title">Resumen de Hallazgos</h3>
  {getAIInsight()}
</div>
```

Reemplazar por (usando el patrón de import ya agregado):
```tsx
<div className="ai-insight-card-span-4">
  {segmento === 'ambos' ? (
    <>
      {latestMortalidad && (
        <NarrativaIA
          analisisId={latestMortalidad.id}
          tipo="resumen_ejecutivo"
          titulo="Resumen de Hallazgos — Mortalidad"
          filtros={{ year: filterYear || undefined, month: filterMonth || undefined }}
        />
      )}
      {latestMorbilidad && (
        <NarrativaIA
          analisisId={latestMorbilidad.id}
          tipo="resumen_ejecutivo"
          titulo="Resumen de Hallazgos — Morbilidad"
          filtros={{ year: filterYear || undefined, month: filterMonth || undefined }}
        />
      )}
    </>
  ) : (
    <NarrativaIA
      analisisId={segmento === 'mortalidad' ? latestMortalidad!.id : latestMorbilidad!.id}
      tipo="resumen_ejecutivo"
      titulo="Resumen de Hallazgos"
      filtros={{ year: filterYear || undefined, month: filterMonth || undefined }}
    />
  )}
</div>
```

- [ ] **Step 3: Agregar el import**

Al inicio de `DashboardOKD.tsx`, junto a `import AnalisisView from './AnalisisView'`:
```tsx
import NarrativaIA from './NarrativaIA'
```

- [ ] **Step 4: Verificar tipos**

Run: `npx tsc --noEmit` (desde `FRONTED/maternanalytics`)
Expected: sin errores. Si `tsc` reporta que `latestMortalidad`/`latestMorbilidad` pueden ser `null` en la rama `else`, es porque `segmento` solo puede ser `'mortalidad'`/`'morbilidad'` ahí cuando el respectivo `latest*` existe (la UI ya lo garantiza en `AnalysisHomeSection`) — el `!` non-null assertion es válido en ese punto; si `tsc` no lo acepta, envolver el bloque en un chequeo explícito `if (!latestMortalidad && !latestMorbilidad) return null` antes de este render, coherente con el resto del componente.

- [ ] **Step 5: Verificación manual**

Run: `pnpm dev` (backend e IA-SERVICE corriendo). Abrir el dashboard con al menos un análisis cargado, click en "Generar resumen IA", confirmar que aparece texto (no el placeholder fijo anterior).

- [ ] **Step 6: Commit**

```bash
git add FRONTED/maternanalytics/src/components/DashboardOKD.tsx
git commit -m "feat: reemplazar tarjeta de IA hardcodeada por NarrativaIA real en el dashboard"
```

---

### Task 14: Integrar en `AnalisisView.tsx` (demoras/tiempo_remision, tendencias, clustering)

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/AnalisisView.tsx`

- [ ] **Step 1: Pasar `analisisId`, `filterYear`, `filterMonth` a `OverviewTab`**

En el render de `AnalisisView`, cambiar:
```tsx
{activeTab === 'overview' && <OverviewTab data={data} />}
```
por:
```tsx
{activeTab === 'overview' && (
  <OverviewTab data={data} analisisId={analisisId} filterYear={filterYear} filterMonth={filterMonth} />
)}
```

- [ ] **Step 2: Actualizar `OverviewTabProps` y agregar las narrativas dentro de `OverviewTab`**

```tsx
interface OverviewTabProps {
  data: AnalisisCompleto
  analisisId: number
  filterYear?: string
  filterMonth?: string
}

function OverviewTab({ data, analisisId, filterYear, filterMonth }: OverviewTabProps) {
  const stats = data.estadisticas_basicas
  const filtros = { year: filterYear || undefined, month: filterMonth || undefined }

  return (
    <div className="overview-tab">
      {/* ... contenido existente de stats-grid sin cambios ... */}

      <NarrativaIA
        analisisId={analisisId}
        tipo={data.tipo === 'mortalidad' ? 'demoras' : 'demoras'}
        titulo={data.tipo === 'mortalidad' ? 'Interpretación de demoras' : 'Interpretación de tiempo de remisión'}
        filtros={filtros}
      />
      <NarrativaIA
        analisisId={analisisId}
        tipo="tendencias"
        titulo="Alertas de tendencias"
        filtros={filtros}
      />
    </div>
  )
}
```

Nota: `tipo="demoras"` se usa para ambos casos (mortalidad y morbilidad) — el backend ya distingue internamente en `narrativa_service.extraer_indicadores_para_narrativa` cuál campo (`demoras` o `tiempo_remision`) corresponde según `analisis.tipo`; el frontend no necesita bifurcar el `tipo_narrativa`, solo el título mostrado. Insertar el bloque `<NarrativaIA .../>` al final del `return` de `OverviewTab`, después del contenido existente (dentro del `</div>` de cierre de `overview-tab`).

- [ ] **Step 3: Pasar `analisisId` a `ClusteringTab` y agregar la narrativa ahí**

En el render de `AnalisisView`, cambiar:
```tsx
{activeTab === 'clustering' && (
  <ClusteringTab 
    data={clusteringData} 
    loading={loading}
    onGenerate={cargarClustering}
    clusterCount={clusterCount}
    setClusterCount={setClusterCount}
  />
)}
```
por:
```tsx
{activeTab === 'clustering' && (
  <ClusteringTab 
    data={clusteringData} 
    loading={loading}
    onGenerate={cargarClustering}
    clusterCount={clusterCount}
    setClusterCount={setClusterCount}
    analisisId={analisisId}
  />
)}
```

Actualizar `ClusteringTabProps` y agregar el componente dentro de `ClusteringTab` (después del contenido existente, antes del cierre del `return`):
```tsx
interface ClusteringTabProps {
  data: Record<string, unknown> | null
  loading: boolean
  onGenerate: (tipoClustering: string, nClusters: number) => void
  clusterCount: number
  setClusterCount: (n: number) => void
  analisisId: number
}

function ClusteringTab({ data, loading, onGenerate, clusterCount, setClusterCount, analisisId }: ClusteringTabProps) {
  // ... contenido existente sin cambios ...

  return (
    <div className="clustering-tab">
      {/* ... JSX existente ... */}

      {data && (
        <NarrativaIA
          analisisId={analisisId}
          tipo="clustering"
          titulo="Perfiles de clustering"
          filtros={{ nClusters: clusterCount }}
        />
      )}
    </div>
  )
}
```

Nota de ejecución: verificar el nombre exacto del `className` del contenedor raíz de `ClusteringTab` al editar (puede no ser `clustering-tab` — usar el que ya existe en el archivo real, no renombrar el contenedor).

- [ ] **Step 4: Agregar el import**

Al inicio de `AnalisisView.tsx`:
```tsx
import NarrativaIA from './NarrativaIA'
```

- [ ] **Step 5: Verificar tipos**

Run: `npx tsc --noEmit`
Expected: sin errores.

- [ ] **Step 6: Verificación manual**

Run: `pnpm dev`. Abrir un análisis, ir a la pestaña "Resumen" → botones de narrativa de demoras/tendencias visibles; ir a "Clustering" → narrativa de clustering visible tras generar el clustering.

- [ ] **Step 7: Commit**

```bash
git add FRONTED/maternanalytics/src/components/AnalisisView.tsx
git commit -m "feat: integrar NarrativaIA en pestañas de overview y clustering de AnalisisView"
```

---

## Parte 4 — Verificación final

### Task 15: Suite completa + verificación end-to-end con Ollama real

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr toda la suite de IA-SERVICE**

Run (desde `IA-SERVICE/`, venv activo): `pytest tests/ -v`
Expected: todos PASSED.

- [ ] **Step 2: Correr toda la suite de BACKEND**

Run (desde `BACKEND/`, venv activo): `pytest tests/ -v`
Expected: todos PASSED.

- [ ] **Step 3: Correr toda la suite de frontend**

Run (desde `FRONTED/maternanalytics`): `npx tsc --noEmit && pnpm test && pnpm run build`
Expected: sin errores de tipos, todos los tests PASSED, build exitoso.

- [ ] **Step 4: Verificación end-to-end manual con Ollama corriendo**

```bash
ollama serve          # si no está corriendo ya
ollama pull qwen2.5    # si no está descargado
```

En 3 terminales separadas:
```bash
# Terminal 1
cd IA-SERVICE && venv\Scripts\activate && uvicorn main:app --reload --port 8001

# Terminal 2
cd BACKEND && venv\Scripts\activate && uvicorn main:app --reload --port 8000

# Terminal 3
cd FRONTED\maternanalytics && pnpm dev
```

Con un análisis ya cargado: abrir el dashboard, click en "Generar resumen IA" → debe aparecer una narrativa coherente con los indicadores reales (no un texto fijo). Repetir en las pestañas de demoras/tendencias/clustering de `AnalisisView`.

- [ ] **Step 5: Verificación de degradación con Ollama apagado**

Detener `ollama serve`. Recargar el dashboard, click en "Generar resumen IA" → la tarjeta debe desaparecer silenciosamente (sin mensaje de error visible, sin romper el resto del dashboard). Confirmar en la consola del backend (Terminal 2) que sí quedó logueado el error 503 para depuración.

## Criterio de aceptación (verificado, no asumido)

- [ ] Con Ollama corriendo y `qwen2.5` descargado, las 4 narrativas se generan con contenido coherente a los indicadores reales.
- [ ] Con Ollama apagado, la UI se degrada sin errores visibles ni romper el resto del dashboard.
- [ ] Toda la suite de tests pasa: IA-SERVICE (pytest), BACKEND (pytest, incluyendo la red de seguridad sobre `_mortalidad_processor.py`/`_morbilidad_processor.py`), FRONTEND (vitest).
- [ ] El test `test_narrativa_no_envia_columnas_identificables_a_ia_client` confirma en código (no solo por inspección) que no se envían datos identificables al LLM.
- [ ] `npx tsc --noEmit`, `pnpm run build` y `pytest` (BACKEND e IA-SERVICE) terminan sin errores.
