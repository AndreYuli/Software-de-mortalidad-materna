# 🚀 Guía de Migración: Django a FastAPI + PostgreSQL

Este documento describe la migración del backend del **Software de Mortalidad Materna** a **FastAPI** y la base de datos a **PostgreSQL**. Se han portado todos los modelos, vistas analíticas, endpoints y el script de ingesta de archivos Excel de SIVIGILA manteniendo compatibilidad total con la lógica de negocio original.

---

## 🛠️ Enfoque de la Migración

El backend se ha estructurado en un paquete modular dentro del directorio `BACKEND/api_fastapi`:

```
BACKEND/api_fastapi/
├── __init__.py
├── auth.py              # Validación y hash de contraseñas (100% compatible con Django)
├── database.py          # Configuración dinámica de SQLAlchemy (SQLite, MySQL o Postgres)
├── database_views.py    # Recreación de vistas SQL optimizadas por dialecto (PostgreSQL, SQLite, MySQL)
├── models_sqlalchemy.py # Modelos ORM relacionales generados a partir de Django
├── schemas.py           # Modelos de validación y serialización de Pydantic V2
├── sivigila_ingestion.py# Port de ingesta de datos SIVIGILA usando SQLAlchemy Session
└── main.py              # Servidor FastAPI, endpoints REST y Middleware de CORS
```

---

## 📋 Requisitos Previos

1. Tener instalado **PostgreSQL** y un servidor corriendo localmente o en la nube.
2. Crear una base de datos vacía en PostgreSQL, por ejemplo: `sivigila_maternidad`.

---

## 🚀 Pasos para la Configuración e Inicio

### 1️⃣ Configurar variables de entorno

Edita el archivo [BACKEND/.env](file:///C:/Users/lopez/Documents/UNIVERSIDAD/Software-de-mortalidad-materna/BACKEND/.env) y cambia la configuración a PostgreSQL:

```env
DB_ENGINE=postgresql
DB_NAME=sivigila_maternidad
DB_USER=postgres
DB_PASSWORD=tu_contraseña_de_postgresql
DB_HOST=localhost
DB_PORT=5432
```

### 2️⃣ Iniciar el servidor FastAPI (Inicialización de tablas)

Ejecuta el servidor FastAPI una vez. Al arrancar, SQLAlchemy creará automáticamente todas las tablas del esquema en tu base de datos de PostgreSQL y creará las vistas SQL de forma nativa para PostgreSQL:

```powershell
# En la terminal del backend
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\BACKEND
venv\Scripts\uvicorn api_fastapi.main:app --reload --port 8000
```

*Nota: Mantén el puerto `8000` para que el frontend React (`http://localhost:5173`) pueda comunicarse sin cambios de configuración.*

### 3️⃣ Migrar los datos existentes y catálogos de SIVIGILA

Dado que la ingesta de archivos Excel SIVIGILA realiza búsquedas (lookups) en los catálogos del sistema, estos deben estar poblados. Hemos creado un script automatizado que copia todos los catálogos y datos anteriores de SQLite a PostgreSQL en orden jerárquico para no violar las restricciones de llave foránea.

Con el servidor FastAPI corriendo (lo que asegura que las tablas existen en Postgres), ejecuta:

```powershell
# Abre una nueva terminal en el backend
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\BACKEND
venv\Scripts\python migrate_data_sqlite_to_postgres.py
```

El script se encargará de:
1. Copiar los registros de todas las tablas catalogadoras, de pacientes y casos.
2. Actualizar los generadores de secuencias autoincrementales (`SERIAL`) en Postgres para evitar conflictos de llaves primarias duplicadas en futuras cargas de archivos.

---

## ⚡ Comandos de Ejecución Diarios

### Backend (FastAPI):
```powershell
cd BACKEND
venv\Scripts\uvicorn api_fastapi.main:app --reload --port 8000
```
* **Documentación Interactiva (Swagger UI)**: Accede a [http://localhost:8000/docs](http://localhost:8000/docs) para probar los endpoints y ver la documentación interactiva generada por FastAPI.
* **Documentación Alternativa (Redoc)**: Accede a [http://localhost:8000/redoc](http://localhost:8000/redoc).

### Frontend (React):
```powershell
cd FRONTED/maternanalytics
pnpm dev
```
* Disponible en [http://localhost:5173](http://localhost:5173).

---

## 💡 Notas de Implementación

* **Compatibilidad de Contraseñas**: Se utiliza `passlib` con soporte nativo de `django_pbkdf2_sha256`. Los usuarios registrados previamente en Django pueden iniciar sesión normalmente sin necesidad de restablecer su contraseña.
* **Vistas Dinámicas**: Las vistas `v_morbilidad_completa` y `v_mortalidad_completa` se generan dinámicamente. El script detecta el motor de base de datos y utiliza `EXTRACT(YEAR FROM AGE(...))` en PostgreSQL, `TIMESTAMPDIFF` en MySQL, o cálculos de fechas en SQLite, garantizando portabilidad absoluta.
