# Fase 1: corregir y simplificar el Análisis. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir los indicadores y la semántica de color del análisis, simplificar la pantalla (IA plegada, filtros sin "día" y sin barra fija, causas legibles) y poder verlo con datos de prueba de proporciones creíbles.

**Architecture:** Primero los datos (reinicio controlado de casos, generador realista y su carga), luego el frontend en piezas pequeñas: una función pura de indicadores, la franja de KPIs, colores y orden de causas, etiquetas de valor en las barras, el panel plegable de IA y la barra de filtros. Cada tarea deja `tsc` y los tests en verde.

**Tech Stack:** PostgreSQL + FastAPI + pandas + pytest (datos); React 18, TypeScript, Tailwind v4, lucide-react, Chart.js, Vitest (frontend).

Spec: `docs/superpowers/specs/2026-09-20-analisis-fase1-corregir-simplificar-design.md`

**Quién ejecuta qué:** las Tareas 1 y 3 tocan la base de datos y las ejecuta **el controlador** (no un subagente). El resto se delega a subagentes.

**Convenciones**
- Frontend: los comandos se ejecutan desde `frontend/maternanalytics`. Los tests importan de `vitest` lo que usen. Suite completa con `pnpm exec vitest run --testTimeout=30000`.
- Backend: los comandos se ejecutan desde `backend`, con `venv/Scripts/python.exe`.
- Los commits terminan con `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.
- **No tocar ni commitear** los cambios sin commitear ajenos que hay en el árbol (chatbot: `backend/api/routers/analisis.py`, `backend/schemas/analisis_schema.py`, `backend/services/ia_client.py`, `ia-service/*`, `frontend/.../api.ts`, `frontend/.../DashboardOKD.tsx`, `frontend/.../components/chat/`, `docs/*`). Cada commit hace `git add` solo de los archivos de su tarea.
- Los íconos decorativos de lucide llevan `aria-hidden="true"`.

---

## Estructura de archivos

| Archivo | Acción | Tarea |
|---|---|---|
| `backend/scripts/reiniciar_datos_casos.py` | Crear | 1 |
| `backend/scripts/generar_excels_realistas.py` + `backend/tests/test_generar_excels_realistas.py` | Crear | 2 |
| `data/pruebas/realista_mortalidad_550.xlsx`, `realista_morbilidad_549.xlsx` | Generar | 2 |
| `backend/scripts/cargar_excels_realistas.py` | Crear | 3 |
| `src/utils/indicadoresMaternos.ts` + `.test.ts` | Crear | 4 |
| `src/components/dashboard/KpiRow.tsx` + `.test.tsx` | Reescribir | 5 |
| `src/components/dashboard/AnalysisHomeSection.tsx` | Modificar | 5, 8, 9 |
| `src/constants/chartTheme.ts` + `.test.ts` | Modificar | 6 |
| `src/hooks/dashboard/useDashboardCharts.ts` + `.test.ts` | Modificar | 6 |
| `src/utils/barValueLabels.ts` + `.test.ts` | Crear | 7 |
| `src/utils/causasChartLabels.ts` + `.test.ts` | Modificar | 7 |
| `src/components/dashboard/TrendChartsRow.tsx` | Modificar | 7 |
| `src/components/dashboard/AiSummaryPanel.tsx` + `.test.tsx` | Crear | 8 |
| `src/components/dashboard/FiltersBar.tsx` + `.test.tsx` | Modificar | 9 |

---

### Task 1: Reinicio controlado de casos (lo ejecuta el controlador)

**Contexto:** el análisis se calcula sobre todos los casos acumulados en la base; para ver datos realistas hay que vaciar los casos de prueba. El usuario dio permiso explícito para borrar datos de prueba. Se conservan usuarios (`api_usuario`, 6 cuentas) y catálogos.

**Files:**
- Create: `backend/scripts/reiniciar_datos_casos.py`

- [ ] **Step 1: Crear el script**

Crear `backend/scripts/reiniciar_datos_casos.py`:

```python
"""Vacía los casos y análisis de la base para poder probar el dashboard con datos nuevos.

NO toca usuarios (api_usuario), catálogos (cat_*) ni las tablas de Django/auth. Antes de borrar
exporta cada tabla afectada a CSV en data/local/backup_<fecha>/ (carpeta ignorada por git),
porque en esta máquina no hay pg_dump. Sin --confirmar solo muestra lo que haría.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/reiniciar_datos_casos.py              # simulación
    venv/Scripts/python.exe scripts/reiniciar_datos_casos.py --confirmar  # borra
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import engine  # noqa: E402

# Tablas de partida; el resto (hijas por clave foránea) se calcula solo.
SEMILLAS = [
    'paciente',
    'caso_mortalidad',
    'caso_morbilidad',
    'api_analisis',
    'api_sivigilaimportacion',
    'narrativa_ia',
]
PROTEGIDAS_EXACTAS = {'api_usuario'}
PROTEGIDAS_PREFIJOS = ('cat_', 'django_', 'auth_')

_SQL_DEPENDIENTES = """
WITH RECURSIVE arbol AS (
    SELECT c.oid AS rel
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname = ANY(:semillas)
  UNION
    SELECT f.conrelid
    FROM pg_constraint f
    JOIN arbol a ON f.confrelid = a.rel
    WHERE f.contype = 'f'
)
SELECT DISTINCT c.relname FROM arbol a JOIN pg_class c ON c.oid = a.rel ORDER BY 1
"""


def _es_protegida(tabla: str) -> bool:
    return tabla in PROTEGIDAS_EXACTAS or tabla.startswith(PROTEGIDAS_PREFIJOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--confirmar', action='store_true', help='Borra de verdad (sin esto es una simulación).')
    args = parser.parse_args()

    with engine.connect() as conn:
        tablas = [r[0] for r in conn.execute(text(_SQL_DEPENDIENTES), {'semillas': SEMILLAS})]
        protegidas = [t for t in tablas if _es_protegida(t)]
        if protegidas:
            print(f'ABORTADO: dependen de los casos y son protegidas: {protegidas}')
            return 1
        conteos = {t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in tablas}
        usuarios_antes = conn.execute(text('SELECT count(*) FROM api_usuario')).scalar()

    print('Tablas que se vaciarán:')
    for tabla, filas in conteos.items():
        print(f'  {tabla:<40}{filas:>10}')
    print(f'Usuarios (api_usuario), NO se tocan: {usuarios_antes}')

    if not args.confirmar:
        print('\nSimulación: no se borró nada. Repite con --confirmar para borrar.')
        return 0

    carpeta = Path(__file__).resolve().parents[2] / 'data' / 'local' / f'backup_{datetime.now():%Y%m%d_%H%M%S}'
    carpeta.mkdir(parents=True, exist_ok=False)
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        for tabla in tablas:
            with open(carpeta / f'{tabla}.csv', 'w', encoding='utf-8', newline='') as fh:
                cur.copy_expert(f'COPY "{tabla}" TO STDOUT WITH CSV HEADER', fh)
        print(f'\nCopia de seguridad en {carpeta}')
        lista = ', '.join(f'"{t}"' for t in tablas)
        cur.execute(f'TRUNCATE TABLE {lista} RESTART IDENTITY')
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()

    with engine.connect() as conn:
        restantes = {t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in tablas}
        usuarios_despues = conn.execute(text('SELECT count(*) FROM api_usuario')).scalar()
    print(f'Filas restantes en las tablas vaciadas: {sum(restantes.values())}')
    print(f'Usuarios: {usuarios_antes} -> {usuarios_despues}')
    return 0 if sum(restantes.values()) == 0 and usuarios_antes == usuarios_despues else 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Simulación (no borra nada)**

Run (desde `backend`): `venv/Scripts/python.exe scripts/reiniciar_datos_casos.py`
Expected: lista de tablas con sus filas, `Usuarios (api_usuario), NO se tocan: 6` y `Simulación: no se borró nada`. Ninguna tabla `cat_*`, `django_*`, `auth_*` ni `api_usuario` en la lista. Si el script imprime `ABORTADO`, parar y reportar.

- [ ] **Step 3: Ejecutar de verdad**

Run: `venv/Scripts/python.exe scripts/reiniciar_datos_casos.py --confirmar`
Expected: `Copia de seguridad en …data/local/backup_<fecha>`, `Filas restantes en las tablas vaciadas: 0` y `Usuarios: 6 -> 6`. Comprobar que la carpeta de respaldo existe y tiene un CSV por tabla, y que `git status` no muestra esos CSV (están ignorados).

- [ ] **Step 4: Commit del script**

```bash
git add backend/scripts/reiniciar_datos_casos.py
git commit -m "feat(scripts): reinicio controlado de casos con copia en CSV, sin tocar usuarios ni catálogos"
```

---

### Task 2: Generador de datos realistas

**Files:**
- Create: `backend/scripts/generar_excels_realistas.py`
- Test: `backend/tests/test_generar_excels_realistas.py`
- Genera: `data/pruebas/realista_mortalidad_550.xlsx`, `data/pruebas/realista_morbilidad_549.xlsx`

**Contexto para el implementador:** `backend/scripts/generar_excels_prueba.py` (no modificarlo) define `generar_mortalidad(n)` y `generar_morbilidad(n)`, que devuelven DataFrames con **todas las columnas requeridas** pero con `random.choice` uniforme, y helpers `_fmt(date)` y `_fecha_nacimiento_para_edad(fecha_evento, edad)`. Las columnas clave son: mortalidad `5.2 Fecha de defunción`, `Fecha de Nacimiento`, `10.1 Causa básica CIE-10`, `9.2 Semana gestación`; morbilidad `Fecha de egreso`, `Fecha de Nacimiento`, `Causa principal CIE-10`, `Edad gestacional ocurrencia (sem)`. Las 4 columnas sociodemográficas (`Zona de residencia`, `Población vulnerable`, `Etnia`, `Tipo de afiliación`) no vienen en esas funciones y hay que añadirlas, solo con valores de los catálogos de la base:
- Zona: `Urbana`, `Rural`
- Etnia: `Ninguna`, `Indígena`, `Afrocolombiana`, `Rrom`, `Raizal`, `Otra`
- Población vulnerable: `Ninguna`, `Migrante`, `Indígena`, `Afro`, `Discapacidad`, `Víctima de conflicto`, `Desplazada`
- Afiliación: `Contributivo`, `Subsidiado`, `No afiliada`

- [ ] **Step 1: Escribir el test (falla)**

Crear `backend/tests/test_generar_excels_realistas.py`:

```python
"""Tests del generador de datos de prueba con proporciones realistas."""

import random

import pandas as pd

from scripts.generar_excels_realistas import (
    CATALOGO_AFILIACION,
    CATALOGO_ETNIA,
    CATALOGO_POBLACION_VULNERABLE,
    CATALOGO_ZONA,
    FECHA_FIN,
    FECHA_INICIO,
    N_MORBILIDAD_DEFECTO,
    N_MORTALIDAD_DEFECTO,
    generar_morbilidad_realista,
    generar_mortalidad_realista,
)
from services._analisis_excel import _COLUMNAS_REQUERIDAS

COLUMNAS_SOCIODEMO = ['Zona de residencia', 'Población vulnerable', 'Etnia', 'Tipo de afiliación']


def test_relacion_morbilidad_mortalidad_es_50_a_1():
    assert N_MORBILIDAD_DEFECTO / N_MORTALIDAD_DEFECTO == 50


def test_mortalidad_trae_las_columnas_requeridas_y_las_sociodemograficas():
    df = generar_mortalidad_realista(50, random.Random(1))
    assert set(_COLUMNAS_REQUERIDAS['mortalidad']) <= set(df.columns)
    assert set(COLUMNAS_SOCIODEMO) <= set(df.columns)
    assert len(df) == 50


def test_morbilidad_trae_las_columnas_requeridas_y_las_sociodemograficas():
    df = generar_morbilidad_realista(50, random.Random(1))
    assert set(_COLUMNAS_REQUERIDAS['morbilidad']) <= set(df.columns)
    assert set(COLUMNAS_SOCIODEMO) <= set(df.columns)
    assert len(df) == 50


def test_las_causas_no_son_uniformes_y_la_primera_es_hipertensiva():
    df = generar_morbilidad_realista(3000, random.Random(7))
    frecuencias = df['Causa principal CIE-10'].value_counts(normalize=True)
    assert frecuencias.index[0] == 'O14.1'
    assert 0.20 <= frecuencias.iloc[0] <= 0.32
    assert frecuencias.iloc[0] > 2 * frecuencias.iloc[-1]

    df_mort = generar_mortalidad_realista(3000, random.Random(7))
    frecuencias_mort = df_mort['10.1 Causa básica CIE-10'].value_counts(normalize=True)
    assert frecuencias_mort.index[0] == 'O14.1'


def test_los_valores_sociodemograficos_pertenecen_a_los_catalogos():
    for df in (generar_mortalidad_realista(300, random.Random(3)), generar_morbilidad_realista(300, random.Random(3))):
        assert set(df['Zona de residencia']) <= set(CATALOGO_ZONA)
        assert set(df['Etnia']) <= set(CATALOGO_ETNIA)
        assert set(df['Población vulnerable']) <= set(CATALOGO_POBLACION_VULNERABLE)
        assert set(df['Tipo de afiliación']) <= set(CATALOGO_AFILIACION)


def test_la_zona_urbana_predomina():
    df = generar_morbilidad_realista(2000, random.Random(5))
    assert (df['Zona de residencia'] == 'Urbana').mean() > 0.6


def test_las_fechas_caen_en_el_periodo():
    df = generar_morbilidad_realista(500, random.Random(9))
    fechas = pd.to_datetime(df['Fecha de egreso'], dayfirst=True)
    assert fechas.min() >= pd.Timestamp(FECHA_INICIO)
    assert fechas.max() <= pd.Timestamp(FECHA_FIN)

    df_mort = generar_mortalidad_realista(200, random.Random(9))
    fechas_mort = pd.to_datetime(df_mort['5.2 Fecha de defunción'], dayfirst=True)
    assert fechas_mort.min() >= pd.Timestamp(FECHA_INICIO)
    assert fechas_mort.max() <= pd.Timestamp(FECHA_FIN)


def test_misma_semilla_mismo_resultado():
    a = generar_mortalidad_realista(80, random.Random(11))
    b = generar_mortalidad_realista(80, random.Random(11))
    pd.testing.assert_frame_equal(a, b)
```

- [ ] **Step 2: Ejecutar y comprobar que falla**

Run (desde `backend`): `venv/Scripts/python.exe -m pytest tests/test_generar_excels_realistas.py -v`
Expected: FAIL, no se puede importar `scripts.generar_excels_realistas`.

- [ ] **Step 3: Implementar el generador**

Crear `backend/scripts/generar_excels_realistas.py`:

```python
"""Genera Excels de prueba con proporciones creíbles para revisar el dashboard.

A diferencia de `generar_excels_prueba.py` (elecciones uniformes, pensado para probar la carga),
aquí las causas, edades, zona, etnia y afiliación siguen distribuciones sesgadas y la relación
entre morbilidad materna extrema y muertes maternas es de 50 a 1, del orden de lo que reportan
las cifras oficiales. Los valores sociodemográficos son los de los catálogos de la base.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/generar_excels_realistas.py
Escribe data/pruebas/realista_mortalidad_550.xlsx y data/pruebas/realista_morbilidad_549.xlsx.
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generar_excels_prueba as base  # noqa: E402

N_MORTALIDAD_DEFECTO = 60
N_MORBILIDAD_DEFECTO = 3000
FECHA_INICIO = date(2025, 1, 1)
FECHA_FIN = date(2026, 8, 31)
SEMILLA = 2026

_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'

CATALOGO_ZONA = ['Urbana', 'Rural']
CATALOGO_ETNIA = ['Ninguna', 'Indígena', 'Afrocolombiana', 'Rrom', 'Raizal', 'Otra']
CATALOGO_POBLACION_VULNERABLE = [
    'Ninguna',
    'Migrante',
    'Indígena',
    'Afro',
    'Discapacidad',
    'Víctima de conflicto',
    'Desplazada',
]
CATALOGO_AFILIACION = ['Contributivo', 'Subsidiado', 'No afiliada']

# Pesos relativos (no hace falta que sumen 100).
_PESOS_ZONA = [72, 28]
_PESOS_ETNIA = [78, 9, 10, 0.5, 1, 1.5]
_PESOS_POBLACION_VULNERABLE = [70, 10, 4, 3, 3, 4, 6]
_PESOS_AFILIACION = [43, 52, 5]

# O14.1 preeclampsia severa, O15.0 eclampsia, O85 sepsis puerperal, O08.1 hemorragia tras aborto, ...
_CAUSAS_MORTALIDAD = {
    'O14.1': 24,
    'O15.0': 14,
    'O85': 14,
    'O08.1': 12,
    'O41.1': 9,
    'O99.3': 6,
    'O26.6': 6,
    'O98.0': 5,
    'O94': 5,
    'O44.0': 5,
}
_CAUSAS_MORBILIDAD = {
    'O14.1': 26,
    'O14.0': 14,
    'O46.0': 12,
    'O15.0': 10,
    'O85': 8,
    'O20.0': 8,
    'O34.2': 8,
    'O41.1': 6,
    'O10.0': 4,
    'O36.4': 4,
}
_EDADES_MORTALIDAD = {16: 5, 17: 5, 18: 6, 22: 8, 25: 9, 27: 9, 29: 9, 31: 9, 33: 9, 36: 11, 38: 10, 41: 10}
_EDADES_MORBILIDAD = {16: 4, 18: 6, 20: 8, 23: 10, 26: 12, 28: 12, 30: 12, 32: 11, 34: 10, 37: 8, 39: 7}
# Semanas de gestación: más casos a término (37-41) que en el resto.
_SEMANAS = list(range(20, 43))
_PESOS_SEMANAS = [1 if s < 28 else 2 if s < 37 else 4 if s < 42 else 1 for s in _SEMANAS]


def _fechas(rng: random.Random, n: int) -> list[date]:
    dias = (FECHA_FIN - FECHA_INICIO).days
    return [FECHA_INICIO + timedelta(days=rng.randint(0, dias)) for _ in range(n)]


def _aplicar_sociodemografia(df: pd.DataFrame, rng: random.Random) -> None:
    n = len(df)
    df['Zona de residencia'] = rng.choices(CATALOGO_ZONA, weights=_PESOS_ZONA, k=n)
    df['Población vulnerable'] = rng.choices(CATALOGO_POBLACION_VULNERABLE, weights=_PESOS_POBLACION_VULNERABLE, k=n)
    df['Etnia'] = rng.choices(CATALOGO_ETNIA, weights=_PESOS_ETNIA, k=n)
    df['Tipo de afiliación'] = rng.choices(CATALOGO_AFILIACION, weights=_PESOS_AFILIACION, k=n)


def _aplicar_fechas_y_edades(
    df: pd.DataFrame, rng: random.Random, columna_fecha: str, pesos_edad: dict[int, int]
) -> None:
    n = len(df)
    fechas = _fechas(rng, n)
    edades = rng.choices(list(pesos_edad.keys()), weights=list(pesos_edad.values()), k=n)
    df[columna_fecha] = [base._fmt(f) for f in fechas]
    df['Fecha de Nacimiento'] = [base._fmt(base._fecha_nacimiento_para_edad(f, e)) for f, e in zip(fechas, edades)]


def generar_mortalidad_realista(n: int, rng: random.Random) -> pd.DataFrame:
    """N muertes maternas con causas, edades y sociodemografía sesgadas."""
    random.seed(rng.getrandbits(32))  # las funciones base usan el generador global: se fija desde `rng`
    df = base.generar_mortalidad(n)
    df['10.1 Causa básica CIE-10'] = rng.choices(
        list(_CAUSAS_MORTALIDAD), weights=list(_CAUSAS_MORTALIDAD.values()), k=n
    )
    df['9.2 Semana gestación'] = rng.choices(_SEMANAS, weights=_PESOS_SEMANAS, k=n)
    _aplicar_fechas_y_edades(df, rng, '5.2 Fecha de defunción', _EDADES_MORTALIDAD)
    _aplicar_sociodemografia(df, rng)
    return df


def generar_morbilidad_realista(n: int, rng: random.Random) -> pd.DataFrame:
    """N casos de morbilidad materna extrema con causas, edades y sociodemografía sesgadas."""
    random.seed(rng.getrandbits(32))  # las funciones base usan el generador global: se fija desde `rng`
    df = base.generar_morbilidad(n)
    df['Causa principal CIE-10'] = rng.choices(
        list(_CAUSAS_MORBILIDAD), weights=list(_CAUSAS_MORBILIDAD.values()), k=n
    )
    df['Edad gestacional ocurrencia (sem)'] = rng.choices(_SEMANAS, weights=_PESOS_SEMANAS, k=n)
    _aplicar_fechas_y_edades(df, rng, 'Fecha de egreso', _EDADES_MORBILIDAD)
    _aplicar_sociodemografia(df, rng)
    return df


def main() -> None:
    rng = random.Random(SEMILLA)
    df_mort = generar_mortalidad_realista(N_MORTALIDAD_DEFECTO, rng)
    df_morb = generar_morbilidad_realista(N_MORBILIDAD_DEFECTO, rng)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ruta_mort = _OUTPUT_DIR / 'realista_mortalidad_550.xlsx'
    ruta_morb = _OUTPUT_DIR / 'realista_morbilidad_549.xlsx'
    df_mort.to_excel(ruta_mort, index=False)
    df_morb.to_excel(ruta_morb, index=False)
    print(f'Escrito {ruta_mort} ({len(df_mort)} filas)')
    print(f'Escrito {ruta_morb} ({len(df_morb)} filas)')
    print(f'Relación MME/MM: {len(df_morb) / len(df_mort):.0f}:1')


if __name__ == '__main__':
    main()
```

Notas para el implementador: (a) los nombres de columna y los helpers vienen de `generar_excels_prueba.py`; si alguno difiere del contexto de arriba, ajustar y reportar qué cambió. (b) `random.seed(rng.getrandbits(32))` es necesario: `generar_excels_prueba.py` usa el generador global y sin esa línea dos llamadas con la misma semilla darían tablas distintas. (c) el test de fechas asume el formato `dd/mm/aaaa` que produce `base._fmt`; si es otro, ajustar el `pd.to_datetime` del test (no la aserción) y reportarlo.

- [ ] **Step 4: Ejecutar y comprobar que pasan**

Run: `venv/Scripts/python.exe -m pytest tests/test_generar_excels_realistas.py -v`
Expected: PASS, 8 tests.

Run: `venv/Scripts/python.exe -m ruff check scripts/generar_excels_realistas.py tests/test_generar_excels_realistas.py && venv/Scripts/python.exe -m ruff format --check scripts/generar_excels_realistas.py tests/test_generar_excels_realistas.py`
Expected: sin errores (si el formato difiere, ejecutar `ruff format` sobre esos dos archivos).

- [ ] **Step 5: Generar los Excel**

Run: `venv/Scripts/python.exe scripts/generar_excels_realistas.py`
Expected: `Escrito …realista_mortalidad_550.xlsx (60 filas)`, `…realista_morbilidad_549.xlsx (3000 filas)` y `Relación MME/MM: 50:1`.

- [ ] **Step 6: Commit**

```bash
git add backend/scripts/generar_excels_realistas.py backend/tests/test_generar_excels_realistas.py data/pruebas/realista_mortalidad_550.xlsx data/pruebas/realista_morbilidad_549.xlsx
git commit -m "feat(scripts): generador de datos de prueba con proporciones realistas"
```

---

### Task 3: Cargar los datos realistas y comprobar (lo ejecuta el controlador)

**Files:**
- Create: `backend/scripts/cargar_excels_realistas.py`

- [ ] **Step 1: Crear el cargador**

Crear `backend/scripts/cargar_excels_realistas.py`:

```python
"""Sube por la API los Excels realistas de data/pruebas (requiere el backend en marcha).

Usa el usuario de pruebas del helper e2e (constantes públicas del repositorio); lo crea si no existe.

Uso (desde backend/):
    venv/Scripts/python.exe scripts/cargar_excels_realistas.py
"""

import sys
from pathlib import Path

import requests

API_URL = 'http://localhost:8000/api'
EMAIL = 'e2e@vidamaterna.co'
PASSWORD = 'e2e-clave-segura'
_DATOS = Path(__file__).resolve().parent.parent.parent / 'data' / 'pruebas'
_ARCHIVOS = [
    ('mortalidad', _DATOS / 'realista_mortalidad_550.xlsx'),
    ('morbilidad', _DATOS / 'realista_morbilidad_549.xlsx'),
]
_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def main() -> int:
    # 201 si se crea; 400 si ya existía: ambos valen.
    requests.post(f'{API_URL}/auth/register/', json={'nombre': 'Usuario E2E', 'email': EMAIL, 'password': PASSWORD}, timeout=30)
    login = requests.post(f'{API_URL}/auth/login/', json={'email': EMAIL, 'password': PASSWORD}, timeout=30)
    login.raise_for_status()
    cabeceras = {'Authorization': f'Bearer {login.json()["access_token"]}'}

    for tipo, ruta in _ARCHIVOS:
        with open(ruta, 'rb') as fh:
            respuesta = requests.post(
                f'{API_URL}/analisis/',
                data={'tipo': tipo},
                files={'archivo': (ruta.name, fh, _XLSX)},
                headers=cabeceras,
                timeout=900,
            )
        print(f'{tipo}: HTTP {respuesta.status_code}')
        if respuesta.status_code >= 400:
            print(respuesta.text[:500])
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Ejecutar la carga**

Run (desde `backend`, con el backend en marcha en `localhost:8000`): `venv/Scripts/python.exe scripts/cargar_excels_realistas.py`
Expected: `mortalidad: HTTP 201` y `morbilidad: HTTP 201`. Si un tipo falla, mirar el mensaje, no reintentar a ciegas.

- [ ] **Step 3: Comprobar las proporciones**

Run: `venv/Scripts/python.exe -c "import psycopg2;env=dict(l.strip().split('=',1) for l in open('.env',encoding='utf-8') if '=' in l and not l.startswith('#'));c=psycopg2.connect(host=env['DB_HOST'],port=env['DB_PORT'],user=env['DB_USER'],password=env['DB_PASSWORD'],dbname=env['DB_NAME']);cur=c.cursor();[print(t,(cur.execute(f'select count(*) from {t}'),cur.fetchone()[0])[1]) for t in ('caso_mortalidad','caso_morbilidad','api_analisis','api_usuario')]"`
Expected: `caso_mortalidad 60`, `caso_morbilidad 3000`, `api_analisis 2` (o similar) y `api_usuario` con las cuentas de antes (6, o 7 si el usuario e2e no existía).

- [ ] **Step 4: Commit del cargador**

```bash
git add backend/scripts/cargar_excels_realistas.py
git commit -m "feat(scripts): cargar por la API los Excels de prueba realistas"
```

---

### Task 4: Indicadores maternos y formato es-CO

**Files:**
- Create: `src/utils/indicadoresMaternos.ts`
- Test: `src/utils/indicadoresMaternos.test.ts`

- [ ] **Step 1: Escribir el test (falla)**

Crear `src/utils/indicadoresMaternos.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { calcularIndicadores, formatoNumero } from './indicadoresMaternos'

describe('calcularIndicadores', () => {
  it('sin ambos eventos no hay relación ni índice', () => {
    expect(calcularIndicadores({ ambosEventos: false, totalMortalidad: 60, totalMorbilidad: 3000 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: null,
    })
  })

  it('calcula la relación MME/MM y el índice de mortalidad', () => {
    const { relacionMmeMm, indiceMortalidad } = calcularIndicadores({
      ambosEventos: true,
      totalMortalidad: 60,
      totalMorbilidad: 3000,
    })
    expect(relacionMmeMm).toBe(50)
    expect(indiceMortalidad).toBeCloseTo(1.96, 2)
  })

  it('sin muertes la relación no existe y el índice es 0', () => {
    expect(calcularIndicadores({ ambosEventos: true, totalMortalidad: 0, totalMorbilidad: 100 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: 0,
    })
  })

  it('sin ningún caso no hay ni relación ni índice', () => {
    expect(calcularIndicadores({ ambosEventos: true, totalMortalidad: 0, totalMorbilidad: 0 })).toEqual({
      relacionMmeMm: null,
      indiceMortalidad: null,
    })
  })
})

describe('formatoNumero', () => {
  it('usa el punto de miles del es-CO', () => {
    expect(formatoNumero(20100)).toBe('20.100')
    expect(formatoNumero(3000)).toBe('3.000')
    expect(formatoNumero(1234567)).toBe('1.234.567')
  })

  it('usa la coma decimal y los decimales pedidos', () => {
    expect(formatoNumero(50.31, 1)).toBe('50,3')
    expect(formatoNumero(50, 1)).toBe('50,0')
  })
})
```

- [ ] **Step 2: Ejecutar y comprobar que falla**

Run: `pnpm exec vitest run src/utils/indicadoresMaternos.test.ts`
Expected: FAIL, no se resuelve `./indicadoresMaternos`.

- [ ] **Step 3: Implementar**

Crear `src/utils/indicadoresMaternos.ts`:

```ts
export interface IndicadoresMaternos {
  /** Casos de morbilidad materna extrema por cada muerte materna (MME / MM). */
  relacionMmeMm: number | null
  /** Muertes maternas sobre el total de eventos: MM / (MME + MM) × 100. */
  indiceMortalidad: number | null
}

interface EntradaIndicadores {
  /** Solo tienen sentido cuando están los dos eventos en el análisis. */
  ambosEventos: boolean
  totalMortalidad: number
  totalMorbilidad: number
}

export function calcularIndicadores({
  ambosEventos,
  totalMortalidad,
  totalMorbilidad,
}: EntradaIndicadores): IndicadoresMaternos {
  if (!ambosEventos) return { relacionMmeMm: null, indiceMortalidad: null }
  const total = totalMortalidad + totalMorbilidad
  return {
    relacionMmeMm: totalMortalidad > 0 ? totalMorbilidad / totalMortalidad : null,
    indiceMortalidad: total > 0 ? (totalMortalidad / total) * 100 : null,
  }
}

/** Formato numérico colombiano: `20.100`, `50,3`. */
export function formatoNumero(valor: number, decimales = 0): string {
  return valor.toLocaleString('es-CO', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
}
```

- [ ] **Step 4: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/utils/indicadoresMaternos.test.ts`
Expected: PASS, 6 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/utils/indicadoresMaternos.ts src/utils/indicadoresMaternos.test.ts
git commit -m "feat(analisis): función de indicadores maternos y formato numérico es-CO"
```

---

### Task 5: KpiRow con relación MME/MM e índice de mortalidad

**Files:**
- Modify (reescribir): `src/components/dashboard/KpiRow.tsx`
- Modify (reescribir): `src/components/dashboard/KpiRow.test.tsx`
- Modify: `src/components/dashboard/AnalysisHomeSection.tsx` (import, cálculo previo al `return` y las props de `<KpiRow>`)

- [ ] **Step 1: Reescribir el test (falla)**

Reemplazar todo el contenido de `src/components/dashboard/KpiRow.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiRow, type KpiRowProps } from './KpiRow'

const base: KpiRowProps = {
  totalMortalidad: 60,
  totalMorbilidad: 3000,
  relacionMmeMm: 50,
  indiceMortalidad: 1.96,
  yearCompareMort: { cur: 15, prev: 10 },
  yearCompareMorb: { cur: 105, prev: 117 },
}

describe('KpiRow', () => {
  it('muestra la región y las cuatro etiquetas nuevas', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByRole('region', { name: 'Resumen epidemiológico' })).toBeInTheDocument()
    expect(screen.getByText('Mortalidad materna 550')).toBeInTheDocument()
    expect(screen.getByText('Morbilidad materna extrema 549')).toBeInTheDocument()
    expect(screen.getByText('Relación MME/MM')).toBeInTheDocument()
    expect(screen.getByText('Índice de mortalidad')).toBeInTheDocument()
  })

  it('ya no muestra "Casos analizados" ni "Tasa de letalidad"', () => {
    render(<KpiRow {...base} />)
    expect(screen.queryByText('Casos analizados')).not.toBeInTheDocument()
    expect(screen.queryByText('Tasa de letalidad')).not.toBeInTheDocument()
  })

  it('muestra las cifras con formato es-CO', () => {
    render(<KpiRow {...base} />)
    expect(screen.getByText('60')).toBeInTheDocument()
    expect(screen.getByText('3.000')).toBeInTheDocument()
    expect(screen.getByText('50,0:1')).toBeInTheDocument()
    expect(screen.getByText('2,0%')).toBeInTheDocument()
  })

  it('muestra "—" cuando la relación o el índice no se pueden calcular', () => {
    render(<KpiRow {...base} relacionMmeMm={null} indiceMortalidad={null} />)
    expect(screen.getAllByText('—')).toHaveLength(2)
  })

  it('muestra las tendencias de mortalidad y morbilidad con la base de comparación', () => {
    render(<KpiRow {...base} periodo="mes" />)
    expect(screen.getByText('+50% vs mes anterior')).toBeInTheDocument()
    expect(screen.getByText('-10% vs mes anterior')).toBeInTheDocument()
  })

  it('usa "año anterior" cuando el periodo es el año', () => {
    render(<KpiRow {...base} periodo="año" />)
    expect(screen.getAllByText(/vs año anterior/)).toHaveLength(2)
  })

  it('sin comparación muestra "Histórico" en las dos tendencias', () => {
    render(<KpiRow {...base} yearCompareMort={null} yearCompareMorb={null} />)
    expect(screen.getAllByText('Histórico')).toHaveLength(2)
  })

  it('explica cómo se calcula cada indicador en un tooltip accesible', () => {
    render(<KpiRow {...base} />)
    const botones = screen.getAllByRole('button', { name: 'Cómo se calcula' })
    expect(botones).toHaveLength(2)
    expect(botones[1]).toHaveAccessibleDescription(/MM \/ \(MME \+ MM\) × 100/)
    expect(screen.getAllByRole('tooltip')).toHaveLength(2)
  })

  it('no muestra una alerta de umbral aunque el índice sea alto', () => {
    render(<KpiRow {...base} indiceMortalidad={62.5} />)
    expect(screen.queryByText('Valor atípicamente alto')).not.toBeInTheDocument()
  })
})
```

Run: `pnpm exec vitest run src/components/dashboard/KpiRow.test.tsx`
Expected: FAIL (el `KpiRow` actual tiene otras props y etiquetas).

- [ ] **Step 2: Reescribir KpiRow**

Antes, `cat` el `KpiRow.tsx` actual y confirmar que se conservan `TrendBadge` con su `periodo`, el `section` con `aria-label="Resumen epidemiológico"` y la rejilla de 1/2/4 columnas con `gap-px`. Reemplazar todo su contenido:

```tsx
import { useId, type ReactNode } from 'react'
import { Activity, Droplet, Hospital, Info, Percent, type LucideIcon } from 'lucide-react'
import { TrendBadge, type TrendPeriodo } from './TrendBadge'
import type { CompareResult } from '../../hooks/dashboard/useDashboardMetrics'
import { formatoNumero } from '../../utils/indicadoresMaternos'

export interface KpiRowProps {
  totalMortalidad: number
  totalMorbilidad: number
  /** MME / MM; `null` si no se puede calcular. */
  relacionMmeMm: number | null
  /** MM / (MME + MM) × 100; `null` si no se puede calcular. */
  indiceMortalidad: number | null
  yearCompareMort: CompareResult | null
  yearCompareMorb: CompareResult | null
  periodo?: TrendPeriodo
}

const SIN_DATO = '—'
const AYUDA_RELACION = 'Casos de morbilidad materna extrema (MME) por cada muerte materna (MM).'
const AYUDA_INDICE =
  'Índice de mortalidad = MM / (MME + MM) × 100: proporción de muertes maternas (evento 550) sobre el total de eventos 549 y 550.'

function InfoTip({ text }: { text: string }) {
  const id = useId()
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-describedby={id}
        className="rounded-full p-0.5 text-slate-400 hover:text-brand-violet focus-visible:text-brand-violet"
      >
        <Info className="size-4" aria-hidden="true" />
        <span className="sr-only">Cómo se calcula</span>
      </button>
      <span
        role="tooltip"
        id={id}
        className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 hidden w-64 -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-normal text-white shadow-lg group-focus-within:block group-hover:block"
      >
        {text}
      </span>
    </span>
  )
}

interface KpiCellProps {
  icon: LucideIcon
  label: string
  value: string
  hint?: string
  trend?: ReactNode
}

function KpiCell({ icon: Icon, label, value, hint, trend }: KpiCellProps) {
  return (
    <div className="flex flex-col gap-2 bg-white p-5">
      <div className="flex items-center gap-3">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-magenta/10 text-brand-magenta">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <span className="text-sm font-medium text-slate-500">{label}</span>
        {hint && <InfoTip text={hint} />}
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <strong className="text-3xl font-bold text-brand-deep">{value}</strong>
        {trend}
      </div>
    </div>
  )
}

export function KpiRow({
  totalMortalidad,
  totalMorbilidad,
  relacionMmeMm,
  indiceMortalidad,
  yearCompareMort,
  yearCompareMorb,
  periodo,
}: KpiRowProps) {
  return (
    <section
      className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200 shadow-sm sm:grid-cols-2 lg:grid-cols-4"
      aria-label="Resumen epidemiológico"
    >
      <KpiCell
        icon={Droplet}
        label="Mortalidad materna 550"
        value={formatoNumero(totalMortalidad)}
        trend={<TrendBadge compare={yearCompareMort} periodo={periodo} />}
      />
      <KpiCell
        icon={Hospital}
        label="Morbilidad materna extrema 549"
        value={formatoNumero(totalMorbilidad)}
        trend={<TrendBadge compare={yearCompareMorb} periodo={periodo} />}
      />
      <KpiCell
        icon={Activity}
        label="Relación MME/MM"
        value={relacionMmeMm === null ? SIN_DATO : `${formatoNumero(relacionMmeMm, 1)}:1`}
        hint={AYUDA_RELACION}
      />
      <KpiCell
        icon={Percent}
        label="Índice de mortalidad"
        value={indiceMortalidad === null ? SIN_DATO : `${formatoNumero(indiceMortalidad, 1)}%`}
        hint={AYUDA_INDICE}
      />
    </section>
  )
}
```

- [ ] **Step 3: Actualizar AnalysisHomeSection**

En `src/components/dashboard/AnalysisHomeSection.tsx`:

1. Añadir el import: `import { calcularIndicadores } from '../../utils/indicadoresMaternos'`
2. Justo antes del `return (` final (después de los `return` tempranos de carga, error y bienvenida), añadir:

```tsx
  const { relacionMmeMm, indiceMortalidad } = calcularIndicadores({
    ambosEventos: segmento === 'ambos',
    totalMortalidad: metrics.totalMortalidad,
    totalMorbilidad: metrics.totalMorbilidad,
  })
```

3. Reemplazar el bloque `<KpiRow ... />` por:

```tsx
      <KpiRow
        totalMortalidad={metrics.totalMortalidad}
        totalMorbilidad={metrics.totalMorbilidad}
        relacionMmeMm={relacionMmeMm}
        indiceMortalidad={indiceMortalidad}
        yearCompareMort={metrics.yearCompareMort}
        yearCompareMorb={metrics.yearCompareMorb}
        periodo={filterMonth ? 'mes' : 'año'}
      />
```

No cambia nada más (`reportExportData` sigue usando `metrics.tasaLetalidad` y `metrics.totalCasos`; el modal de exportación se rediseña en otra parte).

- [ ] **Step 4: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/components/dashboard/KpiRow.test.tsx`
Expected: PASS, 9 tests.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/KpiRow.tsx src/components/dashboard/KpiRow.test.tsx src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat(analisis): KPIs con relación MME/MM e índice de mortalidad, sin casos analizados"
```

---

### Task 6: Colores de evento y orden de las causas

**Files:**
- Modify: `src/constants/chartTheme.ts`, `src/constants/chartTheme.test.ts`
- Modify: `src/hooks/dashboard/useDashboardCharts.ts`, `src/hooks/dashboard/useDashboardCharts.test.ts`
- Modify: `src/components/dashboard/TrendChartsRow.tsx` (solo el tipo `TopCausasChartData`)

- [ ] **Step 1: Añadir los tests (fallan)**

En `src/constants/chartTheme.test.ts`, cambiar las dos aserciones de color del primer test por:

```ts
    expect(CHART_COLORS.mortalidad).toBe('#9F1D35')
    expect(CHART_COLORS.morbilidad).toBe('#D9822B')
```

En `src/hooks/dashboard/useDashboardCharts.test.ts`, añadir el import `import { CHART_COLORS } from '../../constants/chartTheme'` junto a los demás imports y este bloque al final del archivo:

```ts
function fixtureConCausas(causas: [string, number][], totalRegistros: number): AnalisisCompleto {
  return {
    total_registros: totalRegistros,
    causas_cie10: {
      top_causas: causas.map(([codigo, casos]) => ({ codigo, casos })),
      total_causas_unicas: causas.length,
    },
  } as unknown as AnalisisCompleto
}

describe('useDashboardCharts — causas principales', () => {
  it('ordena las causas de mayor a menor (la barra mayor queda arriba)', () => {
    const mortalidadData = fixtureConCausas(
      [
        ['O85', 5],
        ['O14.1', 30],
        ['O15.0', 12],
      ],
      50,
    )
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData: null, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad.values).toEqual([30, 12, 5])
  })

  it('usa el color de cada evento y expone el total de registros', () => {
    const mortalidadData = fixtureConCausas([['O14.1', 30]], 60)
    const morbilidadData = fixtureConCausas([['O14.1', 900]], 3000)
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData, morbilidadData, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad.colors).toEqual([CHART_COLORS.mortalidad])
    expect(result.current.topCausasMorbilidad.colors).toEqual([CHART_COLORS.morbilidad])
    expect(result.current.topCausasMortalidad.total).toBe(60)
    expect(result.current.topCausasMorbilidad.total).toBe(3000)
  })

  it('sin datos devuelve listas vacías y total 0', () => {
    const { result } = renderHook(() =>
      useDashboardCharts({ segmento: 'ambos', mortalidadData: null, morbilidadData: null, filterYear: '' }),
    )
    expect(result.current.topCausasMortalidad).toEqual({ labels: [], values: [], colors: [], total: 0 })
  })
})
```

Run: `pnpm exec vitest run src/constants/chartTheme.test.ts src/hooks/dashboard/useDashboardCharts.test.ts`
Expected: FAIL (colores antiguos, la lista sale invertida, no existe `total`).

- [ ] **Step 2: Cambiar los colores**

En `src/constants/chartTheme.ts`:

```ts
export const CHART_COLORS = {
  mortalidad: '#9F1D35',
  morbilidad: '#D9822B',
}
```

(vino y ámbar; validados con `validate_palette.js`: separación para daltonismo ΔE 23,5; el contraste del ámbar, 2,85:1, se compensa con las etiquetas de valor de las barras). Añadir sobre esa constante el comentario:

```ts
// Vino y ámbar en lugar de rojo y verde: el verde comunica "bueno" y no encaja con la morbilidad
// materna extrema, y rojo/verde se confunden en daltonismo (ΔE 6,5 frente a 23,5 ahora).
```

- [ ] **Step 3: Cambiar el hook**

En `src/hooks/dashboard/useDashboardCharts.ts`:

1. Importar `import { CHART_COLORS } from '../../constants/chartTheme'`.
2. En `lineChartData`, sustituir `color: '#c0392b'` por `color: CHART_COLORS.mortalidad` y `color: '#2ca02c'` por `color: CHART_COLORS.morbilidad`.
3. Reemplazar los dos `useMemo` de causas (`topCausasMortalidad` y `topCausasMorbilidad`) por:

```ts
  const topCausasMortalidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'mortalidad')) {
      return { labels: [], values: [], colors: [], total: 0 }
    }
    const causas = mortalidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10)
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => CHART_COLORS.mortalidad),
      total: mortalidadData?.total_registros ?? 0,
    }
  }, [segmento, mortalidadData])

  const topCausasMorbilidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'morbilidad')) {
      return { labels: [], values: [], colors: [], total: 0 }
    }
    const causas = morbilidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10)
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => CHART_COLORS.morbilidad),
      total: morbilidadData?.total_registros ?? 0,
    }
  }, [segmento, morbilidadData])
```

(Se quita el `.reverse()`: con barras horizontales Chart.js dibuja la primera etiqueta arriba, así la mayor queda arriba.) Si `mortalidadData` no declara `total_registros` en su tipo, usar el mismo tipo `AnalisisCompleto` de `src/types.ts` (hereda `total_registros?` de `AnalisisMeta`); reportar cualquier ajuste de tipos.

- [ ] **Step 4: Ajustar el tipo de las causas**

En `src/components/dashboard/TrendChartsRow.tsx`, en `TopCausasChartData` añadir la propiedad opcional:

```ts
export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
  /** Registros del evento, para calcular el porcentaje de cada causa. */
  total?: number
}
```

- [ ] **Step 5: Ejecutar y comprobar que pasa**

Run: `pnpm exec vitest run src/constants/chartTheme.test.ts src/hooks/dashboard/useDashboardCharts.test.ts src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS.

Run: `grep -rnE "c0392b|2ca02c" src --include=*.ts --include=*.tsx | grep -v "test\.\|CLUSTER_COLORS"`
Expected: sin coincidencias (los hexadecimales antiguos solo quedan en `CLUSTER_COLORS`, que es otra paleta, y en datos de tests).

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 6: Commit**

```bash
git add src/constants/chartTheme.ts src/constants/chartTheme.test.ts src/hooks/dashboard/useDashboardCharts.ts src/hooks/dashboard/useDashboardCharts.test.ts src/components/dashboard/TrendChartsRow.tsx
git commit -m "feat(analisis): mortalidad en vino y morbilidad en ámbar, y causas ordenadas de mayor a menor"
```

---

### Task 7: Etiquetas de valor en las barras y alturas compactas

**Files:**
- Create: `src/utils/barValueLabels.ts`, `src/utils/barValueLabels.test.ts`
- Modify: `src/utils/causasChartLabels.ts`, `src/utils/causasChartLabels.test.ts`
- Modify: `src/components/dashboard/TrendChartsRow.tsx`

- [ ] **Step 1: Escribir el test del plugin (falla)**

Crear `src/utils/barValueLabels.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest'
import type { Chart } from 'chart.js'
import { barValueLabelsPlugin } from './barValueLabels'

function graficaFalsa(valores: number[]) {
  const fillText = vi.fn()
  const chart = {
    ctx: { save: vi.fn(), restore: vi.fn(), fillText },
    getDatasetMeta: () => ({ data: valores.map((_, i) => ({ x: 100 + i * 10, y: 20 + i * 30 })) }),
    data: { datasets: [{ data: valores }] },
  }
  return { chart: chart as unknown as Chart<'bar'>, fillText }
}

describe('barValueLabelsPlugin', () => {
  it('dibuja "n (p %)" a la derecha de cada barra cuando hay total', () => {
    const { chart, fillText } = graficaFalsa([50, 30])
    barValueLabelsPlugin(200).afterDatasetsDraw?.(chart, { cancelable: true } as never, {})
    expect(fillText).toHaveBeenNthCalledWith(1, '50 (25,0 %)', 106, 20)
    expect(fillText).toHaveBeenNthCalledWith(2, '30 (15,0 %)', 116, 50)
  })

  it('sin total dibuja solo el número', () => {
    const { chart, fillText } = graficaFalsa([1200])
    barValueLabelsPlugin(0).afterDatasetsDraw?.(chart, { cancelable: true } as never, {})
    expect(fillText).toHaveBeenCalledWith('1.200', 106, 20)
  })

  it('guarda y restaura el estado del canvas', () => {
    const { chart } = graficaFalsa([5])
    barValueLabelsPlugin(10).afterDatasetsDraw?.(chart, { cancelable: true } as never, {})
    expect(chart.ctx.save).toHaveBeenCalledTimes(1)
    expect(chart.ctx.restore).toHaveBeenCalledTimes(1)
  })
})
```

Run: `pnpm exec vitest run src/utils/barValueLabels.test.ts`
Expected: FAIL, no se resuelve `./barValueLabels`.

- [ ] **Step 2: Crear el plugin**

Crear `src/utils/barValueLabels.ts`:

```ts
import type { Plugin } from 'chart.js'
import { CHART_FONT_FAMILY, CHART_TEXT_COLOR } from '../constants/chartTheme'
import { formatoNumero } from './indicadoresMaternos'

/** Plugin de Chart.js que escribe `n (p %)` a la derecha de cada barra horizontal (solo `n` sin total). */
export function barValueLabelsPlugin(total: number): Plugin<'bar'> {
  return {
    id: 'barValueLabels',
    afterDatasetsDraw(chart) {
      const { ctx } = chart
      const barras = chart.getDatasetMeta(0).data
      const valores = chart.data.datasets[0]?.data as number[] | undefined
      if (!valores) return
      ctx.save()
      ctx.font = `600 11px ${CHART_FONT_FAMILY}`
      ctx.fillStyle = CHART_TEXT_COLOR
      ctx.textBaseline = 'middle'
      ctx.textAlign = 'left'
      barras.forEach((barra, i) => {
        const valor = valores[i]
        const texto =
          total > 0 ? `${formatoNumero(valor)} (${formatoNumero((valor / total) * 100, 1)} %)` : formatoNumero(valor)
        ctx.fillText(texto, barra.x + 6, barra.y)
      })
      ctx.restore()
    },
  }
}
```

- [ ] **Step 3: Ejecutar el test del plugin**

Run: `pnpm exec vitest run src/utils/barValueLabels.test.ts`
Expected: PASS, 3 tests. (Si Chart.js tipa distinto la firma de `afterDatasetsDraw`, ajustar los tipos del plugin y del test sin cambiar el comportamiento, y reportarlo.)

- [ ] **Step 4: Alturas compactas**

En `src/utils/causasChartLabels.ts` cambiar las constantes de altura para que una barra de una línea ocupe unos 28 px (+20 px por línea extra):

```ts
const LINE_HEIGHT = 20
const MIN_BAR_HEIGHT = 8
```

(`AXIS_PADDING = 60` y `MIN_CHART_HEIGHT = 320` no cambian.) En `src/utils/causasChartLabels.test.ts` mantener los tres tests de `calculateChartHeight` y añadir:

```ts
  it('una barra de una línea ocupa unos 28 px y cada línea extra suma 20 px', () => {
    const diez = Array.from({ length: 10 }, () => 'Eclampsia')
    expect(calculateChartHeight(diez)).toBe(60 + 10 * 28)
  })
```

Run: `pnpm exec vitest run src/utils/causasChartLabels.test.ts`
Expected: PASS (el test de "crece cuando las etiquetas ocupan más líneas" debe seguir pasando; si no, reportar cuál y por qué).

- [ ] **Step 5: Usar el plugin en TrendChartsRow**

En `src/components/dashboard/TrendChartsRow.tsx`:

1. Importar `import { barValueLabelsPlugin } from '../../utils/barValueLabels'` y añadir `useMemo` a la importación de React si falta (ya está importado).
2. En `CausasBarChart`, antes del `return`, crear el plugin una sola vez por total:

```tsx
  const plugins = useMemo(() => [barValueLabelsPlugin(data.total ?? 0)], [data.total])
```

3. En el `<Bar ...>`, añadir la prop `plugins={plugins}` y, dentro de `options`, la propiedad `layout: { padding: { right: 84 } },` (deja sitio a la etiqueta para que no se recorte). No cambiar ninguna otra opción.

- [ ] **Step 6: Ejecutar y comprobar**

Run: `pnpm exec vitest run src/components/dashboard/TrendChartsRow.test.tsx src/utils/causasChartLabels.test.ts src/utils/barValueLabels.test.ts`
Expected: PASS.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 7: Commit**

```bash
git add src/utils/barValueLabels.ts src/utils/barValueLabels.test.ts src/utils/causasChartLabels.ts src/utils/causasChartLabels.test.ts src/components/dashboard/TrendChartsRow.tsx
git commit -m "feat(analisis): etiquetas n (%) en las barras de causas y barras más compactas"
```

---

### Task 8: Panel plegable del resumen de IA

**Files:**
- Create: `src/components/dashboard/AiSummaryPanel.tsx`, `src/components/dashboard/AiSummaryPanel.test.tsx`
- Modify: `src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Escribir el test (falla)**

Crear `src/components/dashboard/AiSummaryPanel.test.tsx`:

```tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AiSummaryPanel } from './AiSummaryPanel'

describe('AiSummaryPanel', () => {
  it('empieza cerrado', () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    expect(screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('contenido de la IA')).not.toBeVisible()
  })

  it('se abre y se cierra con el botón', async () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    const boton = screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })

    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('contenido de la IA')).toBeVisible()

    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByText('contenido de la IA')).not.toBeVisible()
  })

  it('muestra el aviso de validación al abrirlo', async () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    expect(screen.getByText(/requiere validación del equipo de vigilancia/)).not.toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ }))
    expect(screen.getByText(/Generado automáticamente por IA local/)).toBeVisible()
  })

  it('el botón controla el panel con aria-controls', () => {
    render(
      <AiSummaryPanel>
        <p>contenido de la IA</p>
      </AiSummaryPanel>,
    )
    const boton = screen.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ })
    expect(document.getElementById(boton.getAttribute('aria-controls') as string)).not.toBeNull()
  })
})
```

Run: `pnpm exec vitest run src/components/dashboard/AiSummaryPanel.test.tsx`
Expected: FAIL, no se resuelve `./AiSummaryPanel`.

- [ ] **Step 2: Crear el panel**

Crear `src/components/dashboard/AiSummaryPanel.tsx`:

```tsx
import { useId, useState, type ReactNode } from 'react'
import { ChevronDown, Sparkles } from 'lucide-react'

export interface AiSummaryPanelProps {
  children: ReactNode
}

/** Panel plegable (cerrado por defecto) para los resúmenes generados por IA, con aviso de validación. */
export function AiSummaryPanel({ children }: AiSummaryPanelProps) {
  const [open, setOpen] = useState(false)
  const panelId = useId()

  return (
    <section className="rounded-xl border border-brand-magenta/30 bg-white shadow-sm">
      <h2 className="text-base">
        <button
          type="button"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((value) => !value)}
          className="flex w-full items-center gap-2 px-5 py-4 text-left font-semibold text-brand-deep"
        >
          <Sparkles className="size-5 text-brand-magenta" aria-hidden="true" />
          <span className="flex-1">Resumen ejecutivo (IA)</span>
          <ChevronDown
            className={`size-5 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>
      </h2>
      <div id={panelId} hidden={!open} className="space-y-4 border-t border-slate-200 px-5 py-4">
        <p className="text-sm text-slate-500">
          Generado automáticamente por IA local; requiere validación del equipo de vigilancia.
        </p>
        {children}
      </div>
    </section>
  )
}
```

- [ ] **Step 3: Colocarlo en AnalysisHomeSection**

En `src/components/dashboard/AnalysisHomeSection.tsx`:

1. Importar `import { AiSummaryPanel } from './AiSummaryPanel'`.
2. **Quitar** el bloque `<NarrativasResumen ... />` que está entre `<KpiRow ... />` y el contenido de las pestañas.
3. Añadir, justo antes de `<ExportReportModal ... />` (después del contenido de las pestañas), el mismo bloque envuelto en el panel, con **exactamente las mismas props** que tenía:

```tsx
      <AiSummaryPanel>
        <NarrativasResumen
          latestMortalidad={latestMortalidad}
          latestMorbilidad={latestMorbilidad}
          segmento={segmento}
          filterYear={filterYear}
          filterMonth={filterMonth}
        />
      </AiSummaryPanel>
```

- [ ] **Step 4: Ejecutar y comprobar**

Run: `pnpm exec vitest run src/components/dashboard/AiSummaryPanel.test.tsx src/components/dashboard/NarrativasResumen.test.tsx`
Expected: PASS, 4 + 6 tests (`NarrativasResumen.test.tsx` no se modifica).

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/AiSummaryPanel.tsx src/components/dashboard/AiSummaryPanel.test.tsx src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat(analisis): resumen de IA en un panel plegable al final, con aviso de validación"
```

---

### Task 9: Barra de filtros sin "día" y sin barra fija

**Files:**
- Modify: `src/components/dashboard/FiltersBar.tsx`, `src/components/dashboard/FiltersBar.test.tsx`
- Modify: `src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Actualizar el test (falla)**

En `src/components/dashboard/FiltersBar.test.tsx`:

1. En `baseProps` quitar las líneas `filterDay: ''` y `onDayChange: vi.fn(),`.
2. Reemplazar los tests que hablaban del día por estos (mantener los demás tal cual):

```tsx
  it('deshabilita la semana cuando no hay año seleccionado', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.getByLabelText('Semana de Reporte')).toBeDisabled()
  })

  it('habilita la semana al seleccionar año', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByLabelText('Semana de Reporte')).not.toBeDisabled()
  })

  it('renderiza las 53 semanas ISO', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.getByText('Semana 53')).toBeInTheDocument()
  })

  it('ya no ofrece el filtro por día de reporte', () => {
    render(<FiltersBar {...baseProps} filterYear="2026" filterMonth="3" />)
    expect(screen.queryByLabelText('Día de Reporte')).not.toBeInTheDocument()
  })

  it('el botón Limpiar resetea año, mes y semana', () => {
    const onYearChange = vi.fn()
    const onMonthChange = vi.fn()
    const onWeekChange = vi.fn()
    render(
      <FiltersBar
        {...baseProps}
        filterYear="2026"
        onYearChange={onYearChange}
        filterMonth="3"
        onMonthChange={onMonthChange}
        filterWeek="11"
        onWeekChange={onWeekChange}
      />,
    )
    fireEvent.click(screen.getByText('Limpiar'))
    expect(onYearChange).toHaveBeenCalledWith('')
    expect(onMonthChange).toHaveBeenCalledWith('')
    expect(onWeekChange).toHaveBeenCalledWith('')
  })

  it('la barra no queda fija al hacer scroll', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.getByRole('region', { name: 'Filtros del análisis' }).className).not.toMatch(/sticky/)
  })
```

Run: `pnpm exec vitest run src/components/dashboard/FiltersBar.test.tsx`
Expected: FAIL en los tests nuevos de día y de `sticky`.

- [ ] **Step 2: Cambiar FiltersBar**

En `src/components/dashboard/FiltersBar.tsx`:

1. Quitar de `FiltersBarProps` y de la desestructuración las props `filterDay` y `onDayChange`, y la constante `DIAS_MES`.
2. En `hasActiveFilters` dejar `Boolean(filterYear || filterMonth || filterWeek)`.
3. En `handleClearFilters` quitar la línea `onDayChange('')`.
4. Borrar el bloque `<SelectField id="filter-day" ...>...</SelectField>` completo.
5. En el `className` del `<section aria-label="Filtros del análisis">` quitar ` lg:sticky lg:top-0 lg:z-10`, dejando `rounded-xl border border-slate-200 bg-white p-4 shadow-sm`.

- [ ] **Step 3: Actualizar AnalysisHomeSection**

En `src/components/dashboard/AnalysisHomeSection.tsx`, dentro de `<FiltersBar ... />` quitar las dos props `filterDay={filterDay}` y `onDayChange={onDayChange}`. **No** quitar `filterDay` ni `onDayChange` de `AnalysisHomeSectionProps` ni de las que se pasan a `useAnalysisHomeData` (el estado interno del filtro no se toca). Si tras esto `onDayChange` queda sin usar en la desestructuración de la función y `tsc` lo marca, quitarlo solo de esa desestructuración.

- [ ] **Step 4: Ejecutar y comprobar**

Run: `pnpm exec vitest run src/components/dashboard/FiltersBar.test.tsx`
Expected: PASS.

Run: `pnpm exec tsc -b`
Expected: sin salida.

- [ ] **Step 5: Commit**

```bash
git add src/components/dashboard/FiltersBar.tsx src/components/dashboard/FiltersBar.test.tsx src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat(analisis): barra de filtros sin día de reporte y sin quedar fija"
```

---

### Task 10: Verificación final

**Files:** ninguno (solo comprobaciones).

- [ ] **Step 1: Tipos, build y suite**

Run (desde `frontend/maternanalytics`): `pnpm exec tsc -b`, `pnpm exec vite build` y `pnpm exec vitest run --testTimeout=30000`.
Expected: sin errores de tipos, `✓ built in …` y todos los tests en verde. Referencia: antes de esta fase había 188 tests en 39 archivos; el recuento cambia (KpiRow pasa de 7 a 9, FiltersBar suma y resta, se añaden `indicadoresMaternos`, `barValueLabels` y `AiSummaryPanel`, y 3 tests del hook). Reportar el número final.

- [ ] **Step 2: Lint y backend**

Run: `pnpm exec eslint src/utils/indicadoresMaternos.ts src/utils/barValueLabels.ts src/components/dashboard/KpiRow.tsx src/components/dashboard/AiSummaryPanel.tsx src/components/dashboard/FiltersBar.tsx src/components/dashboard/TrendChartsRow.tsx src/components/dashboard/AnalysisHomeSection.tsx src/hooks/dashboard/useDashboardCharts.ts`
Expected: sin errores nuevos (el aviso previo de `AnalysisHomeSection` sobre `morbKpis.edadPromedio` puede seguir).

Run (desde `backend`): `venv/Scripts/python.exe -m pytest tests/test_generar_excels_realistas.py -q`
Expected: 8 passed.

- [ ] **Step 3: Restos**

Run: `grep -rnE "Casos analizados|Tasa de letalidad|Día de Reporte|filter-day|lg:sticky" src --include=*.ts --include=*.tsx`
Expected: sin coincidencias.

- [ ] **Step 4: Comprobar el análisis con los datos realistas (controlador)**

Con el backend en marcha, pedir el análisis completo del último análisis de cada tipo y comprobar cifras: `GET /api/analisis/` para ver los ids y `GET /api/analisis/{id}/completo/` para cada uno. Expected: mortalidad con 60 casos y morbilidad con 3.000; en `causas_cie10.top_causas`, `O14.1` primero y con un porcentaje claramente mayor que el último.

- [ ] **Step 5: Revisión visual (el usuario)**

Con `pnpm dev` y los datos realistas cargados, abrir `/dashboard` y comprobar:
- Los KPIs muestran 60, 3.000, 50,0:1 y un índice cercano al 2 %, con el tooltip del índice.
- Las causas de mortalidad en vino y las de morbilidad en ámbar, la mayor arriba, con `n (%)` al final de cada barra y sin recortes.
- El resumen de IA aparece al final, plegado, con el aviso al abrirlo.
- La barra de filtros no tiene "Día de Reporte" y ya no se queda fija.
- Comparar con la sensación de "sopa" anterior: ¿qué sigue sobrando?
