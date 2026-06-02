# 🏥 VidaMaterna Analytics - Documentación Técnica

## 📊 Sistema de Análisis de Mortalidad y Morbilidad Materna

Sistema completo de análisis de datos de salud materna con capacidades de clustering, visualización interactiva y procesamiento de reglas de negocio basadas en diccionarios de datos.

---

## 🎯 Funcionalidades Implementadas

### 1. **Backend (Django + scikit-learn)**

#### **Procesadores de Datos** (`api/processors.py`)
- ✅ **MortalidadProcessor**: Procesa datos de Mortalidad Materna (Evento 550)
- ✅ **MorbilidadProcessor**: Procesa datos de Morbilidad Materna Extrema (Evento 549)
- ✅ **Diccionario de Datos**: Mapeo completo de códigos a descripciones legibles
- ✅ **Reglas de Negocio**: Validación y procesamiento según estándares de salud pública

#### **Análisis Estadístico**
- 📈 Estadísticas descriptivas (promedios, totales, distribuciones)
- 🔍 Análisis de momento de muerte/ocurrencia
- ⏰ Análisis de las 4 demoras en la atención
- 📋 Top causas CIE-10
- ✅ Análisis de criterios de inclusión de morbilidad

#### **Clustering y Machine Learning**
- 🎯 **K-means Clustering**: Agrupa casos similares por factores de riesgo
- 🌳 **Clustering Jerárquico**: Dendrogramas para análisis de relaciones
- 📊 **PCA**: Reducción dimensional a 2D y 3D para visualización
- 🔥 **Heatmaps**: Matrices de correlación para análisis multivariado

#### **Endpoints API REST**

```
GET  /api/analisis/                  # Listar todos los análisis
POST /api/subir/                     # Subir y validar archivo Excel
GET  /api/analisis/<id>/             # Detalle básico de un análisis
GET  /api/analisis/<id>/completo/    # Análisis estadístico completo
POST /api/analisis/<id>/clustering/  # Generar clustering
GET  /api/analisis/<id>/heatmap/     # Matriz de correlación (morbilidad)
```

---

### 2. **Frontend (React + Plotly.js)**

#### **Componentes**
- 🏠 **Dashboard**: Carga de archivos y lista de análisis
- 📊 **AnalisisView**: Vista detallada con 3 pestañas
  - **Resumen**: Estadísticas clave y KPIs
  - **Gráficos**: Visualizaciones interactivas
  - **Clustering**: Análisis de agrupamiento 2D/3D

#### **Visualizaciones con Plotly**
- 📊 Gráficos de barras (distribuciones)
- 🥧 Gráficos de dona (demoras, porcentajes)
- 📈 Gráficos de líneas (tendencias)
- 🎯 Scatter plots 2D/3D (clustering)
- 🔥 Heatmaps (correlaciones)
- 📉 Gráficos horizontales (ranking de causas)

---

## 🚀 Instalación y Uso

### **Backend**

```bash
cd BACKEND

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

### **Frontend**

```bash
cd FRONTED/maternanalytics

# Instalar dependencias
pnpm install

# Iniciar desarrollo
pnpm dev
```

---

## 📋 Flujo de Uso

### 1. **Subir Archivos**
1. Seleccionar tipo: Mortalidad (550) o Morbilidad (549)
2. Arrastrar archivo Excel o hacer clic para seleccionar
3. Sistema valida columnas requeridas automáticamente
4. Hacer clic en "Analizar"

### 2. **Ver Análisis**
1. Hacer clic en cualquier análisis de la lista
2. Se abre vista con 3 pestañas:
   - **📊 Resumen**: KPIs principales
   - **📈 Gráficos**: Visualizaciones interactivas
   - **🎯 Clustering**: Análisis de agrupamiento

### 3. **Generar Clustering**
1. Ir a pestaña "Clustering"
2. Seleccionar número de clusters (2-10)
3. Hacer clic en "Generar Clustering K-means"
4. Ver resultados en gráficos 2D y 3D interactivos
5. Revisar perfiles de cada cluster

---

## 🔬 Análisis de Clustering

### **¿Qué analiza?**

#### **Mortalidad Materna**
Agrupa casos por:
- Número de gestaciones
- Partos vaginales/cesáreas
- Número de controles prenatales
- Semanas de gestación al momento del deceso

#### **Morbilidad Materna**
Agrupa casos por:
- Historial obstétrico
- Controles prenatales
- Edad gestacional
- Criterios de morbilidad
- Días de estancia hospitalaria

### **¿Para qué sirve?**

1. **Identificar perfiles de riesgo**: Agrupa pacientes con características similares
2. **Detectar patrones**: Encuentra relaciones no obvias entre variables
3. **Priorizar intervenciones**: Identifica grupos que requieren atención especial
4. **Análisis comparativo**: Compara características entre clusters

---

## 📊 Diccionario de Datos Implementado

### **Mortalidad Materna**

```python
MOMENTO_MUERTE = {
    1: 'Durante el embarazo',
    2: 'Durante el parto',
    3: 'Puerperio (hasta 42 días)',
    4: 'Tardía (43 días - 1 año)',
}

TIPO_PARTO = {
    1: 'Vaginal espontáneo',
    2: 'Vaginal instrumentado',
    3: 'Cesárea',
    4: 'Aborto',
}

DEMORAS = {
    'demora_1': 'Reconocimiento del problema',
    'demora_2': 'Decisión de buscar atención',
    'demora_3': 'Acceso al centro de salud',
    'demora_4': 'Calidad de atención recibida',
}
```

### **Morbilidad Materna**

```python
MOMENTO_OCURRENCIA = {
    1: 'Durante el embarazo',
    2: 'Durante el parto',
    3: 'Puerperio inmediato (0-7 días)',
    4: 'Puerperio tardío (8-42 días)',
}

CRITERIOS_INCLUSION = {
    'Eclampsia': 'Eclampsia',
    'Sepsis sistémica severa': 'Sepsis',
    'Hemorragia obstétrica severa': 'Hemorragia',
    'Preeclampsia': 'Preeclampsia severa',
    'Ruptura uterina': 'Ruptura uterina',
}
```

---

## 🎨 Tipos de Gráficos Disponibles

### **Resumen**
- 📊 Tarjetas de KPIs (total casos, promedios)
- 📋 Lista de demoras con porcentajes
- ✅ Criterios de inclusión con frecuencias

### **Gráficos**
- **Barras verticales**: Momento de muerte/ocurrencia
- **Barras horizontales**: Top 10 causas CIE-10
- **Dona**: Distribución porcentual de demoras

### **Clustering**
- **Scatter 2D**: Visualización PCA en 2 dimensiones
- **Scatter 3D**: Visualización PCA en 3 dimensiones (interactivo, rotable)
- **Perfiles**: Tarjetas con características promedio por cluster

---

## 🔧 Tecnologías Utilizadas

### **Backend**
- Django 6.0.4
- Django REST Framework 3.17.1
- pandas 3.0.2
- scikit-learn 1.6.1
- scipy 1.15.1
- openpyxl 3.1.5

### **Frontend**
- React 18
- Vite
- Plotly.js (react-plotly.js)
- XLSX (SheetJS)

---

## 📈 Próximos Pasos Sugeridos

1. **Más tipos de clustering**:
   - DBSCAN (clustering basado en densidad)
   - Gaussian Mixture Models
   
2. **Análisis temporal**:
   - Tendencias a lo largo del tiempo
   - Predicción de casos futuros

3. **Exportación de reportes**:
   - PDF con gráficos
   - Excel con resultados de clustering

4. **Filtros avanzados**:
   - Por rango de fechas
   - Por región geográfica
   - Por institución

5. **Dashboard en tiempo real**:
   - Actualización automática
   - Alertas de casos críticos

---

## 📝 Notas Técnicas

### **PCA (Principal Component Analysis)**
- Reduce dimensionalidad manteniendo máxima varianza
- Facilita visualización de datos multidimensionales
- Los porcentajes indican qué tanta información se preserva

### **K-means**
- Algoritmo iterativo que agrupa por similitud
- Requiere especificar número de clusters a priori
- Sensible a valores atípicos

### **Clustering Jerárquico**
- Crea dendrograma con relaciones jerárquicas
- Útil para determinar número óptimo de clusters
- Más computacionalmente costoso

---

## 🐛 Troubleshooting

### **Error: "Datos insuficientes para clustering"**
- Verificar que el archivo tenga al menos 3 registros completos
- Revisar que las columnas numéricas tengan valores válidos

### **Gráficos no se muestran**
- Verificar que Plotly esté instalado: `pnpm list react-plotly.js`
- Limpiar caché del navegador

### **Backend no responde**
- Verificar que Django esté corriendo: `python manage.py runserver`
- Revisar configuración CORS en `settings.py`

---

## 👥 Contacto

Para preguntas o soporte técnico, contactar al equipo de desarrollo.

---

**VidaMaterna Analytics** - Sistema de análisis avanzado de datos de salud materna 🏥
