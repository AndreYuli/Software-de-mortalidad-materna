# Software de Mortalidad Materna

Sistema de análisis y visualización de datos de mortalidad materna, desarrollado con Django REST Framework (Backend) y React + Vite (Frontend).

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Python 3.8+** (recomendado: Python 3.10 o superior)
- **Node.js 16+** y **npm** (recomendado: Node.js 18 o superior)
- **Git**

## 🚀 Instalación y Configuración

### Backend (Django)

1. **Navega al directorio del backend:**

   ```bash
   cd BACKEND
   ```
2. **Crea un entorno virtual de Python:**

   ```bash
   python -m venv venv
   ```
3. **Activa el entorno virtual:**

   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
4. **Instala las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```
5. **Ejecuta las migraciones de la base de datos:**

   ```bash
   python manage.py migrate
   ```
6. **(Opcional) Crea un superusuario para acceder al admin:**

   ```bash
   python manage.py createsuperuser
   ```
7. **Inicia el servidor de desarrollo:**

   ```bash
   python manage.py runserver
   ```

   El backend estará disponible en: `http://localhost:8000`

### Frontend (React + Vite)

1. **Navega al directorio del frontend:**

   ```bash
   cd FRONTED/maternanalytics
   ```
2. **Instala las dependencias:**

   ```bash
   npm install
   ```
3. **Inicia el servidor de desarrollo:**

   ```bash
   npm run dev
   ```

   El frontend estará disponible en: `http://localhost:5173` (o el puerto que Vite asigne)

## 📁 Estructura del Proyecto

```
Software-de-mortalidad-materna/
├── BACKEND/              # API REST con Django
│   ├── api/             # Aplicación principal de la API
│   ├── config/          # Configuración de Django
│   ├── media/           # Archivos subidos por usuarios
│   ├── db.sqlite3       # Base de datos SQLite
│   ├── manage.py        # Script de gestión de Django
│   └── requirements.txt # Dependencias de Python
├── FRONTED/             # Aplicación React
│   └── maternanalytics/
│       ├── src/         # Código fuente
│       │   ├── components/  # Componentes React
│       │   ├── assets/      # Recursos estáticos
│       │   └── App.jsx      # Componente principal
│       ├── public/      # Archivos públicos
│       └── package.json # Dependencias de Node.js
└── ETL/                 # Procesos de ETL (en desarrollo)
```

## 🛠️ Tecnologías Utilizadas

### Backend

- **Django 6.0.4** - Framework web
- **Django REST Framework 3.17.1** - API REST
- **django-cors-headers** - Manejo de CORS
- **pandas 3.0.2** - Análisis de datos
- **openpyxl 3.1.5** - Procesamiento de archivos Excel
- **numpy 2.4.4** - Cálculos numéricos

### Frontend

- **React 19.2.5** - Biblioteca de UI
- **Vite 8.0.10** - Build tool y servidor de desarrollo
- **xlsx 0.18.5** - Manejo de archivos Excel
- **ESLint** - Linter de código

## 🔧 Comandos Útiles

### Backend

```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Acceder al shell de Django
python manage.py shell

# Ejecutar tests
python manage.py test
```

### Frontend

```bash
# Iniciar en modo desarrollo
npm run dev

# Construir para producción
npm run build

# Vista previa de la build de producción
npm run preview

# Ejecutar linter
npm run lint
```

## 🌐 URLs Importantes

- **Backend API:** http://localhost:8000/api/
- **Admin de Django:** http://localhost:8000/admin/
- **Frontend:** http://localhost:5173/

## � Credenciales de Acceso

### Frontend (Login)

Para acceder a la plataforma web, utiliza las siguientes credenciales por defecto:

- **Correo:** `analista@vidamaterna.gov.co`
- **Contraseña:** `VidaMaterna2025`

### Panel de Administración Django

Para acceder al panel de administración de Django (`http://localhost:8000/admin/`), primero debes crear un superusuario ejecutando:

```bash
python manage.py createsuperuser
```

Luego ingresa el nombre de usuario, correo y contraseña que prefieras.

## �📝 Notas Adicionales

- La base de datos SQLite (`db.sqlite3`) se crea automáticamente al ejecutar las migraciones
- Los archivos subidos se almacenan en el directorio `BACKEND/media/`
- Para desarrollo, ambos servidores (backend y frontend) deben estar ejecutándose simultáneamente
- El backend maneja CORS para permitir peticiones desde el frontend

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request
