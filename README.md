# Software de Mortalidad Materna (MaternAnalytics)

Sistema de análisis, visualización e interpretación con IA de datos de mortalidad y morbilidad materna extrema (fichas SIVIGILA 549 y 550). Una persona de la Secretaría de Salud carga los archivos Excel, y el sistema los valida, los procesa y los muestra en un dashboard con indicadores, filtros, historial de cargas y narrativas generadas por IA local.

## Arquitectura

Tres servicios más PostgreSQL y Ollama:

| Servicio | Carpeta | Tecnología | Puerto |
|---|---|---|---:|
| Frontend | `frontend/maternanalytics/` | React 18, TypeScript, Vite | 5173 |
| Backend | `backend/` | FastAPI, SQLAlchemy, pandas, scikit-learn, JWT | 8000 |
| IA-SERVICE | `ia-service/` | FastAPI, httpx, Ollama (`qwen2.5`) | 8001 |
| PostgreSQL | externo o Docker | PostgreSQL 16 | 5432 |
| Ollama | externo o Docker | LLM local | 11434 |

- Todos los endpoints de datos (`/api/analisis/*`, `/api/sivigila/*`) exigen un JWT válido. Solo son públicos el login, el registro y `/health`. Los archivos cargados (`backend/media/`) no se sirven públicamente.
- El backend nunca envía datos crudos de pacientes al servicio de IA: solo indicadores ya agregados. Ver `backend/services/narrativa_service.py`.
- Si Ollama o `ia-service` no están disponibles, el resto de la aplicación sigue funcionando y las narrativas se ocultan.

Documentación detallada en [`docs/`](docs/): [arquitectura](docs/ARCHITECTURE.md), [producto](docs/PRODUCT.md), [diseño](docs/DESIGN.md), [reglas](docs/RULES.md), [decisiones](docs/DECISIONS.md), [tareas](docs/TASKS.md) y [changelog](docs/CHANGELOG.md).

## Estructura de carpetas

```text
Software-de-mortalidad-materna/
├── backend/            # API FastAPI (api/, core/, db/, schemas/, services/, utils/, scripts/, tests/)
├── ia-service/         # Microservicio de narrativas (core/, prompts/, tests/)
├── frontend/
│   └── maternanalytics/
│       ├── src/        # components/{auth,dashboard,icons,shared}, hooks/, utils/, api.ts, types.ts
│       └── e2e/        # Pruebas end-to-end (Playwright)
├── docs/               # Documentación vigente (docs/historico: planes y specs anteriores)
├── notes/              # Auditorías y notas de trabajo (notes/local no se versiona)
├── data/
│   ├── referencia/     # Fichas SIVIGILA 549/550 y tabla de referencia CIE-10
│   ├── pruebas/        # Excel sintéticos para probar la carga
│   └── local/          # No se versiona
├── scripts/            # iniciar_servicios.bat, ejecutar_pruebas_e2e.bat
├── docker-compose.yml
├── .env.example        # Variables para docker compose
└── ruff.toml           # Estilo Python (comillas simples)
```

## Requisitos

- **Python 3.11+**
- **Node.js 18+** y **pnpm**
- **PostgreSQL 14+** (o Docker)
- **[Ollama](https://ollama.com)** con el modelo `qwen2.5`: `ollama pull qwen2.5`
- Opcional: **Docker Desktop** para levantar todo con `docker compose`

## Variables de entorno

**Backend** (`backend/.env`, copiar desde `backend/.env.example`):

| Variable | Descripción | Por defecto |
|---|---|---|
| `DB_ENGINE`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT` | Conexión a PostgreSQL | `postgresql`, `postgres`, `password`, `sivigila_maternidad`, `localhost`, `5432` |
| `JWT_SECRET` | Clave de firma de los tokens. **Cámbiala fuera de desarrollo.** | valor de ejemplo |
| `JWT_ALGORITHM`, `JWT_EXPIRATION_MINUTES` | Algoritmo y vigencia del token | `HS256`, `60` |
| `IA_SERVICE_URL` | URL de `ia-service` | `http://localhost:8001` |
| `CORS_ORIGINS` | Orígenes permitidos, separados por comas | `localhost:5173/5174` |

**ia-service** (opcionales): `OLLAMA_HOST` (`http://localhost:11434`), `OLLAMA_MODEL` (`qwen2.5`), `OLLAMA_TIMEOUT_S` (`30`).

**Frontend** (`frontend/maternanalytics/.env.local`, opcional): `VITE_API_URL` (por defecto `http://localhost:8000/api`).

**Docker** (`.env` en la raíz, copiar desde `.env.example`): `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `CORS_ORIGINS`. Los archivos `.env` nunca se versionan.

## Instalación y ejecución local

### 1. Base de datos

```bash
psql -U postgres -c "CREATE DATABASE sivigila_maternidad;"
psql -U postgres -d sivigila_maternidad -f backend/sivigila_maternidad_postgres.sql
```

Las tablas propias de la aplicación (`api_analisis`, `api_usuario`, `api_sivigilaimportacion`, `narrativa_ia`) se crean solas al arrancar el backend.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # y edita DB_PASSWORD y JWT_SECRET
uvicorn main:app --reload --port 8000
```

### 3. ia-service

```bash
cd ia-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 4. Frontend

```bash
cd frontend/maternanalytics
pnpm install
pnpm dev
```

Abre **http://localhost:5173**. Vite hace de proxy de `/api` hacia `localhost:8000`.

En Windows, `scripts\iniciar_servicios.bat` abre las terminales de Ollama, ia-service, backend, frontend y ngrok (necesita los `venv` ya creados).

### Primer usuario

No hay usuarios por defecto. Regístrate desde la pantalla de registro, o por API:

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Tu Nombre","email":"tu@correo.co","password":"una-clave-segura"}'
```

## Docker

```bash
copy .env.example .env         # define DB_USER, DB_PASSWORD, JWT_SECRET y CORS_ORIGINS
docker compose up -d --build
docker exec maternidad_ollama ollama pull qwen2.5    # solo la primera vez
```

Levanta PostgreSQL (carga el esquema SQL), Ollama, ia-service y backend, todos publicados solo en `127.0.0.1`. El frontend no está en el compose: se ejecuta aparte con `pnpm dev` (o se sirve construido con `pnpm build`).

## Pruebas

```bash
# Backend (67 tests)
cd backend && venv\Scripts\activate && pip install pytest pytest-mock && pytest tests/ -v

# ia-service (18 tests)
cd ia-service && venv\Scripts\activate && pytest tests/ -v

# Frontend: tipos, lint, tests unitarios y build
cd frontend/maternanalytics
npx tsc --noEmit
pnpm lint
pnpm test
pnpm build
```

**End-to-end (Playwright):** requiere backend y frontend en marcha y los Excel de `frontend/maternanalytics/e2e/fixtures/` (no se versionan). Ejecuta `scripts\ejecutar_pruebas_e2e.bat`.

**Estilo Python:** `ruff` con comillas simples, configurado en `backend/pyproject.toml` y `ruff.toml`. Se aplica con pre-commit: `pip install pre-commit ruff` y `pre-commit install --config backend/.pre-commit-config.yaml`.

## Datos de referencia y de prueba

- `data/referencia/`: fichas oficiales 549 y 550 (md y pdf) y `TablaReferencia_CIE10__1.xlsx`. Con la tabla se regenera el catálogo del frontend: `python backend/scripts/generate_cie10_reference.py`.
- `data/pruebas/`: Excel sintéticos. Se regeneran con `python backend/scripts/generar_excels_prueba.py` y `generar_datos_sinteticos_fase0.py`.
- No subas al repositorio archivos con datos reales de pacientes.

## Acceso público (ngrok)

Para compartir el frontend fuera de tu red se expone el puerto 5173 con [ngrok](https://ngrok.com) (`winget install Ngrok.Ngrok`, `ngrok config add-authtoken <token>` y un túnel `frontend` hacia `addr: 5173` en `%LOCALAPPDATA%\ngrok\ngrok.yml`). Después: `ngrok start --all` (ya incluido en `scripts\iniciar_servicios.bat`). Vite hace de proxy hacia el backend, así que solo se expone un puerto. En el plan gratuito solo puede haber un túnel activo (`ERR_NGROK_334` significa que ya hay otro `ngrok.exe`).
