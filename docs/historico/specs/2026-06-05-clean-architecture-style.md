# Clean Architecture + Estilo PEP 8 — Spec de Diseño

**Fecha:** 2026-06-05  
**Alcance:** Todos los archivos Python en `BACKEND/api/`

---

## Objetivo

Refactorizar el backend Django para:

1. Separar responsabilidades en capas claras (HTTP / servicios / dominio / persistencia).
2. Aplicar PEP 8 estricto, comillas simples, docstrings Google y comentarios de lógica de negocio en todos los archivos.

---

## Arquitectura de capas

```
BACKEND/api/
├── views.py                  ← HTTP únicamente: parsear request, delegar, retornar Response
├── urls.py                   ← routing de URLs
├── models.py                 ← modelos ORM de la aplicación
├── serializers.py            ← serializadores DRF
├── processors.py             ← análisis estadístico y ML sobre DataFrames
├── sivigila_models.py        ← modelos ORM de tablas SIVIGILA (unmanaged)
├── sivigila_ingestion.py     ← persistencia de filas SIVIGILA en BD
├── apps.py                   ← configuración de la app Django
└── services/
    ├── __init__.py
    ├── analisis_service.py   ← carga, caché y construcción de resultados de análisis
    ├── upload_service.py     ← validación de Excel, procesamiento de df, guardado
    └── auth_service.py       ← registro y autenticación de usuarios
```

### Responsabilidades por capa

| Capa | Hace | No hace |
|---|---|---|
| `views.py` | Parsear request, llamar servicio, retornar `Response` | No toca pandas, no lee Excel, no calcula |
| `services/` | Lógica de negocio: leer Excel, cachear, construir resultados | No sabe nada de HTTP ni de `request` |
| `processors.py` | Análisis estadístico y clustering sobre DataFrame | No accede a BD ni a archivos |
| `sivigila_ingestion.py` | Persistir filas SIVIGILA en BD | No analiza ni serializa para HTTP |

---

## Contenido de cada servicio

### `services/upload_service.py`

Funciones públicas:

| Función | Responsabilidad |
|---|---|
| `validar_columnas_excel(archivo, tipo)` | Lee headers del Excel, devuelve lista de columnas faltantes |
| `leer_dataframe_excel(archivo, tipo)` | Lee el Excel completo y canoniza nombres de columnas |
| `procesar_carga_archivo(tipo, archivo)` | Orquesta: validar → leer df → persistir SIVIGILA → guardar Analisis |

Retorna `(data_dict, http_status_code)` para que `views.py` solo haga `return Response(data, status=http_status)`.

### `services/analisis_service.py`

Funciones públicas:

| Función | Responsabilidad |
|---|---|
| `obtener_analisis_completo(analisis, year, month)` | Lee Excel, procesa, cachea, devuelve dict de resultado |
| `obtener_extra_columna(analisis)` | Detecta columna opcional (edad/municipio/etc.), devuelve datos de gráfico |
| `obtener_clustering(analisis, tipo_clustering, n_clusters)` | Genera clustering K-means o jerárquico |
| `obtener_heatmap(analisis)` | Calcula matriz de correlación para morbilidad |

### `services/auth_service.py`

Funciones públicas:

| Función | Responsabilidad |
|---|---|
| `registrar_usuario(nombre, email, password)` | Valida campos, verifica duplicado de email, crea usuario |
| `autenticar_usuario(email, password)` | Verifica credenciales, retorna datos del usuario o error |

Ambas retornan `(data_dict, http_status_code)`.

---

## Reglas de estilo

### Comillas
- Todas las cadenas usan comillas simples: `'texto'`
- Docstrings usan triple doble comilla: `"""..."""`
- f-strings usan comillas simples: `f'valor: {x}'`

### PEP 8
- Líneas máximo 79 caracteres
- 2 líneas en blanco entre definiciones de nivel superior
- 1 línea en blanco entre métodos de clase
- Espacios alrededor de operadores
- Constantes en `UPPER_CASE`, funciones y variables en `snake_case`, clases en `PascalCase`
- Imports ordenados: stdlib → terceros → locales, separados por línea en blanco

### Docstrings (estilo Google)

Todas las funciones y métodos públicos llevan docstring:

```python
def calcular_edad(fecha_nacimiento, fecha_evento):
    """Calcula la edad en años entre dos fechas.

    Args:
        fecha_nacimiento: Fecha de nacimiento del paciente.
        fecha_evento: Fecha del evento clínico (parto, defunción, egreso).

    Returns:
        Edad en años como entero, o None si alguna fecha es inválida.
    """
```

Funciones privadas (prefijo `_`) llevan docstring solo si la lógica no es evidente.

### Comentarios de lógica de negocio

Solo donde el WHY no es obvio por el nombre:

```python
# SIVIGILA exporta fechas como seriales Excel (días desde 1899-12-30)
# en versiones anteriores a 2018; el rango 1000-100000 los identifica
is_excel_serial = (s_numeric > 1000) & (s_numeric < 100_000)
```

No se comentan cosas que ya dice el nombre de la variable o función.

---

## Archivos modificados

| Archivo | Cambios |
|---|---|
| `views.py` | Queda solo con vistas HTTP (~5 líneas cada una); imports de services |
| `services/__init__.py` | Nuevo (vacío) |
| `services/upload_service.py` | Nuevo — lógica extraída de `views.py` |
| `services/analisis_service.py` | Nuevo — lógica extraída de `views.py` |
| `services/auth_service.py` | Nuevo — lógica extraída de `views.py` |
| `processors.py` | Estilo: quotes, docstrings, PEP 8 |
| `models.py` | Estilo: quotes, docstrings, PEP 8 |
| `serializers.py` | Estilo: quotes, docstrings, PEP 8 |
| `sivigila_models.py` | Estilo: quotes, docstrings, PEP 8 |
| `sivigila_ingestion.py` | Estilo: quotes, docstrings, PEP 8 |
| `urls.py` | Estilo: quotes, PEP 8 |
| `apps.py` | Estilo: quotes, PEP 8 |

---

## Criterios de éxito

- El backend arranca sin errores (`python manage.py runserver`)
- Todos los endpoints responden igual que antes
- `views.py` no importa `pandas`, `openpyxl`, ni `BytesIO`
- Cada función pública tiene docstring
- No hay cadenas con comillas dobles en ningún archivo `.py`
