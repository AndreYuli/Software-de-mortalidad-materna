# Arquitectura

Este documento describe la arquitectura real del proyecto MaternAnalytics. Debe revisarse antes de modificar código, especialmente si la tarea afecta datos, visualizaciones, filtros, carga de archivos, autenticación o IA.

## Estructura general

```text
Software-de-mortalidad-materna/
├── backend/
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routers/
│   │       ├── analisis.py
│   │       ├── auth.py
│   │       └── sivigila.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── database.py
│   │   ├── database_views.py
│   │   └── models_sqlalchemy.py
│   ├── schemas/
│   ├── scripts/
│   ├── services/
│   │   ├── analisis_service.py
│   │   ├── sivigila_service.py
│   │   ├── narrativa_service.py
│   │   ├── ia_client.py
│   │   ├── _analisis_*.py
│   │   ├── _sivigila_*.py
│   │   ├── _mortalidad_processor.py
│   │   ├── _morbilidad_processor.py
│   │   ├── _ml_analisis.py
│   │   └── _sankey_builder.py
│   ├── tests/
│   ├── utils/
│   ├── main.py
│   ├── requirements.txt
│   └── sivigila_maternidad_postgres.sql
├── ia-service/
│   ├── core/
│   ├── prompts/
│   ├── tests/
│   ├── main.py
│   ├── ollama_client.py
│   └── requirements.txt
├── frontend/
│   └── maternanalytics/
│       ├── e2e/
│       ├── public/
│       ├── src/
│       │   ├── components/
│       │   │   ├── auth/
│       │   │   ├── dashboard/
│       │   │   ├── icons/
│       │   │   └── shared/
│       │   ├── constants/
│       │   ├── hooks/
│       │   │   ├── analysis/
│       │   │   ├── auth/
│       │   │   ├── dashboard/
│       │   │   ├── files/
│       │   │   ├── filters/
│       │   │   └── navigation/
│       │   ├── utils/
│       │   ├── validation/
│       │   ├── api.ts
│       │   ├── App.tsx
│       │   ├── main.tsx
│       │   └── types.ts
│       ├── package.json
│       └── vite.config.js
├── docs/                    # Documentación vigente
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── CONTEXTO_PROYECTO.md
│   ├── DECISIONS.md
│   ├── DESIGN.md
│   ├── PRODUCT.md
│   ├── PROMPT_CLAUDE.md
│   ├── RULES.md
│   ├── TASKS.md
│   └── historico/           # Planes y specs anteriores
├── notes/                   # Auditorías y notas de trabajo (notes/local no se versiona)
├── data/
│   ├── referencia/          # Fichas SIVIGILA 549/550 y tabla CIE-10
│   ├── pruebas/             # Excel sintéticos
│   └── local/               # No versionado: archivos de procedencia sin confirmar
├── scripts/                 # iniciar_servicios.bat, ejecutar_pruebas_e2e.bat
├── docker-compose.yml
├── .env.example
├── ruff.toml
└── README.md
```

Nota: las carpetas se llaman `backend`, `ia-service` y `frontend` (en minúscula). Se renombraron el 2026-09-20 desde `BACKEND`, `IA-SERVICE` y `FRONTED` (ver `DEC-003`). El backend y ia-service **no** usan una carpeta `app/`: importan sus paquetes de primer nivel (`from db...`, `from services...`); ver `DEC-004`.

## Servicios

| Servicio | Carpeta | Tecnología | Puerto | Responsabilidad |
|---|---|---:|---:|---|
| Frontend | `frontend/maternanalytics/` | React 18, TypeScript, Vite | 5173 | Interfaz, dashboard, carga, historial, filtros y visualizaciones |
| Backend | `backend/` | FastAPI, SQLAlchemy, pandas | 8000 | API, autenticación, carga de Excel, procesamiento, indicadores y persistencia |
| IA-SERVICE | `ia-service/` | FastAPI, httpx, Ollama | 8001 | Generación de narrativas con IA local a partir de indicadores agregados |
| PostgreSQL | externo / Docker | PostgreSQL 16 | 5432 | Base de datos relacional |
| Ollama | externo / Docker | Ollama con modelo local | 11434 | Motor LLM local para IA-SERVICE |

`docker-compose.yml` levanta PostgreSQL, Ollama, IA-SERVICE y Backend. El frontend se ejecuta aparte con Vite.

## Frontend

Framework:

**React 18 + TypeScript + Vite**

Librerías relevantes:

- `react-router-dom` para rutas.
- `react-hook-form` y `zod` para formularios y validación.
- `echarts`, `echarts-for-react` y `echarts-gl` para visualizaciones nuevas o más complejas.
- `chart.js` y `react-chartjs-2` para gráficas ya existentes.
- `xlsx` para trabajo con archivos Excel desde frontend cuando aplica.
- `vitest` y Testing Library para pruebas.
- Playwright para pruebas e2e.

### Rutas principales

Definidas en `frontend/maternanalytics/src/App.tsx`:

- `/login`
- `/register`
- `/`
- `/dashboard`
- `/cargar-mortalidad`
- `/cargar-morbilidad`
- `/historial`

Una sola ruta protegida (`ProtectedRoute`) monta `DashboardOKD` como **layout** y las vistas son rutas hijas (`DashboardViewRoute` dentro de un `<Outlet/>`), así que el layout no se remonta al navegar. `useDashboardData` vive en el layout y conserva filtros, pestañas y segmento entre rutas. La vista activa se deriva de la URL: no crear un estado paralelo de vista. Tras una carga exitosa se navega a `/dashboard`.

### Componentes principales

- **Dashboard:** `DashboardOKD.tsx`, `AnalysisHomeSection.tsx`, `ViewRouter.tsx`.
- **Gráficas:** componentes dentro de `components/dashboard/`, apoyados por hooks como `useDashboardCharts`.
- **Grafos:** el backend calcula datos tipo Sankey para flujos; su uso visual debe respetar `PRODUCT.md` y `DESIGN.md`.
- **Filtros:** `FiltersSidebar.tsx`, `FilterPanel.tsx`, `useDashboardFilters.ts`.
- **Tablas:** `UploadHistorySection.tsx` y tablas de previsualización de archivos.
- **Historial:** `UploadHistorySection.tsx`, `useUploadHistory.ts`.
- **Carga de archivos:** `UploadSection.tsx`, `UploadCard.tsx`, `useFileUpload.ts`.
- **Autenticación:** `components/auth/` (`Login.tsx`, `Register.tsx`), hooks de auth y rutas protegidas.
- **Narrativa IA:** `NarrativaIA.tsx` existe, pero debe verificarse su integración visible antes de asumir que está activa en el dashboard.

## Gestión de datos

El flujo general de datos es:

1. El usuario carga un archivo Excel de SIVIGILA 549 o 550 desde el frontend.
2. El frontend envía el archivo al backend mediante `POST /api/analisis/`.
3. El backend valida el tipo de análisis y procesa el Excel con servicios de dominio.
4. Los procesadores normalizan datos de mortalidad o morbilidad.
5. El backend guarda metadatos, historial y registros procesados en PostgreSQL.
6. El frontend consulta los análisis disponibles con endpoints como `GET /api/analisis/` y `GET /api/analisis/{pk}/completo/`.
7. Los filtros por año, mes, semana o día se envían como query params al backend.
8. El backend recalcula o devuelve indicadores filtrados.
9. El frontend transforma esos datos en KPIs, gráficas, cruces, tablas y reportes.

El cliente HTTP central está en `frontend/maternanalytics/src/api.ts`. Allí se define `API_URL`, timeout de peticiones, manejo básico de errores, historial, cruces y narrativa IA.

## Visualizaciones

Librerías utilizadas:

- **ECharts** mediante `echarts` y `echarts-for-react`.
- **Chart.js** mediante `chart.js` y `react-chartjs-2`.

Regla: no agregar una tercera librería de gráficas sin justificar claramente por qué ECharts o Chart.js no resuelven el caso.

Visualizaciones actuales o soportadas:

- KPIs generales.
- Evolución mensual.
- Principales causas CIE-10.
- Distribución por edad.
- Distribución por edad gestacional.
- Distribución por edad de riesgo.
- Distribución sociodemográfica.
- Cruce de variables sociodemográficas y clínicas.
- Demoras.
- Fallas orgánicas o severidad para morbilidad cuando existan datos.
- Sankey/flujo clínico calculado desde backend para mortalidad.

La transformación de datos para el dashboard ocurre principalmente en hooks de `src/hooks/dashboard/`, especialmente `useDashboardCharts.ts` y `useDashboardMetrics.ts`.

## Backend

El backend existe y está construido con **FastAPI + SQLAlchemy + PostgreSQL + pandas**.

Responsabilidades principales:

- recibir archivos Excel;
- validar estructura y tipo de evento;
- procesar archivos SIVIGILA 549 y 550;
- persistir análisis, historial y datos procesados;
- calcular indicadores estadísticos;
- exponer endpoints para dashboard, historial, cruces, clustering, heatmap y narrativa;
- gestionar autenticación y usuarios;
- guardar los archivos cargados en `media/` (no se sirven públicamente).

### Capas principales

```text
backend/
├── api/routers/          # Endpoints HTTP
├── core/                 # Configuración y seguridad
├── db/                   # Conexión, modelos y vistas
├── schemas/              # Schemas Pydantic
├── services/             # Lógica de negocio y procesamiento
├── utils/                # Parsers y utilidades compartidas
└── tests/                # Pruebas
```

### Endpoints relevantes de análisis

- `POST /api/analisis/`: carga y procesa archivo.
- `GET /api/analisis/`: lista análisis recientes por tipo.
- `GET /api/analisis/historial/`: historial paginado.
- `GET /api/analisis/{pk}/`: metadatos de análisis.
- `GET /api/analisis/{pk}/completo/`: indicadores y distribuciones con filtros.
- `GET /api/analisis/{pk}/cruce/`: cruces sociodemográficos y clínicos.
- `GET /api/analisis/{pk}/heatmap/`: heatmap para morbilidad.
- `POST /api/analisis/{pk}/clustering/`: clustering.
- `GET /api/analisis/{pk}/narrativa/{tipo_narrativa}/`: narrativa IA.

## IA-SERVICE

`IA-SERVICE` es un microservicio FastAPI separado. Su función es generar narrativas usando Ollama y un modelo local.

Reglas:

- recibe indicadores agregados, no registros crudos de pacientes;
- expone `GET /health` y `POST /generar-narrativa`;
- si Ollama falla, responde error controlado;
- el backend cachea narrativas en la tabla `narrativa_ia`.

No enviar datos sensibles o filas individuales de pacientes a servicios externos.

## Base de datos

Base principal:

**PostgreSQL**

El esquema base de SIVIGILA está en:

```text
backend/sivigila_maternidad_postgres.sql
```

El backend también crea tablas propias mediante SQLAlchemy al iniciar, como análisis, usuarios, importaciones y narrativas, según los modelos en `db/models_sqlalchemy.py`.

## Reglas de arquitectura

- Reutilizar componentes existentes.
- Evitar duplicación.
- Separar presentación y lógica cuando sea posible.
- No modificar la arquitectura para solucionar problemas pequeños.
- No crear nuevas dependencias sin justificar su necesidad.
- Mantener las responsabilidades de cada componente.
- No mezclar lógica de negocio dentro de componentes visuales si puede vivir en hooks, servicios o utilidades.
- No cambiar rutas, estructura de carpetas o contratos de API sin revisar el impacto completo.
- No renombrar `backend`, `ia-service` ni `frontend` sin actualizar `docker-compose.yml`, `scripts/` y `.gitignore`.
- No introducir otra librería de gráficas si ECharts o Chart.js son suficientes.
- No enviar datos crudos de pacientes a IA.
- Si cambia una decisión arquitectónica, actualizar este documento y `docs/CHANGELOG.md`.

## Deudas y riesgos conocidos

Estos puntos fueron identificados en el código y deben tenerse presentes antes de hacer cambios (la seguridad de endpoints, `/media`, `ProtectedRoute` y la duplicidad de Vitest se resolvieron; ver `docs/CHANGELOG.md`):

- La definición de tasa de letalidad debe confirmarse con el equipo antes de ajustar cálculos.
- `NarrativaIA.tsx` existe, pero su integración visible en el dashboard debe verificarse antes de asumir que el usuario puede usarla.
- El frontend no está incluido en `docker-compose.yml`; si se define despliegue con Docker completo, debe agregarse explícitamente.
