# Software de Mortalidad Materna

Sistema de análisis, visualización e interpretación con IA de datos de mortalidad y morbilidad materna extrema (SIVIGILA 549/550). Arquitectura de 3 servicios: **BACKEND** (FastAPI + PostgreSQL), **IA-SERVICE** (microservicio FastAPI aislado que genera narrativas con un LLM local vía Ollama) y **FRONTED** (React + TypeScript + Vite).

## 📋 Requisitos Previos

- **Python 3.10+**
- **Node.js 18+** y **pnpm** (o npm)
- **PostgreSQL 14+** corriendo localmente
- **[Ollama](https://ollama.com)** instalado, con el modelo `qwen2.5` descargado:
  ```bash
  ollama pull qwen2.5
  ```

---

## 🗄️ Configuración y Creación de la Base de Datos Local (PostgreSQL)

Para que el backend funcione correctamente, debes crear la base de datos `sivigila_maternidad` y cargar su esquema inicial. Sigue estos sencillos pasos:

### Paso 1: Crear la Base de Datos en PostgreSQL

Abre tu terminal o PowerShell y conéctate a PostgreSQL con tu usuario (generalmente `postgres`):

```bash
# Conectar a PostgreSQL con el usuario postgres
psql -U postgres
```

Dentro de la consola interactiva de PostgreSQL, ejecuta:

```sql
-- 1. Crear la base de datos
CREATE DATABASE sivigila_maternidad;

-- 2. Conectarse a la base de datos creada
\c sivigila_maternidad;
```

*(Opcional: Si usas **pgAdmin**, haz clic derecho sobre "Databases" > "Create" > "Database..." y nómbrala `sivigila_maternidad`).*

### Paso 2: Cargar el Esquema y Tablas SIVIGILA

Ejecuta el script SQL incluido en el proyecto ([`BACKEND/sivigila_maternidad_postgres.sql`](file:///C:/Users/lopez/Documents/UNIVERSIDAD/Software-de-mortalidad-materna/BACKEND/sivigila_maternidad_postgres.sql)) que contiene la estructura del dominio (tablas `paciente`, `caso_morbilidad`, `caso_mortalidad`, catálogos CIE-10 y vistas agregadas):

```bash
# Desde la raíz del proyecto (o dentro de la carpeta BACKEND)
psql -U postgres -d sivigila_maternidad -f BACKEND/sivigila_maternidad_postgres.sql
```

*(Si estás en pgAdmin: abre el "Query Tool" sobre la base de datos `sivigila_maternidad`, abre el archivo `sivigila_maternidad_postgres.sql` y presiona F5 o Ejecutar).*

---

## 🚀 Instalación y Configuración

### 1. BACKEND (FastAPI + PostgreSQL)

```bash
cd BACKEND
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

Copia `.env.example` a `.env` y coloca tu contraseña de PostgreSQL local:

```bash
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/Mac
```

Asegúrate de que el archivo `.env` en `BACKEND/.env` contenga la cadena de conexión correcta:

```env
DATABASE_URL=postgresql://postgres:TU_CONTRASEÑA@localhost:5432/sivigila_maternidad
JWT_SECRET=tu_clave_secreta_jwt_para_tokens
IA_SERVICE_URL=http://localhost:8001
MEDIA_ROOT=media/uploads
```

> **Nota:** Las tablas operativas de la aplicación (`api_analisis`, `api_usuario`, `api_sivigilaimportacion`, `narrativa_ia`) se crean automáticamente mediante SQLAlchemy la primera vez que arranca el servidor FastAPI.

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
