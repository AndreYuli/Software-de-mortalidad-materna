# Migración completa a FastAPI + PostgreSQL — Spec de Diseño

**Fecha:** 2026-06-05

---

## Objetivo

Reemplazar Django por FastAPI como único backend. Aplicar todas las mejoras de arquitectura, rendimiento y estilo hechas en Django a la implementación FastAPI existente en `BACKEND/api_fastapi/`.

---

## Qué se elimina

- `BACKEND/api/` — app Django completa
- `BACKEND/config/` — configuración Django
- `BACKEND/manage.py`
- `BACKEND/db.sqlite3` (si existe)
- Dependencias Django de `requirements.txt`

---

## Estructura final

```
BACKEND/
├── api_fastapi/
│   ├── __init__.py
│   ├── main.py              ← HTTP puro: rutas, sin lógica de negocio
│   ├── database.py          ← SQLAlchemy engine + session + PostgreSQL
│   ├── database_views.py    ← Vistas SQL por dialecto (PG/SQLite/MySQL)
│   ├── models_sqlalchemy.py ← Modelos ORM SQLAlchemy
│   ├── schemas.py           ← Pydantic v2 schemas
│   ├── processors.py        ← Movido desde api/processors.py (limpio)
│   ├── views_constants.py   ← Constantes SIVIGILA (columnas, alias, mapping)
│   ├── sivigila_ingestion.py← Ingesta con matching flexible + fallback
│   ├── auth.py              ← Helpers bcrypt
│   └── services/
│       ├── __init__.py
│       ├── analisis_service.py  ← análisis completo, caché, extra-columna, clustering, heatmap
│       ├── upload_service.py    ← validación Excel, canonización, persistencia Analisis
│       └── auth_service.py      ← registro y autenticación de usuarios
├── requirements.txt         ← solo FastAPI + SQLAlchemy + dependencias de análisis
└── .env                     ← DB_ENGINE=postgresql (sin cambios)
```

---

## Mejoras aplicadas al FastAPI

| Mejora | Archivo destino |
|---|---|
| `processors.py` limpio (PEP 8, docstrings, sin prints) | `api_fastapi/processors.py` |
| `views_constants.py` con constantes de dominio | `api_fastapi/views_constants.py` |
| Capa de servicios separada | `api_fastapi/services/` |
| `main.py` solo con rutas HTTP | `api_fastapi/main.py` |
| Caché TTL 10 min (`cachetools.TTLCache`) | `services/analisis_service.py` |
| Parseo de fechas una sola vez por request | `services/analisis_service.py` |
| Endpoint `GET /api/analisis/{id}/extra-columna/` | `main.py` + `analisis_service.py` |
| Matching flexible de catálogos + fallback | `sivigila_ingestion.py` |
| PEP 8 estricto, comillas simples, docstrings Google | Todos los archivos |

---

## Base de datos

- Motor: **PostgreSQL** (`DB_ENGINE=postgresql` en `.env`)
- ORM: **SQLAlchemy** con `psycopg2-binary`
- Tablas `api_analisis`, `api_sivigilaimportacion`, `api_usuario`: creadas por SQLAlchemy al arrancar
- Tablas SIVIGILA (`paciente`, `caso_*`, `cat_*`): ya existen en `sivigila_maternidad`
- Vistas `v_mortalidad_completa`, `v_morbilidad_completa`: recreadas al arrancar via `database_views.py`

---

## Caching

`cachetools.TTLCache` como dict en memoria con TTL de 600 segundos (10 min). Invalidación al subir un archivo nuevo (sobrescribe la clave). Sin Redis, sin dependencias extra.

```python
from cachetools import TTLCache
_cache: TTLCache = TTLCache(maxsize=50, ttl=600)
```

---

## Arranque

```bash
cd BACKEND
venv\Scripts\uvicorn api_fastapi.main:app --reload --port 8000
```

---

## Criterios de éxito

- `uvicorn` arranca sin errores
- `GET /api/analisis/` responde 200
- Upload de `PLANTILLA Mortalidad materna.xlsx` responde 201
- `GET /api/analisis/{id}/completo/` responde en < 5s primera vez, < 0.5s segunda
- `views.py` no importa pandas ni openpyxl
- No existe ningún archivo de Django en el repo
