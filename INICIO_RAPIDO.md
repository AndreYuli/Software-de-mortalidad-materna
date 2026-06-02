# 🚀 Guía de Inicio Rápido - VidaMaterna Analytics

## ⚡ Pasos para Ejecutar el Sistema

### **1️⃣ Iniciar el Backend (Django)**

```powershell
# Navegar al directorio del backend
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\BACKEND

# Activar entorno virtual (si existe)
# .\venv\Scripts\Activate

# Instalar/actualizar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

El backend estará disponible en: **http://localhost:8000**

---

### **2️⃣ Iniciar el Frontend (React + Vite)**

```powershell
# Abrir NUEVA terminal PowerShell
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\FRONTED\maternanalytics

# Instalar dependencias (si no están instaladas)
pnpm install

# Iniciar servidor de desarrollo
pnpm dev
```

El frontend estará disponible en: **http://localhost:5173**

---

## 📊 Usar el Sistema

### **Paso 1: Subir Archivos**

1. Abre **http://localhost:5173** en tu navegador
2. Verás dos tarjetas:
   - 🔴 **MORTALIDAD** (Evento 550)
   - 🔵 **MORBILIDAD** (Evento 549)
3. Arrastra un archivo Excel o haz clic para seleccionar
4. El sistema validará automáticamente las columnas
5. Si todo está correcto, haz clic en **"Analizar"**

### **Paso 2: Ver Análisis**

1. En la lista de análisis, haz clic en cualquier tarjeta
2. Se abrirá la vista de análisis con 3 pestañas:
   - **📊 Resumen**: Estadísticas principales
   - **📈 Gráficos**: Visualizaciones interactivas
   - **🎯 Clustering**: Análisis de agrupamiento

### **Paso 3: Generar Clustering**

1. Ve a la pestaña **🎯 Clustering**
2. Selecciona el número de clusters (2-10)
3. Haz clic en **"Generar Clustering K-means"**
4. Explora los gráficos 2D y 3D:
   - **2D**: Vista simplificada
   - **3D**: Vista rotable e interactiva
5. Revisa los perfiles de cada cluster

---

## 📁 Estructura de Archivos Excel

### **Mortalidad Materna (Evento 550)**

El archivo debe contener estas columnas clave:
- `1.1 Código departamento de procedencia`
- `6.5 Gestaciones`
- `6.6 Partos Vaginales`
- `6.7 Cesáreas`
- `8.1 No. CPN` (Número de controles prenatales)
- `9.1 Momento de la muerte` (1-4)
- `9.2 Semana gestación`
- `10.1 Causa básica CIE-10`
- `10.3.1 Demora 1` (1=Sí, 2=No)
- `10.3.2 Demora 2`
- `10.3.3 Demora 3`
- `10.3.4 Demora 4`

### **Morbilidad Materna (Evento 549)**

El archivo debe contener estas columnas clave:
- `6.5 N° gestaciones`
- `6.6 Partos vaginales`
- `6.7 Cesáreas`
- `8.1 No. CPN`
- `9.1 Edad gestacional ocurrencia (sem)`
- `9.2 Momento de la ocurrencia` (1-4)
- `10.1 Eclampsia` (1=Sí, 2=No)
- `10.2 Sepsis sistémica severa`
- `10.3 Hemorragia obstétrica severa`
- `10.4 Preeclampsia`
- `10.5 Ruptura uterina`
- `12.1 Días estancia hospitalaria`

---

## 🎨 Tipos de Visualizaciones

### **📊 Pestaña Resumen**
- **Tarjetas de KPIs**: Total de casos, promedios
- **Análisis de Demoras**: 4 tipos de demoras con porcentajes
- **Criterios de Inclusión**: Grid con frecuencias

### **📈 Pestaña Gráficos**
- **Barras Verticales**: Momento de muerte/ocurrencia
- **Barras Horizontales**: Top 10 causas CIE-10
- **Gráficos de Dona**: Distribución porcentual de demoras

### **🎯 Pestaña Clustering**
- **Scatter 2D**: Visualización PCA en 2 dimensiones
- **Scatter 3D**: Visualización PCA en 3 dimensiones (rotable)
- **Perfiles de Cluster**: Características promedio por grupo
- **Varianza Explicada**: % de información preservada

---

## 🔧 Solución de Problemas

### **Error: "Faltan columnas requeridas"**
✅ **Solución**: 
- Verifica que el archivo Excel tenga todas las columnas con los nombres exactos
- Descarga la plantilla oficial del SIVIGILA
- Revisa que no haya espacios extra en los nombres de columnas

### **Error: "Todos los archivos tienen 0 registros"**
✅ **Solución**:
- Asegúrate de que el archivo tenga datos en las filas (no solo encabezados)
- Verifica que los valores numéricos sean válidos
- Elimina filas completamente vacías

### **Clustering no se genera**
✅ **Solución**:
- Necesitas al menos 3 registros completos
- Verifica que las columnas numéricas tengan valores válidos
- Intenta con un número menor de clusters

### **Frontend no carga**
✅ **Solución**:
- Verifica que el backend esté corriendo en http://localhost:8000
- Revisa la configuración de CORS en `BACKEND/config/settings.py`
- Limpia la caché del navegador (Ctrl + Shift + Delete)

### **Gráficos no se muestran**
✅ **Solución**:
- Verifica la consola del navegador (F12)
- Asegúrate de que Plotly.js esté instalado
- Refresca la página (F5)

---

## 📝 Comandos Rápidos

### **Ver logs del backend**
```powershell
cd BACKEND
python manage.py runserver
# Los logs aparecen en consola
```

### **Ver logs del frontend**
```powershell
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\FRONTED\maternanalytics
pnpm dev
# Los logs aparecen en consola y navegador (F12)
```

### **Reiniciar base de datos**
```powershell
cd BACKEND
# Eliminar base de datos
del db.sqlite3
# Recrear
python manage.py migrate
```

### **Limpiar instalación frontend**
```powershell
cd C:\Users\lopez\Documents\UNIVERSIDAD\Software-de-mortalidad-materna\FRONTED\maternanalytics
# Eliminar node_modules
rmdir /s /q node_modules
# Eliminar lockfile
del pnpm-lock.yaml
# Reinstalar
pnpm install
```

---

## 🎯 Datos de Ejemplo

Para probar el sistema, usa archivos Excel con esta estructura:

### **Mortalidad (mínimo 3 registros)**
| 6.5 Gestaciones | 6.6 Partos Vaginales | 8.1 No. CPN | 9.1 Momento de la muerte | 10.1 Causa básica CIE-10 |
|-----------------|---------------------|-------------|-------------------------|--------------------------|
| 3 | 2 | 5 | 1 | O15 |
| 2 | 1 | 3 | 2 | O72 |
| 4 | 3 | 7 | 1 | O14 |

### **Morbilidad (mínimo 3 registros)**
| 6.5 N° gestaciones | 8.1 No. CPN | 10.1 Eclampsia | 10.3 Hemorragia obstétrica severa | 12.1 Días estancia hospitalaria |
|-------------------|-------------|----------------|----------------------------------|--------------------------------|
| 2 | 4 | 1 | 2 | 5 |
| 3 | 6 | 2 | 1 | 8 |
| 1 | 2 | 1 | 1 | 12 |

---

## 📚 Recursos Adicionales

- **Documentación Técnica Completa**: [DOCS_TECNICA.md](DOCS_TECNICA.md)
- **Ejemplos de API**: [API_EXAMPLES.md](API_EXAMPLES.md)
- **Diccionario de Datos**: Ver `BACKEND/api/processors.py` líneas 10-50

---

## ✨ Funcionalidades Destacadas

1. ✅ **Validación Automática**: Verifica columnas antes de subir
2. 📊 **Análisis en Tiempo Real**: Resultados instantáneos
3. 🎯 **Clustering Inteligente**: K-means con PCA 2D/3D
4. 🔄 **Visualizaciones Interactivas**: Zoom, pan, rotación en gráficos
5. 📱 **Diseño Responsivo**: Funciona en desktop y tablet
6. 🎨 **Interfaz Moderna**: Colores institucionales, diseño limpio
7. 💾 **Persistencia de Datos**: Los archivos se guardan en la base de datos

---

## 🚀 ¡Listo para Empezar!

1. Abre **2 terminales PowerShell**
2. Terminal 1: `cd BACKEND && python manage.py runserver`
3. Terminal 2: `cd FRONTED/maternanalytics && pnpm dev`
4. Abre **http://localhost:5173** en tu navegador
5. ¡Comienza a analizar datos!

---

**VidaMaterna Analytics** - Sistema de análisis de mortalidad y morbilidad materna 🏥
