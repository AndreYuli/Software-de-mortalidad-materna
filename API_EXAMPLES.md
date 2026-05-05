# 📡 API Examples - VidaMaterna Analytics

Ejemplos de uso de los endpoints del API REST.

---

## 🔑 Base URL

```
http://localhost:8000/api
```

---

## 📤 1. Subir y Analizar Archivo

### **POST /api/subir/**

Sube un archivo Excel y valida las columnas requeridas.

**Request:**
```bash
curl -X POST http://localhost:8000/api/subir/ \
  -F "tipo=mortalidad" \
  -F "archivo=@datos_mortalidad.xlsx"
```

**Body (FormData):**
```json
{
  "tipo": "mortalidad",  // o "morbilidad"
  "archivo": <File>
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "tipo": "mortalidad",
  "nombre_archivo": "datos_mortalidad.xlsx",
  "archivo": "/media/uploads/2026/05/datos_mortalidad.xlsx",
  "fecha_carga": "2026-05-05T10:30:45.123456Z",
  "total_registros": 125,
  "resumen": {
    "distribucion_momento": {
      "Durante el embarazo": 45,
      "Durante el parto": 30,
      "Puerperio (hasta 42 días)": 40,
      "Tardía (43 días - 1 año)": 10
    },
    "top5_causas": {
      "O15": 25,
      "O72": 18,
      "O14": 15,
      "O85": 12,
      "O45": 10
    }
  }
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "error": "Faltan columnas requeridas.",
  "columnas_faltantes": [
    "10.3.1 Demora 1",
    "10.3.2 Demora 2"
  ]
}
```

---

## 📋 2. Listar Análisis

### **GET /api/analisis/**

Obtiene la lista de todos los análisis guardados.

**Request:**
```bash
curl http://localhost:8000/api/analisis/
```

**Response (200 OK):**
```json
[
  {
    "id": 3,
    "tipo": "mortalidad",
    "nombre_archivo": "datos_mortalidad_mayo.xlsx",
    "archivo": "/media/uploads/2026/05/datos_mortalidad_mayo.xlsx",
    "fecha_carga": "2026-05-05T14:22:10.123456Z",
    "total_registros": 125,
    "resumen": {}
  },
  {
    "id": 2,
    "tipo": "morbilidad",
    "nombre_archivo": "datos_morbilidad_abril.xlsx",
    "archivo": "/media/uploads/2026/04/datos_morbilidad_abril.xlsx",
    "fecha_carga": "2026-04-28T09:15:30.123456Z",
    "total_registros": 342,
    "resumen": {}
  }
]
```

---

## 📊 3. Análisis Completo

### **GET /api/analisis/{id}/completo/**

Genera análisis estadístico completo con todas las métricas.

**Request:**
```bash
curl http://localhost:8000/api/analisis/1/completo/
```

**Response (200 OK) - Mortalidad:**
```json
{
  "tipo": "mortalidad",
  "id": 1,
  "nombre_archivo": "datos_mortalidad.xlsx",
  "fecha_carga": "2026-05-05T10:30:45.123456Z",
  "estadisticas_basicas": {
    "total_casos": 125,
    "gestaciones_promedio": 2.8,
    "controles_prenatales_promedio": 4.5
  },
  "momento_muerte": {
    "distribucion": {
      "Durante el embarazo": 45,
      "Durante el parto": 30,
      "Puerperio (hasta 42 días)": 40,
      "Tardía (43 días - 1 año)": 10
    },
    "total": 125
  },
  "demoras": {
    "demora_1": {
      "nombre": "Reconocimiento del problema",
      "casos_con_demora": 78,
      "porcentaje": 62.4
    },
    "demora_2": {
      "nombre": "Decisión de buscar atención",
      "casos_con_demora": 65,
      "porcentaje": 52.0
    },
    "demora_3": {
      "nombre": "Acceso al centro de salud",
      "casos_con_demora": 92,
      "porcentaje": 73.6
    },
    "demora_4": {
      "nombre": "Calidad de atención recibida",
      "casos_con_demora": 45,
      "porcentaje": 36.0
    }
  },
  "causas_cie10": {
    "top_causas": [
      {"codigo": "O15", "casos": 25},
      {"codigo": "O72", "casos": 18},
      {"codigo": "O14", "casos": 15}
    ],
    "total_causas_unicas": 32
  }
}
```

**Response (200 OK) - Morbilidad:**
```json
{
  "tipo": "morbilidad",
  "id": 2,
  "nombre_archivo": "datos_morbilidad.xlsx",
  "fecha_carga": "2026-05-05T10:30:45.123456Z",
  "estadisticas_basicas": {
    "total_casos": 342,
    "estancia_hospitalaria_promedio": 5.8,
    "estancia_uci_promedio": 2.3,
    "criterios_promedio": 2.1
  },
  "criterios_inclusion": {
    "Eclampsia": {
      "nombre": "Eclampsia",
      "casos": 87,
      "porcentaje": 25.4
    },
    "Sepsis sistémica severa": {
      "nombre": "Sepsis",
      "casos": 65,
      "porcentaje": 19.0
    },
    "Hemorragia obstétrica severa": {
      "nombre": "Hemorragia",
      "casos": 112,
      "porcentaje": 32.7
    }
  },
  "momento_ocurrencia": {
    "distribucion": {
      "Durante el embarazo": 120,
      "Durante el parto": 98,
      "Puerperio inmediato (0-7 días)": 89,
      "Puerperio tardío (8-42 días)": 35
    }
  }
}
```

---

## 🎯 4. Clustering

### **POST /api/analisis/{id}/clustering/**

Genera análisis de clustering K-means o jerárquico.

**Request - K-means:**
```bash
curl -X POST http://localhost:8000/api/analisis/1/clustering/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_clustering": "kmeans",
    "n_clusters": 3
  }'
```

**Request - Jerárquico:**
```bash
curl -X POST http://localhost:8000/api/analisis/1/clustering/ \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_clustering": "jerarquico"
  }'
```

**Body:**
```json
{
  "tipo_clustering": "kmeans",  // o "jerarquico"
  "n_clusters": 3  // opcional, default: 3
}
```

**Response (200 OK) - K-means:**
```json
{
  "analisis_id": 1,
  "tipo_analisis": "mortalidad",
  "tipo_clustering": "kmeans",
  "n_clusters": 3,
  "n_samples": 120,
  "features_used": [
    "6.5 Gestaciones",
    "6.6 Partos Vaginales",
    "6.7 Cesáreas",
    "8.1 No. CPN",
    "9.2 Semana gestación"
  ],
  "clusters": [0, 1, 0, 2, 1, 0, 2, ...],  // Array de asignaciones
  "pca_2d": {
    "x": [-2.3, 1.5, -1.8, 3.2, ...],
    "y": [0.8, -1.2, 2.1, -0.5, ...],
    "variance_explained": 0.78  // 78% de varianza explicada
  },
  "pca_3d": {
    "x": [-2.3, 1.5, -1.8, ...],
    "y": [0.8, -1.2, 2.1, ...],
    "z": [1.1, -0.3, 0.7, ...],
    "variance_explained": 0.89  // 89% de varianza explicada
  },
  "centroids": [
    [2.8, 1.2, 0.8, 5.3, 36.2],
    [3.5, 2.1, 1.3, 6.8, 38.1],
    [1.9, 0.5, 0.2, 2.1, 32.5]
  ],
  "cluster_sizes": [45, 52, 23],
  "cluster_profiles": [
    {
      "cluster_id": 0,
      "size": 45,
      "features": {
        "6.5 Gestaciones": 2.8,
        "6.6 Partos Vaginales": 1.2,
        "6.7 Cesáreas": 0.8,
        "8.1 No. CPN": 5.3,
        "9.2 Semana gestación": 36.2
      }
    },
    {
      "cluster_id": 1,
      "size": 52,
      "features": {
        "6.5 Gestaciones": 3.5,
        "6.6 Partos Vaginales": 2.1,
        "6.7 Cesáreas": 1.3,
        "8.1 No. CPN": 6.8,
        "9.2 Semana gestación": 38.1
      }
    },
    {
      "cluster_id": 2,
      "size": 23,
      "features": {
        "6.5 Gestaciones": 1.9,
        "6.6 Partos Vaginales": 0.5,
        "6.7 Cesáreas": 0.2,
        "8.1 No. CPN": 2.1,
        "9.2 Semana gestación": 32.5
      }
    }
  ]
}
```

**Response (200 OK) - Jerárquico:**
```json
{
  "analisis_id": 1,
  "tipo_analisis": "mortalidad",
  "tipo_clustering": "jerarquico",
  "linkage_matrix": [
    [0, 5, 0.12, 2],
    [1, 8, 0.25, 2],
    [2, 15, 0.38, 3],
    ...
  ],
  "n_samples": 100,
  "method": "ward",
  "features_used": [
    "6.5 Gestaciones",
    "6.6 Partos Vaginales",
    "8.1 No. CPN"
  ]
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Datos insuficientes para clustering"
}
```

---

## 🔥 5. Heatmap de Correlación

### **GET /api/analisis/{id}/heatmap/**

Genera matriz de correlación (solo para morbilidad).

**Request:**
```bash
curl http://localhost:8000/api/analisis/2/heatmap/
```

**Response (200 OK):**
```json
{
  "analisis_id": 2,
  "columns": [
    "N° gestaciones",
    "Partos vaginales",
    "Cesáreas",
    "N° controles prenatales",
    "Edad gestacional ocurrencia (sem)",
    "Total criterios",
    "Días estancia hospitalaria"
  ],
  "correlation_matrix": [
    [1.0, 0.85, 0.72, 0.45, 0.23, 0.18, 0.12],
    [0.85, 1.0, 0.68, 0.52, 0.19, 0.25, 0.15],
    [0.72, 0.68, 1.0, 0.38, 0.14, 0.32, 0.21],
    ...
  ],
  "values": [...]  // Misma matriz que correlation_matrix
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Heatmap solo disponible para análisis de morbilidad"
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado exitosamente |
| 400 | Bad Request - Solicitud inválida |
| 404 | Not Found - Recurso no encontrado |
| 422 | Unprocessable Entity - Validación fallida |
| 500 | Internal Server Error - Error del servidor |

---

## 📝 Notas de Implementación

### **Validación de Columnas**
El endpoint `/api/subir/` valida que el archivo Excel contenga todas las columnas requeridas según el tipo:
- **Mortalidad**: 55 columnas requeridas
- **Morbilidad**: 57 columnas requeridas

### **Clustering**
- Requiere al menos `n_clusters` registros completos
- PCA reduce dimensionalidad para visualización
- El porcentaje de varianza indica qué tanta información se preserva

### **Heatmap**
- Solo disponible para análisis de morbilidad
- Calcula correlaciones de Pearson entre variables numéricas
- Útil para identificar variables redundantes o relacionadas

---

## 🔧 Testing con cURL

```bash
# Test 1: Listar análisis
curl http://localhost:8000/api/analisis/

# Test 2: Análisis completo
curl http://localhost:8000/api/analisis/1/completo/

# Test 3: Clustering
curl -X POST http://localhost:8000/api/analisis/1/clustering/ \
  -H "Content-Type: application/json" \
  -d '{"tipo_clustering": "kmeans", "n_clusters": 4}'

# Test 4: Heatmap
curl http://localhost:8000/api/analisis/2/heatmap/
```

---

## 🐍 Testing con Python

```python
import requests

BASE_URL = 'http://localhost:8000/api'

# Listar análisis
response = requests.get(f'{BASE_URL}/analisis/')
analisis = response.json()
print(f"Total de análisis: {len(analisis)}")

# Análisis completo
analisis_id = 1
response = requests.get(f'{BASE_URL}/analisis/{analisis_id}/completo/')
data = response.json()
print(f"Total casos: {data['estadisticas_basicas']['total_casos']}")

# Clustering
response = requests.post(
    f'{BASE_URL}/analisis/{analisis_id}/clustering/',
    json={'tipo_clustering': 'kmeans', 'n_clusters': 3}
)
clustering = response.json()
print(f"Clusters generados: {clustering['n_clusters']}")
print(f"Varianza explicada: {clustering['pca_3d']['variance_explained']*100:.1f}%")
```

---

## 📊 Visualización con Plotly (JavaScript)

```javascript
// Scatter 3D
const trace = {
  type: 'scatter3d',
  mode: 'markers',
  x: clusteringData.pca_3d.x,
  y: clusteringData.pca_3d.y,
  z: clusteringData.pca_3d.z,
  marker: {
    color: clusteringData.clusters,
    colorscale: 'Viridis',
    size: 6
  }
};

Plotly.newPlot('myDiv', [trace]);
```

---

**VidaMaterna Analytics API** - Documentación completa de endpoints 📡
