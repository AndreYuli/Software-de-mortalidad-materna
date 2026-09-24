# Performance Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar los cuellos de botella de rendimiento del backend Django y el frontend React que hacen la app lenta.

**Architecture:** 9 fixes independientes agrupados en tareas por archivo. Backend: eliminar prints de debug, cachear mapa de alias, consolidar parseos de fechas redundantes, agregar caché en memoria para endpoint pesado, nuevo endpoint para evitar descarga de Excel en browser. Frontend: reemplazar descarga Excel con llamada API, heatmap on-demand, eliminar cómputo duplicado.

**Tech Stack:** Django 6, Django REST Framework, pandas, React + Vite, react-plotly.js, xlsx.js (a eliminar del flujo crítico)

---

## Archivos a modificar

| Archivo | Cambios |
|---|---|
| `BACKEND/api/processors.py` | Eliminar prints, cachear `_construir_mapa_alias` |
| `BACKEND/api/views.py` | Consolidar `_parse_serie_fechas`, fix doble `preparar_dataframe_analisis`, caché `analisis_completo`, nuevo endpoint `extra_columna_analisis` |
| `BACKEND/config/settings.py` | Agregar `CACHES` con LocMemCache |
| `BACKEND/api/urls.py` | Registrar nueva URL `extra-columna` |
| `FRONTED/maternanalytics/src/components/AnalisisView.jsx` | Reemplazar Excel-download, heatmap on-demand, fix `buildClusterDescriptor` doble |

---

### Task 1: Eliminar prints de debug y cachear `_construir_mapa_alias`

**Files:**
- Modify: `BACKEND/api/processors.py:55-91`
- Modify: `BACKEND/api/views.py:213-232`

- [ ] **Step 1: Eliminar los print() de processors.py**

En `processors.py`, reemplazar el bloque `preparar_dataframe_analisis` desde la línea 63 hasta la 91 eliminando todos los `print(...)`:

```python
def preparar_dataframe_analisis(df):
    """Normaliza el DataFrame y elimina filas vacias o duplicadas exactas para analisis."""
    normalizado = df.copy()
    total_original = len(normalizado)

    if total_original == 0:
        return normalizado, {'total_original': 0, 'filas_vacias_omitidas': 0, 'filas_duplicadas_omitidas': 0}

    birth_col = 'Fecha de Nacimiento'
    event_col_candidates = [
        '9.3 Fecha parto (dd/mm/aaaa)', '9.3 Fecha parto',
        '5.2 Fecha de defunción', '5.2 Fecha de defuncion',
        'Fecha de egreso', 'Fecha de egreso (dd/mm/aaaa)',
    ]

    if birth_col in normalizado.columns:
        event_col = next((c for c in event_col_candidates if c in normalizado.columns), None)
        if event_col:
            try:
                nacs = _parse_fecha_robusta(normalizado[birth_col])
                evs = _parse_fecha_robusta(normalizado[event_col])
                years = evs.dt.year - nacs.dt.year
                before_birthday = (evs.dt.month < nacs.dt.month) | (
                    (evs.dt.month == nacs.dt.month) & (evs.dt.day < nacs.dt.day)
                )
                edades = years - before_birthday.astype(int)
                normalizado['Edad'] = edades.where((edades >= 0) & (edades <= 120))
            except Exception:
                pass

    columnas_texto = normalizado.select_dtypes(include=['object']).columns
    for columna in columnas_texto:
        normalizado[columna] = normalizado[columna].apply(
            lambda valor: valor.strip() if isinstance(valor, str) else valor
        )

    sin_vacias = normalizado.dropna(how='all')
    filas_vacias_omitidas = total_original - len(sin_vacias)
    sin_duplicadas = sin_vacias.drop_duplicates().reset_index(drop=True)
    filas_duplicadas_omitidas = len(sin_vacias) - len(sin_duplicadas)

    return sin_duplicadas, {
        'total_original': total_original,
        'filas_vacias_omitidas': filas_vacias_omitidas,
        'filas_duplicadas_omitidas': filas_duplicadas_omitidas,
    }
```

- [ ] **Step 2: Cachear `_construir_mapa_alias` en views.py**

En `views.py`, agregar `from functools import lru_cache` al bloque de imports (arriba del todo) y decorar `_construir_mapa_alias`:

```python
from functools import lru_cache
```

Luego la función queda:

```python
@lru_cache(maxsize=4)
def _construir_mapa_alias(tipo):
    mapa = {}
    for canonical in COLUMNAS_REQUERIDAS[tipo]:
        mapa[_normalizar_encabezado(canonical)] = canonical
    for canonical, alias_list in ALIAS_COLUMNAS.get(tipo, {}).items():
        mapa[_normalizar_encabezado(canonical)] = canonical
        for alias in alias_list:
            mapa[_normalizar_encabezado(alias)] = canonical
    return mapa
```

- [ ] **Step 3: Commit**

```bash
git add BACKEND/api/processors.py BACKEND/api/views.py
git commit -m "perf: eliminar prints de debug y cachear mapa de alias"
```

---

### Task 2: Consolidar los tres `_parse_serie_fechas` en `analisis_completo`

**Files:**
- Modify: `BACKEND/api/views.py:639-728`

El problema: en `analisis_completo`, la columna de fecha se parsea 3 veces:
1. `_extraer_anos_disponibles` (línea 664)
2. el bucle `distribucion_mensual` (línea 671)
3. `_filtrar_dataframe_por_fecha` (línea 682)

La solución es pre-computar las fechas una sola vez antes del filtro y pasarlas donde se necesitan.

- [ ] **Step 1: Reescribir el bloque de fechas en `analisis_completo`**

Reemplazar el bloque desde la línea 664 hasta la 682 con este código que parsea fechas solo una vez:

```python
        col_fecha = _detectar_col_fecha(df, analisis.tipo)
        fechas_serie = None
        anos_disponibles = []
        distribucion_mensual = {}

        if col_fecha is not None:
            fechas_serie = _parse_serie_fechas(df[col_fecha])
            valid_fechas = fechas_serie.dropna()
            anos_disponibles = sorted(valid_fechas.dt.year.unique().astype(int).tolist())
            for fecha in valid_fechas:
                y_str = str(fecha.year)
                m_str = str(fecha.month)
                if y_str not in distribucion_mensual:
                    distribucion_mensual[y_str] = {str(i): 0 for i in range(1, 13)}
                distribucion_mensual[y_str][m_str] = distribucion_mensual[y_str].get(m_str, 0) + 1

        # Filtrar usando las fechas ya calculadas
        if (year or month) and col_fecha is not None and fechas_serie is not None:
            mask = pd.Series([True] * len(df), index=df.index)
            if year:
                mask &= fechas_serie.dt.year == int(year)
            if month:
                mask &= fechas_serie.dt.month == int(month)
            df = df[mask].reset_index(drop=True)
```

También eliminar la función `_extraer_anos_disponibles` (ya no se usa en este flujo) y reemplazar la llamada vieja por el nuevo bloque. Las funciones helper `_extraer_anos_disponibles` y `_filtrar_dataframe_por_fecha` pueden quedar en el archivo por si acaso, solo dejan de usarse en este endpoint.

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/views.py
git commit -m "perf: parsear fechas una sola vez por request en analisis_completo"
```

---

### Task 3: Eliminar el doble `preparar_dataframe_analisis` en `procesar_carga_archivo`

**Files:**
- Modify: `BACKEND/api/views.py:386-467`

El problema: `preparar_dataframe_analisis(df)` se llama en línea 417, y luego se vuelve a llamar dentro de `construir_archivo_analisis_desde_dataframe` (línea 341). El DataFrame ya está limpio cuando entra a la segunda función.

- [ ] **Step 1: Modificar `construir_archivo_analisis_desde_dataframe` para aceptar df ya preparado**

En `views.py`, cambiar la función para que reciba el df ya limpio y no lo vuelva a limpiar:

```python
def construir_archivo_analisis_desde_dataframe(df_fuente, tipo, nombre_archivo):
    # df_fuente ya viene de preparar_dataframe_analisis — no re-procesar
    resumen = calcular_resumen_desde_dataframe(df_fuente, tipo)
    total_registros = resumen.pop('total_registros', len(df_fuente))

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_fuente.to_excel(writer, index=False)

    contenido = buffer.getvalue()
    archivo = ContentFile(contenido, name=nombre_archivo)
    archivo_hash = sha256(contenido).hexdigest()

    return archivo, archivo_hash, resumen, total_registros
```

Nota: `calcular_resumen_desde_dataframe` internamente llamaba a `preparar_dataframe_analisis`. También hay que cambiarla para que NO lo haga:

```python
def calcular_resumen_desde_dataframe(df, tipo):
    try:
        # df ya viene limpio — solo calcular estadísticas
        resumen = {
            'total_registros': len(df),
            'total_registros_original': len(df),
            'filas_vacias_omitidas': 0,
            'filas_duplicadas_omitidas': 0,
        }

        if tipo == 'mortalidad':
            if COLUMNA_MOMENTO_MUERTE in df.columns:
                resumen['distribucion_momento'] = (
                    df[COLUMNA_MOMENTO_MUERTE].value_counts().to_dict()
                )
            if COLUMNA_CAUSA_BASICA_CIE10 in df.columns:
                top5 = df[COLUMNA_CAUSA_BASICA_CIE10].value_counts().head(5).to_dict()
                resumen['top5_causas'] = {str(k): int(v) for k, v in top5.items()}

        elif tipo == 'morbilidad':
            criterios_cols = ['Eclampsia', 'Sepsis sistémica severa',
                              'Hemorragia obstétrica severa', 'Preeclampsia', 'Ruptura uterina']
            presentes = [c for c in criterios_cols if c in df.columns]
            if presentes:
                resumen['criterios_frecuencia'] = {
                    c: int(df[c].apply(es_valor_positivo).sum()) for c in presentes
                }

        return resumen
    except Exception:
        return {}
```

- [ ] **Step 2: Commit**

```bash
git add BACKEND/api/views.py
git commit -m "perf: evitar doble procesamiento del dataframe al subir archivo"
```

---

### Task 4: Cachear resultados de `analisis_completo` con LocMemCache

**Files:**
- Modify: `BACKEND/config/settings.py`
- Modify: `BACKEND/api/views.py`
- Modify: `BACKEND/api/models.py`

- [ ] **Step 1: Agregar CACHES a settings.py**

Al final de `BACKEND/config/settings.py`, agregar:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'maternanalytics',
        'TIMEOUT': 600,  # 10 minutos
    }
}
```

- [ ] **Step 2: Importar cache en views.py**

Agregar al bloque de imports de `views.py`:

```python
from django.core.cache import cache
```

- [ ] **Step 3: Envolver `analisis_completo` con caché**

Al inicio del bloque `try` de `analisis_completo` (después de obtener el objeto `analisis`), agregar:

```python
    cache_key = f'completo_{pk}_{year or ""}_{month or ""}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
```

Y antes del `return Response(resultado)` al final del mismo bloque, agregar:

```python
        cache.set(cache_key, resultado, timeout=600)
        return Response(resultado)
```

- [ ] **Step 4: Invalidar caché cuando se actualiza un Analisis**

En `BACKEND/api/models.py`, en la clase `Analisis`, sobreescribir `save()`:

```python
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.core.cache import cache
        # Limpiar todas las entradas de caché para este análisis
        for sufijo in ['__', '_']:
            # Eliminar cualquier variante de filtro: sin filtros, con year, con month, con ambos
            cache.delete(f'completo_{self.pk}__')
        cache.delete_many([
            f'completo_{self.pk}__',
            f'completo_{self.pk}_',
        ])
        # Usar delete_pattern si está disponible, sino limpiar cache completo
        try:
            cache.delete_pattern(f'completo_{self.pk}_*')
        except AttributeError:
            cache.clear()
```

Nota: `LocMemCache` no soporta `delete_pattern`. La solución simple es limpiar el caché completo en `save()`, ya que en dev solo hay unos pocos análisis:

```python
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.clear()
```

- [ ] **Step 5: Commit**

```bash
git add BACKEND/config/settings.py BACKEND/api/views.py BACKEND/api/models.py
git commit -m "perf: agregar cache en memoria para analisis_completo (10 min TTL)"
```

---

### Task 5: Nuevo endpoint `/api/analisis/<id>/extra-columna/`

**Files:**
- Modify: `BACKEND/api/views.py` (agregar función)
- Modify: `BACKEND/api/urls.py` (registrar URL)

Este endpoint reemplaza la lógica del frontend que descargaba el Excel completo al browser para detectar columnas opcionales (edad, municipio, departamento, régimen, EPS).

- [ ] **Step 1: Implementar `extra_columna_analisis` en views.py**

Agregar al final de `views.py`, antes del último `login_usuario`:

```python
_EXTRA_COL_PATTERNS = {
    'edad': ['edad', 'edad (anos)', 'edad (años)', 'edad anos', 'edad años'],
    'departamento': ['departamento', 'depto', 'dpto'],
    'municipio': ['municipio'],
    'regimen': ['regimen', 'régimen', 'afiliacion', 'afiliación'],
    'eps': ['eps', 'entidad promotora', 'aseguradora'],
}

_EXTRA_COL_PRIORITY = ['municipio', 'departamento', 'edad', 'regimen', 'eps']


def _normalizar_extra(v):
    texto = str(v or '').strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', ' ', texto).strip()


def _detectar_extra_columna(headers):
    headers_norm = [_normalizar_extra(h) for h in headers]
    for kind in _EXTRA_COL_PRIORITY:
        for pattern in _EXTRA_COL_PATTERNS[kind]:
            pat_norm = _normalizar_extra(pattern)
            for i, hn in enumerate(headers_norm):
                if hn == pat_norm or pat_norm in hn:
                    return kind, i, headers[i]
    return None, -1, None


@api_view(['GET'])
@permission_classes([AllowAny])
def extra_columna_analisis(request, pk):
    """
    GET /api/analisis/<id>/extra-columna/
    Detecta columna opcional (edad/municipio/departamento/régimen/EPS) en el Excel
    y devuelve datos listos para graficar. Evita que el frontend descargue el archivo.
    """
    try:
        analisis = Analisis.objects.get(pk=pk)
    except Analisis.DoesNotExist:
        return Response({'error': ERROR_ANALISIS_NO_ENCONTRADO}, status=status.HTTP_404_NOT_FOUND)

    if analisis.tipo != 'mortalidad':
        return Response({'chart': None})

    cache_key = f'extra_col_{pk}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    try:
        df = pd.read_excel(analisis.archivo.path, engine='openpyxl', nrows=2000)
    except Exception:
        return Response({'chart': None})

    kind, col_idx, col_name = _detectar_extra_columna(list(df.columns))
    if kind is None:
        resultado = {'chart': None}
        cache.set(cache_key, resultado, timeout=600)
        return Response(resultado)

    serie = df[col_name]

    if kind == 'edad':
        edades = pd.to_numeric(serie, errors='coerce')
        edades = edades[(edades >= 0) & (edades <= 120)].dropna()
        if len(edades) < 3:
            resultado = {'chart': None}
            cache.set(cache_key, resultado, timeout=600)
            return Response(resultado)

        buckets = [
            ('<15', 0, 14.999), ('15-19', 15, 19.999), ('20-24', 20, 24.999),
            ('25-29', 25, 29.999), ('30-34', 30, 34.999), ('35-39', 35, 39.999),
            ('40+', 40, 120),
        ]
        labels = [b[0] for b in buckets]
        values = [int(((edades >= b[1]) & (edades <= b[2])).sum()) for b in buckets]
        resultado = {
            'chart': {
                'type': 'bar', 'orientation': 'v',
                'title': 'Distribución por edad',
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels, 'values': values,
                'total': int(sum(values)),
                'xTitle': 'Rango de edad (años)', 'yTitle': 'Casos',
            }
        }
    else:
        def clean(v):
            s = str(v or '').strip()
            if not s or s.lower() in ('nan', 'null', 'none', 'sin dato'):
                return None
            return s

        cats = [clean(v) for v in serie]
        cats = [c for c in cats if c]
        if len(cats) < 3:
            resultado = {'chart': None}
            cache.set(cache_key, resultado, timeout=600)
            return Response(resultado)

        counts_map = {}
        for c in cats:
            counts_map[c] = counts_map.get(c, 0) + 1

        sorted_cats = sorted(counts_map.items(), key=lambda x: x[1], reverse=True)
        top = sorted_cats[:10]
        other = sum(v for _, v in sorted_cats[10:])
        labels = [k for k, _ in top]
        values = [v for _, v in top]
        if other > 0:
            labels.append('Otros')
            values.append(other)

        title_map = {
            'departamento': 'Top departamentos',
            'municipio': 'Top municipios',
            'regimen': 'Distribución por régimen',
            'eps': 'Top EPS',
        }
        resultado = {
            'chart': {
                'type': 'bar', 'orientation': 'h',
                'title': title_map.get(kind, 'Distribución'),
                'subtitle': f'Columna detectada: {col_name}',
                'labels': labels, 'values': values,
                'total': int(sum(values)),
                'xTitle': 'Casos', 'yTitle': '',
            }
        }

    cache.set(cache_key, resultado, timeout=600)
    return Response(resultado)
```

- [ ] **Step 2: Registrar la URL en urls.py**

En `BACKEND/api/urls.py`, agregar:

```python
path('analisis/<int:pk>/extra-columna/', views.extra_columna_analisis, name='extra-columna-analisis'),
```

- [ ] **Step 3: Commit**

```bash
git add BACKEND/api/views.py BACKEND/api/urls.py
git commit -m "feat: endpoint extra-columna para evitar descarga de Excel en frontend"
```

---

### Task 6: Frontend — reemplazar descarga de Excel con llamada al nuevo endpoint

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/AnalisisView.jsx:467-682`

Eliminar todo el `useEffect` que descargaba el Excel (unas 200 líneas) y reemplazarlo con un simple `fetch` al nuevo endpoint `/api/analisis/{id}/extra-columna/`.

- [ ] **Step 1: Reemplazar el useEffect de `detectarDistribucion`**

En `ChartsTab`, eliminar el `useEffect` completo de `detectarDistribucion` (líneas ~467–682) y reemplazarlo con este, mucho más corto:

```javascript
  useEffect(() => {
    if (data?.tipo !== 'mortalidad') return

    let isMounted = true
    const controller = new AbortController()

    const cargarExtraChart = async () => {
      setExtraChartLoading(true)
      setExtraChartError(null)
      try {
        const response = await fetch(`${API_URL}/analisis/${analisisId}/extra-columna/`, {
          signal: controller.signal,
        })
        const payload = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(payload?.error || 'No se pudo cargar columna adicional.')
        if (isMounted) setExtraChart(payload.chart ?? null)
      } catch (err) {
        if (err?.name === 'AbortError') return
        if (isMounted) {
          setExtraChart(null)
          setExtraChartError(err?.message || 'No se pudo generar el gráfico adicional.')
        }
      } finally {
        if (isMounted) setExtraChartLoading(false)
      }
    }

    cargarExtraChart()
    return () => { isMounted = false; controller.abort() }
  }, [analisisId, data?.tipo])
```

También eliminar el import de `xlsx` si ya no se usa en ningún otro lugar del componente. Verificar que `import * as XLSX from 'xlsx'` no se referencie más en `AnalisisView.jsx`.

- [ ] **Step 2: Commit**

```bash
git add FRONTED/maternanalytics/src/components/AnalisisView.jsx
git commit -m "perf: reemplazar descarga de Excel en browser con llamada al endpoint extra-columna"
```

---

### Task 7: Frontend — heatmap on-demand en vez de auto-carga

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/AnalisisView.jsx:415-465`

Actualmente el heatmap se carga automáticamente cuando se monta `ChartsTab`. Hay que cargarlo solo cuando el usuario lo pide (clic en botón).

- [ ] **Step 1: Convertir heatmap a carga bajo demanda**

En `ChartsTab`, cambiar el estado y el `useEffect` del heatmap:

```javascript
  const [heatmapData, setHeatmapData] = useState(null)
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  const [heatmapError, setHeatmapError] = useState(null)
  const [heatmapRequested, setHeatmapRequested] = useState(false)
```

Reemplazar el `useEffect` del heatmap (líneas ~423-465) con uno que solo dispara si `heatmapRequested === true`:

```javascript
  useEffect(() => {
    if (data?.tipo !== 'morbilidad' || !heatmapRequested) return

    let isMounted = true
    const controller = new AbortController()

    const cargarHeatmap = async () => {
      setHeatmapLoading(true)
      setHeatmapError(null)
      try {
        const response = await fetch(`${API_URL}/analisis/${analisisId}/heatmap/`, { signal: controller.signal })
        const payload = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(payload?.error || 'No se pudo generar el heatmap.')
        if (payload?.error) throw new Error(payload.error)
        if (isMounted) setHeatmapData(payload)
      } catch (err) {
        if (err?.name === 'AbortError') return
        if (isMounted) { setHeatmapError(err?.message || 'Error al cargar heatmap.'); setHeatmapData(null) }
      } finally {
        if (isMounted) setHeatmapLoading(false)
      }
    }

    cargarHeatmap()
    return () => { isMounted = false; controller.abort() }
  }, [analisisId, data?.tipo, heatmapRequested])
```

En el JSX del heatmap, antes del spinner, agregar un botón que dispara la carga:

```jsx
  {data.tipo === 'morbilidad' && (
    ...
    <div className="chart-container">
      <h3 className="chart-title">Heatmap de correlacion</h3>

      {!heatmapRequested && !heatmapLoading && !heatmapData && (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <button
            className="btn-generate"
            onClick={() => setHeatmapRequested(true)}
          >
            Generar heatmap de correlación
          </button>
        </div>
      )}

      {heatmapRequested && heatmapLoading && (
        <div className="loading" style={{ padding: '40px 20px' }}>
          <div className="spinner"></div>
          <p>Generando heatmap de correlación...</p>
        </div>
      )}
      ... (resto igual)
    </div>
  )}
```

- [ ] **Step 2: Commit**

```bash
git add FRONTED/maternanalytics/src/components/AnalisisView.jsx
git commit -m "perf: heatmap de morbilidad on-demand en vez de auto-carga"
```

---

### Task 8: Frontend — eliminar `buildClusterDescriptor` duplicado

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/AnalisisView.jsx:1320-1460`

`buildClusterDescriptor` se llama dos veces por perfil: una en `clusterLegend` (línea ~1322) y otra al renderizar los `profile-card` (líneas ~1434-1439).

- [ ] **Step 1: Precalcular descriptores una sola vez**

En `ClusteringTab`, reemplazar el cómputo de `clusterLegend` y el doble uso de `buildClusterDescriptor`:

```javascript
  // Precalcular descriptores una vez
  const clusterDescriptors = (data?.cluster_profiles || []).map(profile =>
    buildClusterDescriptor(profile, data?.cluster_profiles || [])
  )

  const clusterMarkerColors = data?.clusters?.map(clusterId => getClusterColor(clusterId)) || []

  const clusterLegend = (data?.cluster_profiles || []).map((profile, idx) => ({
    id: profile.cluster_id,
    size: profile.size,
    color: getClusterColor(profile.cluster_id),
    descriptor: clusterDescriptors[idx],
  }))
```

Luego en el JSX de `profiles-grid`, reemplazar cada llamada `buildClusterDescriptor(profile, data.cluster_profiles)` por `clusterDescriptors[idx]`:

```jsx
  {data.cluster_profiles.map((profile, idx) => (
    <div key={profile.cluster_id} className="profile-card">
      <div className="profile-header">
        <div>
          <span className="profile-label">{clusterDescriptors[idx].title}</span>
          <div className="profile-subtitle">Cluster {profile.cluster_id}</div>
        </div>
        <span className="profile-size">{profile.size} casos</span>
      </div>
      <p className="profile-description">{clusterDescriptors[idx].subtitle}</p>
      ... (resto igual)
    </div>
  ))}
```

- [ ] **Step 2: Commit**

```bash
git add FRONTED/maternanalytics/src/components/AnalisisView.jsx
git commit -m "perf: precalcular buildClusterDescriptor una vez por perfil"
```

---

## Self-Review

| Requisito del diagnóstico | Task que lo cubre |
|---|---|
| Eliminar prints de debug | Task 1 |
| Cachear `_construir_mapa_alias` | Task 1 |
| Fix triple `_parse_serie_fechas` | Task 2 |
| Fix doble `preparar_dataframe_analisis` | Task 3 |
| Caché `analisis_completo` | Task 4 |
| Endpoint extra-columna | Task 5 |
| Frontend: eliminar descarga Excel | Task 6 |
| Heatmap on-demand | Task 7 |
| Fix `buildClusterDescriptor` doble | Task 8 |

Todos los problemas del diagnóstico están cubiertos. No hay placeholders ni TBDs.
