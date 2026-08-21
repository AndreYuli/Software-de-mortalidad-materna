# Software de Mortalidad Materna

Sistema de análisis, visualización e interpretación con IA de datos de mortalidad y morbilidad materna extrema (SIVIGILA 549/550). Arquitectura de 3 servicios: **BACKEND** (FastAPI + PostgreSQL), **IA-SERVICE** (microservicio FastAPI aislado que genera narrativas con un LLM local vía Ollama) y **FRONTED** (React + TypeScript + Vite).

## 📋 Requisitos Previos

- **Python 3.10+**
- **Node.js 18+** y **pnpm**
- **PostgreSQL** (corriendo localmente, con la base `sivigila_maternidad` ya creada — ver `BACKEND/sivigila_maternidad_postgres.sql`)
- **[Ollama](https://ollama.com)** instalado, con el modelo `qwen2.5` descargado:
  ```bash
  ollama pull qwen2.5
  ```

## 🚀 Instalación

### 1. BACKEND (FastAPI + PostgreSQL)

```bash
cd BACKEND
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y ajusta las credenciales de tu PostgreSQL local:

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/Mac
```

Las tablas propias de la API (`api_analisis`, `api_usuario`, `api_sivigilaimportacion`, `narrativa_ia`) se crean automáticamente al arrancar el servidor. Las tablas del dominio SIVIGILA (`paciente`, `caso_morbilidad`, `caso_mortalidad`, catálogos, vistas) deben crearse una vez ejecutando `sivigila_maternidad_postgres.sql` contra tu base.

### 2. IA-SERVICE (microservicio de IA generativa)

```bash
cd IA-SERVICE
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

No requiere `.env` — por defecto apunta a Ollama en `http://localhost:11434` con el modelo `qwen2.5` (configurable en `IA-SERVICE/core/config.py` o variables de entorno `OLLAMA_HOST`/`OLLAMA_MODEL`/`OLLAMA_TIMEOUT_S`).

### 3. FRONTED (React + TypeScript + Vite)

```bash
cd FRONTED/maternanalytics
pnpm install
```

## ▶️ Ejecución (desarrollo)

Se necesitan **4 procesos corriendo en paralelo**, cada uno en su propia terminal:

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — IA-SERVICE (puerto 8001)
cd IA-SERVICE
venv\Scripts\activate
uvicorn main:app --reload --port 8001

# Terminal 3 — BACKEND (puerto 8000)
cd BACKEND
venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 4 — FRONTED (puerto 5173)
cd FRONTED/maternanalytics
pnpm dev
```

Abre **http://localhost:5173** en el navegador.

Si Ollama o IA-SERVICE no están corriendo, el resto de la aplicación sigue funcionando con normalidad — las tarjetas de narrativa de IA simplemente se ocultan (degradación silenciosa, por diseño).

## 🔑 Credenciales de prueba

No hay usuarios por defecto en la base de datos: hay que registrarlos. Puedes crear uno desde la pantalla de registro del frontend, o por API:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Usuario Prueba","email":"prueba@vidamaterna.co","password":"prueba123"}'
```

Ya existe un usuario de prueba creado en la base de datos local durante la verificación de este proyecto:

- **Correo:** `prueba@vidamaterna.co`
- **Contraseña:** `prueba123`

(Válido solo si usas la misma base PostgreSQL local en la que se creó — en una base nueva, regístrate primero.)

## 📁 Estructura del Proyecto

```
Software-de-mortalidad-materna/
├── BACKEND/                    # API FastAPI + PostgreSQL
│   ├── api/routers/            # Endpoints HTTP (auth, sivigila, analisis)
│   ├── core/                   # Configuración y seguridad (JWT)
│   ├── db/                     # Modelos SQLAlchemy y conexión
│   ├── schemas/                # Schemas Pydantic
│   ├── services/                # Lógica de negocio (procesamiento, clustering, IA)
│   ├── tests/                  # pytest
│   ├── media/uploads/          # Archivos Excel subidos
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── requirements.txt
│   └── sivigila_maternidad_postgres.sql
├── IA-SERVICE/                 # Microservicio de IA generativa (FastAPI, aislado)
│   ├── prompts/                # Plantillas de prompt por tipo de narrativa
│   ├── core/                   # Configuración (Ollama host/modelo)
│   ├── tests/                  # pytest
│   ├── main.py                 # Endpoint POST /generar-narrativa
│   ├── ollama_client.py
│   └── requirements.txt
└── FRONTED/maternanalytics/    # React + TypeScript + Vite
    ├── src/
    │   ├── components/         # Login, Register, DashboardOKD, AnalisisView, NarrativaIA
    │   ├── api.ts               # Cliente HTTP tipado
    │   └── types.ts             # Tipos de dominio compartidos
    └── package.json
```

## 🧪 Tests

```bash
# BACKEND
cd BACKEND && venv\Scripts\activate && pytest tests/ -v

# IA-SERVICE
cd IA-SERVICE && venv\Scripts\activate && pytest tests/ -v

# FRONTED
cd FRONTED/maternanalytics && npx tsc --noEmit && pnpm test && pnpm run build
```

## 🛠️ Tecnologías

| Capa | Stack |
|---|---|
| BACKEND | FastAPI, SQLAlchemy, PostgreSQL, pandas, scikit-learn, JWT |
| IA-SERVICE | FastAPI, httpx, Ollama (`qwen2.5`) |
| FRONTED | React 18, TypeScript, Vite, Plotly.js, vitest |

## 📝 Notas

- El backend nunca envía datos crudos de pacientes a IA-SERVICE — solo indicadores ya agregados (totales, promedios, distribuciones). Ver `BACKEND/services/narrativa_service.py::extraer_indicadores_para_narrativa`.
- Las narrativas generadas se cachean en la tabla `narrativa_ia` (por análisis + tipo + filtros); el botón "Regenerar" fuerza una nueva llamada al LLM.
- CORS ya está configurado en el backend para `http://localhost:5173`.
