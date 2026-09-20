# FastAPI/PostgreSQL Migration Cleanup - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar todo el código y dependencias de Django y MySQL del backend, dejando únicamente FastAPI + PostgreSQL.

**Architecture:** Primero mover `api/processors.py` (sin deps Django) a `api_fastapi/processors.py`, luego borrar los directorios Django (`api/`, `config/`), limpiar `requirements.txt` y eliminar referencias MySQL de los módulos FastAPI.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PostgreSQL (psycopg2-binary), Pydantic V2, Pandas

---

### Task 1: Mover processors.py a api_fastapi y actualizar import

**Contexto:** `api_fastapi/main.py:52` importa `from api.processors import ...`. El archivo `api/processors.py` no tiene ninguna dependencia de Django (solo numpy, pandas, sklearn, scipy), por lo que se puede copiar directamente.

**Files:**
- Create: `BACKEND/api_fastapi/processors.py`
- Modify: `BACKEND/api_fastapi/main.py:52-57`

- [ ] **Step 1: Copiar processors.py a api_fastapi/**

  Crear `BACKEND/api_fastapi/processors.py` con el contenido idéntico de `BACKEND/api/processors.py`.

- [ ] **Step 2: Actualizar import en main.py**

  En `BACKEND/api_fastapi/main.py`, cambiar las líneas 52-57:

  ```python
  # ANTES (línea 52-57):
  from api.processors import (
      MortalidadProcessor,
      MorbilidadProcessor,
      preparar_dataframe_analisis,
      es_valor_positivo,
  )

  # DESPUÉS:
  from .processors import (
      MortalidadProcessor,
      MorbilidadProcessor,
      preparar_dataframe_analisis,
      es_valor_positivo,
  )
  ```

- [ ] **Step 3: Verificar que FastAPI inicia sin errores**

  ```
  cd BACKEND
  venv\Scripts\python -c "from api_fastapi.main import app; print('OK')"
  ```
  Expected: `OK` sin ImportError.

- [ ] **Step 4: Commit**

  ```bash
  git add BACKEND/api_fastapi/processors.py BACKEND/api_fastapi/main.py
  git commit -m "refactor: move processors.py to api_fastapi, remove Django import"
  ```

---

### Task 2: Eliminar soporte MySQL de api_fastapi/database.py

**Contexto:** `BACKEND/api_fastapi/database.py` tiene un branch `elif DB_ENGINE == 'mysql'` (líneas 20-26) que construye una URL `mysql+pymysql://`. Se elimina ese branch.

**Files:**
- Modify: `BACKEND/api_fastapi/database.py:20-26`

- [ ] **Step 1: Eliminar branch MySQL**

  Reemplazar el bloque actual:

  ```python
  if DB_ENGINE in ('postgresql', 'postgres'):
      DB_USER = os.getenv('DB_USER', 'postgres')
      DB_PASSWORD = os.getenv('DB_PASSWORD', '')
      DB_HOST = os.getenv('DB_HOST', 'localhost')
      DB_PORT = os.getenv('DB_PORT', '5432')
      DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
      DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  elif DB_ENGINE == 'mysql':
      DB_USER = os.getenv('DB_USER', 'root')
      DB_PASSWORD = os.getenv('DB_PASSWORD', '')
      DB_HOST = os.getenv('DB_HOST', 'localhost')
      DB_PORT = os.getenv('DB_PORT', '3306')
      DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
      DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  else:
      # Default to sqlite
      sqlite_path = BASE_DIR / 'db.sqlite3'
      DATABASE_URL = f"sqlite:///{sqlite_path}"
  ```

  Con:

  ```python
  if DB_ENGINE in ('postgresql', 'postgres'):
      DB_USER = os.getenv('DB_USER', 'postgres')
      DB_PASSWORD = os.getenv('DB_PASSWORD', '')
      DB_HOST = os.getenv('DB_HOST', 'localhost')
      DB_PORT = os.getenv('DB_PORT', '5432')
      DB_NAME = os.getenv('DB_NAME', 'sivigila_maternidad')
      DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  else:
      sqlite_path = BASE_DIR / 'db.sqlite3'
      DATABASE_URL = f"sqlite:///{sqlite_path}"
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add BACKEND/api_fastapi/database.py
  git commit -m "refactor: remove MySQL support from database.py, keep PostgreSQL/SQLite only"
  ```

---

### Task 3: Eliminar dialecto MySQL de api_fastapi/database_views.py

**Contexto:** `BACKEND/api_fastapi/database_views.py:11-13` tiene un branch `elif "mysql" in dialect` que usa `TIMESTAMPDIFF`. Se elimina.

**Files:**
- Modify: `BACKEND/api_fastapi/database_views.py:8-17`

- [ ] **Step 1: Eliminar branch MySQL en cálculo de edad**

  Reemplazar:

  ```python
  if "postgresql" in dialect or "postgres" in dialect:
      edad_morbilidad = "EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer"
      edad_mortalidad = "EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer"
  elif "mysql" in dialect:
      edad_morbilidad = "TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, c.fecha_egreso)"
      edad_mortalidad = "TIMESTAMPDIFF(YEAR, p.fecha_nacimiento, c.fecha_defuncion)"
  else:
      # SQLite dialect
      edad_morbilidad = "CAST(strftime('%Y', c.fecha_egreso) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_egreso) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"
      edad_mortalidad = "CAST(strftime('%Y', c.fecha_defuncion) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_defuncion) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"
  ```

  Con:

  ```python
  if "postgresql" in dialect or "postgres" in dialect:
      edad_morbilidad = "EXTRACT(YEAR FROM AGE(c.fecha_egreso, p.fecha_nacimiento))::integer"
      edad_mortalidad = "EXTRACT(YEAR FROM AGE(c.fecha_defuncion, p.fecha_nacimiento))::integer"
  else:
      # SQLite dialect (fallback para desarrollo local)
      edad_morbilidad = "CAST(strftime('%Y', c.fecha_egreso) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_egreso) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"
      edad_mortalidad = "CAST(strftime('%Y', c.fecha_defuncion) - strftime('%Y', p.fecha_nacimiento) - (strftime('%m-%d', c.fecha_defuncion) < strftime('%m-%d', p.fecha_nacimiento)) AS INTEGER)"
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add BACKEND/api_fastapi/database_views.py
  git commit -m "refactor: remove MySQL SQL dialect from database_views.py"
  ```

---

### Task 4: Limpiar requirements.txt

**Contexto:** El archivo actual mezcla dependencias Django y FastAPI. Eliminar: Django, djangorestframework, django-cors-headers, asgiref, sqlparse, PyMySQL, six (todos innecesarios para FastAPI+PostgreSQL).

**Files:**
- Modify: `BACKEND/requirements.txt`

- [ ] **Step 1: Reescribir requirements.txt**

  Nuevo contenido de `BACKEND/requirements.txt`:

  ```
  numpy==2.4.4
  openpyxl==3.1.5
  et_xmlfile==2.0.0
  pandas==3.0.2
  python-dotenv==1.1.1
  python-dateutil==2.9.0.post0
  scikit-learn==1.6.1
  scipy==1.15.1
  tzdata==2026.2
  fastapi==0.111.0
  uvicorn==0.30.1
  sqlalchemy==2.0.30
  pydantic==2.7.4
  email-validator==2.1.1
  psycopg2-binary==2.9.9
  python-multipart==0.0.9
  passlib[bcrypt]==1.7.4
  ```

  Eliminados: `Django`, `djangorestframework`, `django-cors-headers`, `asgiref`, `sqlparse`, `PyMySQL`, `six`

- [ ] **Step 2: Commit**

  ```bash
  git add BACKEND/requirements.txt
  git commit -m "chore: remove Django and MySQL dependencies from requirements.txt"
  ```

---

### Task 5: Eliminar directorios Django

**Contexto:** `BACKEND/api/` (app Django completa), `BACKEND/config/` (settings/urls Django) y `BACKEND/manage.py` son código muerto — FastAPI no los usa. Esto solo puede hacerse DESPUÉS del Task 1 (processors.py ya está en api_fastapi/).

**Files:**
- Delete: `BACKEND/api/` (directorio completo)
- Delete: `BACKEND/config/` (directorio completo)
- Delete: `BACKEND/manage.py`

- [ ] **Step 1: Borrar directorios Django**

  ```powershell
  Remove-Item -Recurse -Force "BACKEND\api"
  Remove-Item -Recurse -Force "BACKEND\config"
  Remove-Item -Force "BACKEND\manage.py"
  ```

- [ ] **Step 2: Verificar que FastAPI sigue funcionando**

  ```
  venv\Scripts\python -c "from api_fastapi.main import app; print('OK')"
  ```
  Expected: `OK`

- [ ] **Step 3: Commit**

  ```bash
  git add -A
  git commit -m "chore: remove Django app (api/), config/ and manage.py — migration complete"
  ```

---

### Task 6: Limpiar .env.example y credenciales hardcodeadas

**Contexto:** `.env.example` aún referencia MySQL. `migrate_data_mysql_to_postgres.py` tiene credenciales hardcodeadas (`root`/`1212`).

**Files:**
- Modify: `BACKEND/.env.example`
- Modify: `BACKEND/migrate_data_mysql_to_postgres.py`

- [ ] **Step 1: Actualizar .env.example a solo PostgreSQL**

  Nuevo contenido de `BACKEND/.env.example`:

  ```env
  DB_ENGINE=postgresql
  DB_NAME=sivigila_maternidad
  DB_USER=postgres
  DB_PASSWORD=tu_password
  DB_HOST=localhost
  DB_PORT=5432
  ```

- [ ] **Step 2: Reemplazar credenciales hardcodeadas en migrate_data_mysql_to_postgres.py**

  Buscar las líneas con credenciales MySQL hardcodeadas (user=`root`, password=`1212`) y reemplazar con `os.getenv()`:

  ```python
  # ANTES (aproximado):
  MYSQL_USER = 'root'
  MYSQL_PASSWORD = '1212'
  MYSQL_HOST = 'localhost'
  MYSQL_PORT = 3306
  MYSQL_DB = 'maternidad'

  # DESPUÉS:
  import os
  from dotenv import load_dotenv
  load_dotenv()
  MYSQL_USER = os.getenv('MYSQL_USER', 'root')
  MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
  MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
  MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
  MYSQL_DB = os.getenv('MYSQL_DB', 'maternidad')
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add BACKEND/.env.example BACKEND/migrate_data_mysql_to_postgres.py
  git commit -m "chore: remove hardcoded MySQL credentials, update .env.example to PostgreSQL-only"
  ```
