# Frontend-FastAPI Compatibility - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completar la compatibilidad frontend ↔ FastAPI: agregar `distribucion_mensual` al endpoint `/completo/`, crear endpoint `/extra-columna/`, y centralizar `API_URL` en el frontend.

**Architecture:** Dos cambios en backend (`api_fastapi/main.py`) y uno en frontend (nuevo `src/api.js` + actualizar imports en 5 componentes). Los cambios de backend reutilizan helpers ya existentes (`_detectar_col_fecha`, `_parse_serie_fechas`, `_canonizar_columnas_dataframe`).

**Tech Stack:** FastAPI, pandas, React 19, fetch nativo

---

### Task 1: Agregar `distribucion_mensual` al endpoint `/completo/`

**Files:**
- Modify: `BACKEND/api_fastapi/main.py` — agregar helper `_calcular_distribucion_mensual` y usarlo en el endpoint completo

El df ya está filtrado por año/mes cuando llega aquí, así que la distribución refleja los filtros activos.

- [ ] **Step 1: Agregar función helper `_calcular_distribucion_mensual`**

  Insertar después de la función `_filtrar_dataframe_por_fecha` (línea 534), antes del bloque `# --- REST API Endpoints ---`:

  ```python
  MESES_ABREV = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

  def _calcular_distribucion_mensual(df, tipo):
      col = _detectar_col_fecha(df, tipo)
      if col is None:
          return {}
      fechas = _parse_serie_fechas(df[col]).dropna()
      if fechas.empty:
          return {}
      conteos = fechas.dt.month.value_counts().sort_index()
      return {
          'labels': [MESES_ABREV[m - 1] for m in conteos.index],
          'values': [int(v) for v in conteos.values],
      }
  ```

- [ ] **Step 2: Agregar `distribucion_mensual` al resultado de mortalidad (línea ~759)**

  En el dict `resultado` de mortalidad, después de `'anos_disponibles': anos_disponibles,`, agregar:

  ```python
  'distribucion_mensual': _calcular_distribucion_mensual(df, 'mortalidad'),
  ```

- [ ] **Step 3: Agregar `distribucion_mensual` al resultado de morbilidad (línea ~776)**

  En el dict `resultado` de morbilidad, después de `'anos_disponibles': anos_disponibles,`, agregar:

  ```python
  'distribucion_mensual': _calcular_distribucion_mensual(df, 'morbilidad'),
  ```

- [ ] **Step 4: Verificar que el endpoint responde correctamente**

  ```bash
  cd BACKEND
  venv/Scripts/python -c "from api_fastapi.main import app; print('OK')"
  ```
  Expected: `OK` (sin ImportError)

- [ ] **Step 5: Commit**

  ```bash
  git add BACKEND/api_fastapi/main.py
  git commit -m "feat: add distribucion_mensual to analisis completo endpoint"
  ```

---

### Task 2: Crear endpoint `/api/analisis/{pk}/extra-columna/`

**Files:**
- Modify: `BACKEND/api_fastapi/main.py` — agregar nuevo endpoint después de `/heatmap/`

Solo aplica a mortalidad. Busca la primera columna disponible en el df de la lista de prioridad: `5.1 Sitio de Defunción` → `6.3 Escolaridad` → `6.1 Convivencia`.

- [ ] **Step 1: Agregar el endpoint después de `/heatmap/` (aproximadamente línea 866)**

  Insertar el siguiente bloque justo después del endpoint `heatmap_correlacion`:

  ```python
  @app.get("/api/analisis/{pk}/extra-columna/")
  def extra_columna_analisis(pk: int, db: Session = Depends(get_db)):
      analisis = db.query(Analisis).filter(Analisis.id == pk).first()
      if not analisis:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail=ERROR_ANALISIS_NO_ENCONTRADO
          )
      if analisis.tipo != 'mortalidad':
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Extra columna solo disponible para análisis de mortalidad"
          )

      clean_path = analisis.archivo.lstrip("/")
      full_path = Path(clean_path)
      if not full_path.exists():
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="El archivo físico del análisis no existe en el servidor."
          )

      try:
          df = pd.read_excel(full_path, engine='openpyxl')
          df = _canonizar_columnas_dataframe(df, 'mortalidad')
          df, _ = preparar_dataframe_analisis(df)

          COLUMNAS_EXTRA = [
              ('5.1 Sitio de Defunción', 'Distribución por Sitio de Defunción', 'Sitio', 'Casos'),
              ('6.3 Escolaridad', 'Distribución por Nivel de Escolaridad', 'Escolaridad', 'Casos'),
              ('6.1 Convivencia', 'Distribución por Convivencia', 'Convivencia', 'Casos'),
          ]

          for col, titulo, x_title, y_title in COLUMNAS_EXTRA:
              if col not in df.columns:
                  continue
              serie = df[col].dropna().astype(str).str.strip()
              serie = serie[~serie.str.lower().isin({'', 'nan', 'none', 'null'})]
              if len(serie) == 0:
                  continue
              conteos = serie.value_counts()
              return {
                  'chart': {
                      'title': titulo,
                      'subtitle': f'Total: {len(serie)} casos con dato registrado',
                      'labels': conteos.index.tolist(),
                      'values': [int(v) for v in conteos.values],
                      'total': int(len(serie)),
                      'xTitle': x_title,
                      'yTitle': y_title,
                      'orientation': 'h',
                  }
              }

          return {'chart': None}
      except Exception as e:
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=f"Error al procesar extra columna: {str(e)}"
          )
  ```

- [ ] **Step 2: Verificar que el servidor inicia sin errores**

  ```bash
  cd BACKEND
  venv/Scripts/python -c "from api_fastapi.main import app; print('Endpoints OK')"
  ```
  Expected: `Endpoints OK`

- [ ] **Step 3: Commit**

  ```bash
  git add BACKEND/api_fastapi/main.py
  git commit -m "feat: add extra-columna endpoint for mortalidad analysis"
  ```

---

### Task 3: Centralizar API_URL en el frontend

**Files:**
- Create: `FRONTED/maternanalytics/src/api.js`
- Modify: `FRONTED/maternanalytics/src/components/Login.jsx:4`
- Modify: `FRONTED/maternanalytics/src/components/Register.jsx:4`
- Modify: `FRONTED/maternanalytics/src/components/Dashboard.jsx:6`
- Modify: `FRONTED/maternanalytics/src/components/AnalisisView.jsx:14`
- Modify: `FRONTED/maternanalytics/src/components/DashboardOKD.jsx:10`

- [ ] **Step 1: Crear `src/api.js`**

  ```javascript
  export const API_URL = 'http://localhost:8000/api';
  ```

- [ ] **Step 2: Actualizar Login.jsx**

  Reemplazar:
  ```javascript
  const API_URL = 'http://localhost:8000/api'
  ```
  Con:
  ```javascript
  import { API_URL } from '../api.js'
  ```

- [ ] **Step 3: Actualizar Register.jsx**

  Reemplazar:
  ```javascript
  const API_URL = 'http://localhost:8000/api'
  ```
  Con:
  ```javascript
  import { API_URL } from '../api.js'
  ```

- [ ] **Step 4: Actualizar Dashboard.jsx**

  Reemplazar:
  ```javascript
  const API_URL = 'http://localhost:8000/api'
  ```
  Con:
  ```javascript
  import { API_URL } from '../api.js'
  ```

- [ ] **Step 5: Actualizar AnalisisView.jsx**

  Reemplazar:
  ```javascript
  const API_URL = 'http://localhost:8000/api'
  ```
  Con:
  ```javascript
  import { API_URL } from '../api.js'
  ```

- [ ] **Step 6: Actualizar DashboardOKD.jsx**

  Reemplazar:
  ```javascript
  const API_URL = 'http://localhost:8000/api'
  ```
  Con:
  ```javascript
  import { API_URL } from '../api.js'
  ```

- [ ] **Step 7: Commit**

  ```bash
  git add FRONTED/maternanalytics/src/api.js \
          FRONTED/maternanalytics/src/components/Login.jsx \
          FRONTED/maternanalytics/src/components/Register.jsx \
          FRONTED/maternanalytics/src/components/Dashboard.jsx \
          FRONTED/maternanalytics/src/components/AnalisisView.jsx \
          FRONTED/maternanalytics/src/components/DashboardOKD.jsx
  git commit -m "refactor: centralize API_URL in src/api.js"
  ```
