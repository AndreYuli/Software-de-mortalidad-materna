# Actualizar Gráficas de Generalidades con CIE-10 Real y Edad Gestacional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Actualizar (no crear paralelo) las gráficas existentes de "Generalidades" para usar el catálogo oficial completo de CIE-10 (12,634 códigos, provisto por el cliente) en vez del diccionario de ~25 entradas hardcodeado; dividir el gráfico combinado "Top 5 Causas Principales" en dos gráficos reales de Top 10 (una por causa básica de muerte para Mortalidad, otra por causa principal para Morbilidad); y reemplazar la gráfica de "Edad materna" (construida en un plan anterior) por "Edad Gestacional" en Factores Demográficos de Morbilidad y Mortalidad, según la tabla de variables que el cliente confirmó como definitiva.

**Architecture:** Se genera un JSON estático de código→nombre CIE-10 a partir del Excel de referencia oficial (`ayudas/TablaReferencia_CIE10__1.xlsx`, no versionado) mediante un script de un solo uso, y se importa en el frontend reemplazando el diccionario hardcodeado — mismo mecanismo (`getCie10Description`), solo cambia la fuente de datos. En el backend se factoriza la lógica de "top N causas CIE-10" a `ProcesadorBase` para que tanto Mortalidad (causa básica) como Morbilidad (causa principal, nueva) la reutilicen sin duplicar código. La gráfica de "Edad materna" se reemplaza in situ (mismo patrón de componente, subpestaña y wiring) por "Edad Gestacional", con cortes clínicos estándar (pretérmino/a término/postérmino) en vez de los cortes de riesgo por edad materna.

**Tech Stack:** FastAPI + pandas (backend), React 18 + TypeScript + Chart.js (frontend), pytest y Vitest.

---

## Contexto y decisiones ya tomadas con el usuario

- El usuario confirmó: la gráfica de "Edad Gestacional" en Factores Demográficos **reemplaza** (no complementa) la de "Edad materna" que se había construido en el plan anterior (`docs/historico/plans/2026-08-30-edad-riesgo-sociodemografico.md`).
- El usuario confirmó: los Top 10 de causas se hacen **actualizando** el gráfico "Top 5 Causas Principales" existente en la pestaña Generalidades, convirtiéndolo en 2 gráficos separados de Top 10 (mortalidad y morbilidad), con nombres reales del CIE-10.
- El Excel de referencia CIE-10 (`ayudas/TablaReferencia_CIE10__1.xlsx`) tiene 12,634 filas, columnas `Codigo`/`Nombre`/`Descripcion` (entre otras). La columna `Nombre` es la descripción específica a 4 caracteres (ej. `O141` → `PREECLAMPSIA SEVERA`), que es el nivel de detalle que coincide con los códigos que ya vienen en los datos (`causas_cie10.top_causas[].codigo`). La columna `Descripcion` es una categoría más general (3 caracteres) y no se usa en este plan.
- No se modifican `analizar_obstetrico_por_edad` (los 4 grupos `<20/20-29/30-39/≥40` que usan `ClusteringSection` y `ObstetricoEdadSection`) ni `Instituciones de Referencia`, `Tiempo de Remisión`, `Severidad de Fallas`, `Sankey`, `Heatmap de Demoras` — nada de eso cambia en este plan.

## File Structure

- Create: `BACKEND/scripts/generate_cie10_reference.py` — script de un solo uso para generar el JSON desde el Excel.
- Create: `FRONTED/maternanalytics/src/constants/cie10Nombres.json` — generado por el script anterior (12,634 entradas código→nombre).
- Modify: `FRONTED/maternanalytics/src/constants/dashboardConstants.ts` — usar el JSON real en vez del diccionario hardcodeado.
- Create: `FRONTED/maternanalytics/src/constants/dashboardConstants.test.ts`
- Modify: `BACKEND/services/procesador_base.py` — factorizar `_analizar_causas_cie10`; reemplazar `analizar_distribucion_edad_riesgo` por `analizar_distribucion_edad_gestacional`.
- Modify: `BACKEND/services/_mortalidad_processor.py` — `analizar_causas_cie10` usa el helper factorizado, `top_n` por defecto a 10.
- Modify: `BACKEND/services/_morbilidad_processor.py` — nuevo `analizar_causas_cie10` sobre "Causa principal CIE-10".
- Modify: `BACKEND/services/_analisis_calculo.py` — exponer `causas_cie10` para morbilidad, `distribucion_edad_gestacional` en vez de `distribucion_edad_riesgo`, `top_n=10` para ambos.
- Modify: `BACKEND/tests/fixtures_sivigila.py` — agregar columnas de semanas de gestación (mortalidad) y causa principal CIE-10 (morbilidad).
- Modify: `BACKEND/tests/test_mortalidad_processor.py`, `BACKEND/tests/test_morbilidad_processor.py`
- Modify: `FRONTED/maternanalytics/src/types.ts` — renombrar campo.
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.ts`, `.test.ts` — reemplazar `getEdadRiesgoAiInsight` por `getEdadGestacionalAiInsight`.
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts` — quitar `barChartData`, agregar `topCausasMortalidad`/`topCausasMorbilidad`, renombrar `edadRiesgo*` a `edadGestacional*`.
- Delete: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx` y su test.
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadGestacional.tsx` y su test.
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`, `.test.tsx` — reemplazar el gráfico combinado por 2 gráficos de Top 10.
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx` — wiring final.

---

### Task 1: Datos reales de CIE-10

**Files:**
- Create: `BACKEND/scripts/generate_cie10_reference.py`
- Create: `FRONTED/maternanalytics/src/constants/cie10Nombres.json` (generado, no escrito a mano)
- Modify: `FRONTED/maternanalytics/src/constants/dashboardConstants.ts`
- Test: `FRONTED/maternanalytics/src/constants/dashboardConstants.test.ts`

- [ ] **Step 1: Crear el script de generación**

```python
"""Genera el catálogo JSON de descripciones CIE-10 para el frontend.

Lee la tabla de referencia oficial (Excel, provista por el cliente) y
produce un archivo JSON código -> nombre que el frontend usa para
etiquetar las causas de morbilidad y mortalidad en las gráficas. Se
ejecuta manualmente cuando la tabla de referencia se actualiza; el JSON
generado se versiona como código fuente del frontend.

Uso:
    BACKEND/venv/Scripts/python.exe scripts/generate_cie10_reference.py
"""

import json
from pathlib import Path

import pandas as pd

_EXCEL_PATH = Path(__file__).resolve().parent.parent.parent / "ayudas" / "TablaReferencia_CIE10__1.xlsx"
_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "FRONTED"
    / "maternanalytics"
    / "src"
    / "constants"
    / "cie10Nombres.json"
)


def main() -> None:
    """Lee el Excel de referencia y escribe el JSON código -> nombre."""
    df = pd.read_excel(_EXCEL_PATH, usecols=["Codigo", "Nombre"])
    df = df.dropna(subset=["Codigo", "Nombre"])
    mapping = {
        str(codigo).strip().upper(): str(nombre).strip().title()
        for codigo, nombre in zip(df["Codigo"], df["Nombre"])
    }
    _OUTPUT_PATH.write_text(json.dumps(mapping, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"Escritas {len(mapping)} descripciones CIE-10 en {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ejecutar el script y confirmar el JSON generado**

Run: `cd BACKEND && ./venv/Scripts/python.exe scripts/generate_cie10_reference.py`
Expected: imprime algo como `Escritas 12634 descripciones CIE-10 en .../cie10Nombres.json`, y el archivo `FRONTED/maternanalytics/src/constants/cie10Nombres.json` existe.

Verificar manualmente (por ejemplo con `python -c "import json; d=json.load(open('FRONTED/maternanalytics/src/constants/cie10Nombres.json', encoding='utf-8')); print(d['O141'])"` desde la raíz del repo) que `d["O141"]` sea `"Preeclampsia Severa"`.

- [ ] **Step 3: Escribir el test que falla para `getCie10Description`**

```ts
import { describe, it, expect } from 'vitest'
import { getCie10Description } from './dashboardConstants'

describe('getCie10Description', () => {
  it('resuelve un código real del catálogo CIE-10, con o sin punto', () => {
    expect(getCie10Description('O141')).toBe('Preeclampsia Severa')
    expect(getCie10Description('O14.1')).toBe('Preeclampsia Severa')
  })

  it('retorna el mensaje por defecto para un código inexistente', () => {
    expect(getCie10Description('Z999999')).toBe('Descripción no disponible')
  })

  it('retorna el mensaje por defecto para un código vacío o nulo', () => {
    expect(getCie10Description('')).toBe('Descripción no disponible')
    expect(getCie10Description(null)).toBe('Descripción no disponible')
  })
})
```

- [ ] **Step 4: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/constants/dashboardConstants.test.ts`
Expected: FAIL en el primer test — `getCie10Description('O141')` todavía devuelve `'Descripción no disponible'` porque `dashboardConstants.ts` sigue usando el diccionario hardcodeado de 25 entradas (que no incluye `O141` con esa clave exacta) y la normalización actual no quita el punto de `O14.1` de forma consistente con el nuevo dato.

- [ ] **Step 5: Actualizar `dashboardConstants.ts` para usar el catálogo real**

Buscar (líneas 47-84 del archivo actual):

```ts
export const CIE10_DESCRIPTIONS: Record<string, string> = {
  'O14': 'Hipertensión gestacional con preeclampsia',
  'O14.1': 'Hipertensión gestacional con preeclampsia severa',
  'O15': 'Eclampsia',
  'O15.0': 'Eclampsia en el embarazo',
  'O72': 'Hemorragia posparto',
  'O72.1': 'Hemorragia posparto inmediata',
  'O85': 'Sepsis puerperal',
  'O88': 'Embolia obstétrica',
  'O94': 'Secuelas de complicaciones obstétricas',
  'O98': 'Infecciones maternas que complican el embarazo',
  'O98.0': 'Tuberculosis en embarazo',
  'O41.1': 'Corioamnionitis (Infección de saco amniótico)',
  'O08.1': 'Hemorragia por aborto o ectópico',
  'O44.0': 'Placenta previa con hemorragia',
  'O99.3': 'Trastornos mentales o nerviosos en embarazo',
  'O26.6': 'Trastornos del hígado en embarazo',
  'O10.0': 'Hipertensión crónica preexistente',
  'O20.0': 'Amenaza de aborto',
  'O00.1': 'Embarazo ectópico tubárico',
  'O36.4': 'Muerte fetal intrauterina',
  'O62.1': 'Inercia uterina / fallo contracción',
  'O34.2': 'Cicatriz uterina por cesárea previa',
  'O11': 'Hipertensión crónica con preeclampsia sobreagregada',
  'O46.0': 'Hemorragia anteparto con coagulopatía',
  'O24.4': 'Diabetes gestacional',
}

export const CLUSTER_COLORS = ['#0066cc', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad']

export function getCie10Description(code: unknown): string {
  const normalized = String(code ?? '').trim().toUpperCase().replace(/\s+/g, '');
  if (!normalized) return 'Descripción no disponible';
  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized];
  const prefix3 = normalized.slice(0, 3);
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3];
  return 'Descripción no disponible';
}
```

Reemplazar por:

```ts
export const CIE10_DESCRIPTIONS: Record<string, string> = cie10Nombres

export const CLUSTER_COLORS = ['#0066cc', '#c0392b', '#2ca02c', '#f39c12', '#6f42c1', '#16a085', '#d35400', '#8e44ad']

export function getCie10Description(code: unknown): string {
  const normalized = String(code ?? '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (!normalized) return 'Descripción no disponible';
  if (CIE10_DESCRIPTIONS[normalized]) return CIE10_DESCRIPTIONS[normalized];
  const prefix3 = normalized.slice(0, 3);
  if (CIE10_DESCRIPTIONS[prefix3]) return CIE10_DESCRIPTIONS[prefix3];
  return 'Descripción no disponible';
}
```

Nota importante: la normalización cambió de `.replace(/\s+/g, '')` (solo quitaba espacios) a `.replace(/[^A-Z0-9]/g, '')` (quita cualquier caracter que no sea letra/número, incluyendo el punto). Esto es necesario porque el catálogo real usa códigos sin punto (`O141`), mientras que los datos de origen pueden traer el código con punto (`O14.1`) — ambos deben normalizar al mismo valor para hacer match.

Y agregar el import al inicio del archivo (antes de `export const COLUMNAS_MORTALIDAD`, línea 1 actual):

```ts
import cie10Nombres from './cie10Nombres.json'

```

- [ ] **Step 6: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/constants/dashboardConstants.test.ts`
Expected: PASS (4 tests)

- [ ] **Step 7: Verificar tipos y la suite completa**

Run: `cd FRONTED/maternanalytics && npx tsc --noEmit && npm test`
Expected: sin errores de tipos (confirma que `resolveJsonModule` en `tsconfig.json` ya está habilitado y el import de JSON tipa correctamente); toda la suite pasa.

- [ ] **Step 8: Commit**

```bash
git add BACKEND/scripts/generate_cie10_reference.py FRONTED/maternanalytics/src/constants/cie10Nombres.json FRONTED/maternanalytics/src/constants/dashboardConstants.ts FRONTED/maternanalytics/src/constants/dashboardConstants.test.ts
git commit -m "feat: usar catalogo real de CIE-10 en vez del diccionario hardcodeado"
```

---

### Task 2: Backend — Top 10 causas de morbilidad (factorizar y reutilizar)

**Files:**
- Modify: `BACKEND/services/procesador_base.py`
- Modify: `BACKEND/services/_mortalidad_processor.py`
- Modify: `BACKEND/services/_morbilidad_processor.py`
- Modify: `BACKEND/services/_analisis_calculo.py`
- Modify: `BACKEND/tests/fixtures_sivigila.py`
- Test: `BACKEND/tests/test_morbilidad_processor.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `BACKEND/tests/fixtures_sivigila.py`, dentro de `df_morbilidad_ejemplo()`, una nueva columna `"Causa principal CIE-10"`. Buscar:

```python
            "Tiempo remisión (h)": [2.5, 1.0, 4.0, 0.5, 3.0, 6.0],
        }
    )
```

Reemplazar por:

```python
            "Tiempo remisión (h)": [2.5, 1.0, 4.0, 0.5, 3.0, 6.0],
            "Causa principal CIE-10": ["O141", "O721", "O141", "O150", "O721", "O141"],
        }
    )
```

Agregar al final de `BACKEND/tests/test_morbilidad_processor.py`:

```python
def test_analizar_causas_cie10_top_causas():
    """El top de causas CIE-10 de morbilidad debe respetar top_n y los conteos."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_causas_cie10(top_n=5)
    assert resultado["total_causas_unicas"] == 3
    top = {c["codigo"]: c["casos"] for c in resultado["top_causas"]}
    assert top["O141"] == 3
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest tests/test_morbilidad_processor.py -q`
Expected: FAIL — `AttributeError: 'MorbilidadProcessor' object has no attribute 'analizar_causas_cie10'`

- [ ] **Step 3: Factorizar la lógica compartida en `ProcesadorBase`**

Agregar en `BACKEND/services/procesador_base.py`, como método nuevo de la clase (después de `analizar_obstetrico_por_edad`, antes de `analizar_distribucion_edad_riesgo` — ese método se toca en la Task 3, no lo modifiques aquí):

```python
    def _analizar_causas_cie10(self, columna: str, top_n: int) -> dict[str, Any]:
        """Identifica las causas más frecuentes codificadas en CIE-10 de una columna.

        Args:
            columna: Nombre de la columna con el código CIE-10 de la causa.
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas (código, casos, porcentaje) y
            total_causas_unicas. Dict vacío si la columna no existe.
        """
        resultado: dict[str, Any] = {}
        if columna not in self.df.columns:
            return resultado
        total_casos = len(self.df)
        causas = self.df[columna].value_counts().head(top_n)
        top_causas: list[dict[str, Any]] = [
            {
                "codigo": str(k),
                "casos": int(v),
                "porcentaje": float(v / total_casos * 100) if total_casos > 0 else 0.0,
            }
            for k, v in causas.items()
        ]
        resultado = {
            "top_causas": top_causas,
            "total_causas_unicas": int(self.df[columna].nunique()),
        }
        return resultado
```

- [ ] **Step 4: Reutilizar el helper en `MortalidadProcessor`**

En `BACKEND/services/_mortalidad_processor.py`, buscar:

```python
    def analizar_causas_cie10(self, top_n: int = 15) -> dict[str, Any]:
        """Identifica las causas de muerte más frecuentes codificadas en CIE-10.

        Args:
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas y total_causas_unicas.
        """
        resultado: dict[str, Any] = {}
        if _COLUMNA_CAUSA_BASICA in self.df.columns:
            total_casos = len(self.df)
            causas = self.df[_COLUMNA_CAUSA_BASICA].value_counts().head(top_n)
            top_causas: list[dict[str, Any]] = [
                {
                    "codigo": str(k),
                    "casos": int(v),
                    "porcentaje": float(v / total_casos * 100) if total_casos > 0 else 0.0,
                }
                for k, v in causas.items()
            ]
            resultado = {
                "top_causas": top_causas,
                "total_causas_unicas": int(self.df[_COLUMNA_CAUSA_BASICA].nunique()),
            }
        return resultado
```

Reemplazar por:

```python
    def analizar_causas_cie10(self, top_n: int = 10) -> dict[str, Any]:
        """Identifica las causas de muerte más frecuentes codificadas en CIE-10.

        Args:
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas y total_causas_unicas.
        """
        return self._analizar_causas_cie10(_COLUMNA_CAUSA_BASICA, top_n)
```

- [ ] **Step 5: Agregar el método en `MorbilidadProcessor`**

En `BACKEND/services/_morbilidad_processor.py`, agregar la constante de módulo junto a las otras (después de `_COLS_SEVERIDAD`, antes de `def _normalizar`):

```python
_COLUMNA_CAUSA_PRINCIPAL = "Causa principal CIE-10"
```

Y agregar el método público en la clase `MorbilidadProcessor`, justo antes de `def analizar_obstetrico_por_edad(self)`:

```python
    def analizar_causas_cie10(self, top_n: int = 10) -> dict[str, Any]:
        """Identifica las causas principales más frecuentes codificadas en CIE-10.

        Args:
            top_n: Número de causas más frecuentes a incluir.

        Returns:
            Dict con top_causas y total_causas_unicas.
        """
        return self._analizar_causas_cie10(_COLUMNA_CAUSA_PRINCIPAL, top_n)
```

- [ ] **Step 6: Ejecutar el test y verificar que pasa**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest tests/test_morbilidad_processor.py tests/test_mortalidad_processor.py -q`
Expected: todos pasan (el test existente `test_analizar_causas_cie10_top_causas` de mortalidad sigue pasando porque pasa `top_n=5` explícito, no se ve afectado por el cambio del valor por defecto).

- [ ] **Step 7: Exponer `causas_cie10` de morbilidad y ajustar `top_n` en `_analisis_calculo.py`**

Buscar:

```python
        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = {
                **meta,
                "tipo": "mortalidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "momento_muerte": p.analizar_momento_muerte(),
                "demoras": p.analizar_demoras(),
                "causas_cie10": p.analizar_causas_cie10(top_n=15),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "heatmap_demoras": p.analizar_heatmap_causa_demoras(top_n=20),
                "sankey_flujo": p.analizar_sankey_flujo(),
            }
        else:
            p = MorbilidadProcessor(df)
            resultado = {
                **meta,
                "tipo": "morbilidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "criterios_inclusion": p.analizar_criterios_inclusion(),
                "momento_ocurrencia": p.analizar_momento_ocurrencia(),
                "institucion_referencia": p.analizar_institucion_referencia(),
                "tiempo_remision": p.analizar_tiempo_remision(),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "severidad_fallas": p.analizar_severidad_fallas(),
            }
```

Reemplazar por (nota: en este Task solo cambia `top_n=15` a `top_n=10` y se agrega `"causas_cie10"` a la rama morbilidad; la clave `distribucion_edad_riesgo` se toca en la Task 3, déjala igual por ahora):

```python
        if analisis.tipo == "mortalidad":
            p = MortalidadProcessor(df)
            resultado: dict[str, Any] = {
                **meta,
                "tipo": "mortalidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "momento_muerte": p.analizar_momento_muerte(),
                "demoras": p.analizar_demoras(),
                "causas_cie10": p.analizar_causas_cie10(top_n=10),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "heatmap_demoras": p.analizar_heatmap_causa_demoras(top_n=20),
                "sankey_flujo": p.analizar_sankey_flujo(),
            }
        else:
            p = MorbilidadProcessor(df)
            resultado = {
                **meta,
                "tipo": "morbilidad",
                "estadisticas_basicas": p.calcular_estadisticas_basicas(),
                "causas_cie10": p.analizar_causas_cie10(top_n=10),
                "criterios_inclusion": p.analizar_criterios_inclusion(),
                "momento_ocurrencia": p.analizar_momento_ocurrencia(),
                "institucion_referencia": p.analizar_institucion_referencia(),
                "tiempo_remision": p.analizar_tiempo_remision(),
                "obstetrico_edad": p.analizar_obstetrico_por_edad(),
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
                "severidad_fallas": p.analizar_severidad_fallas(),
            }
```

- [ ] **Step 8: Verificar la suite completa de backend**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests pasan, sin regresiones.

- [ ] **Step 9: Commit**

```bash
git add BACKEND/services/procesador_base.py BACKEND/services/_mortalidad_processor.py BACKEND/services/_morbilidad_processor.py BACKEND/services/_analisis_calculo.py BACKEND/tests/fixtures_sivigila.py BACKEND/tests/test_morbilidad_processor.py
git commit -m "feat: agregar top 10 causas CIE-10 para morbilidad reutilizando la logica de mortalidad"
```

---

### Task 3: Backend — reemplazar Edad de Riesgo por Edad Gestacional

**Files:**
- Modify: `BACKEND/services/procesador_base.py`
- Modify: `BACKEND/services/_analisis_calculo.py`
- Modify: `BACKEND/tests/fixtures_sivigila.py`
- Modify: `BACKEND/tests/test_mortalidad_processor.py`
- Modify: `BACKEND/tests/test_morbilidad_processor.py`

- [ ] **Step 1: Agregar la columna de semanas de gestación al fixture de mortalidad**

En `BACKEND/tests/fixtures_sivigila.py`, dentro de `df_mortalidad_ejemplo()`, buscar:

```python
            "10.3.4 Demora 4": [1, 1, 0, 1, 0, 0],
        }
    )
```

Reemplazar por:

```python
            "10.3.4 Demora 4": [1, 1, 0, 1, 0, 0],
            "9.2 Semana gestación": [26, 32, 38, 40, 42, 35],
        }
    )
```

- [ ] **Step 2: Escribir los tests que fallan**

En `BACKEND/tests/test_mortalidad_processor.py`, buscar el test existente:

```python
def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 5, 1]
    assert resultado["total"] == 6
```

Reemplazarlo por:

```python
def test_analizar_distribucion_edad_gestacional_agrupa_por_categorias_clinicas():
    """Debe agrupar en <28, 28-36, 37-41 y >=42 semanas de gestacion."""
    p = MortalidadProcessor(df_mortalidad_ejemplo())
    resultado = p.analizar_distribucion_edad_gestacional()
    assert resultado["labels"] == ["<28 semanas", "28-36 semanas", "37-41 semanas", "≥42 semanas"]
    assert resultado["valores"] == [1, 2, 2, 1]
    assert resultado["total"] == 6
```

En `BACKEND/tests/test_morbilidad_processor.py`, buscar el test existente:

```python
def test_analizar_distribucion_edad_riesgo_agrupa_por_cortes_de_riesgo():
    """Debe agrupar en <19, 19-34 y >=35 anos usando los cortes de riesgo obstetrico."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_distribucion_edad_riesgo()
    assert resultado["labels"] == ["<19 años", "19-34 años", "≥35 años"]
    assert resultado["valores"] == [0, 6, 0]
    assert resultado["total"] == 6
```

Reemplazarlo por:

```python
def test_analizar_distribucion_edad_gestacional_agrupa_por_categorias_clinicas():
    """Debe agrupar en <28, 28-36, 37-41 y >=42 semanas de gestacion."""
    p = MorbilidadProcessor(df_morbilidad_ejemplo())
    resultado = p.analizar_distribucion_edad_gestacional()
    assert resultado["labels"] == ["<28 semanas", "28-36 semanas", "37-41 semanas", "≥42 semanas"]
    assert resultado["valores"] == [1, 5, 0, 0]
    assert resultado["total"] == 6
```

- [ ] **Step 3: Ejecutar los tests y verificar que fallan**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest tests/test_mortalidad_processor.py tests/test_morbilidad_processor.py -q`
Expected: 2 FAILs — `AttributeError: ... object has no attribute 'analizar_distribucion_edad_gestacional'`

- [ ] **Step 4: Reemplazar el método en `procesador_base.py`**

Buscar el método completo (agregado en un plan anterior):

```python
    def analizar_distribucion_edad_riesgo(self) -> dict[str, Any]:
        """Agrupa los casos por los cortes de edad de mayor riesgo obstétrico.

        Los cortes (<19, 19-34, ≥35 años) son los definidos por la experta de
        dominio para priorizar el seguimiento de los extremos de edad
        materna, y son distintos de los 4 grupos usados en
        `analizar_obstetrico_por_edad` (que sirven para cruces con otras
        variables obstétricas, no para esta distribución simple).

        Returns:
            Dict con 'labels' (nombres de los 3 grupos), 'valores' (conteo
            de casos por grupo) y 'total' (casos con edad registrada). Dict
            vacío si no hay columna 'Edad' o no hay datos válidos.
        """
        resultado: dict[str, Any] = {}
        if "Edad" not in self.df.columns:
            return resultado
        edades = pd.to_numeric(self.df["Edad"], errors="coerce").dropna()
        if edades.empty:
            return resultado

        grupos = [
            {"label": "<19 años", "min": 0, "max": 18},
            {"label": "19-34 años", "min": 19, "max": 34},
            {"label": "≥35 años", "min": 35, "max": 120},
        ]
        valores = [int(((edades >= g["min"]) & (edades <= g["max"])).sum()) for g in grupos]
        resultado = {
            "labels": [g["label"] for g in grupos],
            "valores": valores,
            "total": int(len(edades)),
        }
        return resultado
```

Reemplazarlo completamente por:

```python
    def analizar_distribucion_edad_gestacional(self) -> dict[str, Any]:
        """Agrupa los casos por semanas de gestación en categorías clínicas estándar.

        Los cortes (<28, 28-36, 37-41, ≥42 semanas) distinguen partos
        pretérmino, a término y postérmino, categorías clínicas estándar
        para evaluar el riesgo asociado a la duración de la gestación.
        Mortalidad y morbilidad usan columnas de origen distintas, por eso
        se busca la primera que exista.

        Returns:
            Dict con 'labels' (nombres de los 4 grupos), 'valores' (conteo
            de casos por grupo) y 'total' (casos con semanas de gestación
            registradas). Dict vacío si no hay columna de semanas de
            gestación o no hay datos válidos.
        """
        columna = next(
            (
                c
                for c in ("9.2 Semana gestación", "Edad gestacional ocurrencia (sem)")
                if c in self.df.columns
            ),
            None,
        )
        if columna is None:
            return {}
        semanas = pd.to_numeric(self.df[columna], errors="coerce").dropna()
        if semanas.empty:
            return {}

        grupos = [
            {"label": "<28 semanas", "min": 0, "max": 27},
            {"label": "28-36 semanas", "min": 28, "max": 36},
            {"label": "37-41 semanas", "min": 37, "max": 41},
            {"label": "≥42 semanas", "min": 42, "max": 99},
        ]
        valores = [int(((semanas >= g["min"]) & (semanas <= g["max"])).sum()) for g in grupos]
        return {
            "labels": [g["label"] for g in grupos],
            "valores": valores,
            "total": int(len(semanas)),
        }
```

- [ ] **Step 5: Actualizar `_analisis_calculo.py`**

En ambas ramas de `calcular_completo` (mortalidad y morbilidad), buscar:

```python
                "distribucion_edad_riesgo": p.analizar_distribucion_edad_riesgo(),
```

Reemplazar (en las DOS ocurrencias) por:

```python
                "distribucion_edad_gestacional": p.analizar_distribucion_edad_gestacional(),
```

- [ ] **Step 6: Ejecutar los tests y verificar que pasan**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests pasan, sin regresiones.

- [ ] **Step 7: Commit**

```bash
git add BACKEND/services/procesador_base.py BACKEND/services/_analisis_calculo.py BACKEND/tests/fixtures_sivigila.py BACKEND/tests/test_mortalidad_processor.py BACKEND/tests/test_morbilidad_processor.py
git commit -m "feat: reemplazar distribucion de edad materna por edad gestacional"
```

---

### Task 4: Frontend — tipo, resumen de IA y extracción del hook

**Files:**
- Modify: `FRONTED/maternanalytics/src/types.ts`
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.ts`
- Modify: `FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts`
- Modify: `FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts`

- [ ] **Step 1: Renombrar el campo en `types.ts`**

Buscar:

```ts
  distribucion_edad_riesgo?: { labels: string[]; valores: number[]; total: number }
```

Reemplazar por:

```ts
  distribucion_edad_gestacional?: { labels: string[]; valores: number[]; total: number }
```

- [ ] **Step 2: Escribir los tests que fallan para `getEdadGestacionalAiInsight`**

En `FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts`, buscar los dos tests existentes:

```ts
  it('genera resumen de distribucion de edad de riesgo', () => {
    const data = { labels: ['<19 años', '19-34 años', '≥35 años'], valores: [1, 3, 2], total: 6 }
    const result = getEdadRiesgoAiInsight(data, 'Mortalidad')
    expect(result).toContain('mortalidad')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('retorna null para distribucion de edad de riesgo sin datos', () => {
    expect(getEdadRiesgoAiInsight(null, 'Morbilidad')).toBeNull()
  })
```

Reemplazarlos por:

```ts
  it('genera resumen de distribucion de edad gestacional', () => {
    const data = { labels: ['<28 semanas', '28-36 semanas', '37-41 semanas', '≥42 semanas'], valores: [1, 2, 2, 1], total: 6 }
    const result = getEdadGestacionalAiInsight(data, 'Mortalidad')
    expect(result).toContain('mortalidad')
    expect(result).not.toMatch(/\d+\.\d+%/)
  })

  it('retorna null para distribucion de edad gestacional sin datos', () => {
    expect(getEdadGestacionalAiInsight(null, 'Morbilidad')).toBeNull()
  })
```

Y actualizar el import: buscar `getEdadRiesgoAiInsight` en la lista de imports desde `'./aiChartInsights'` y reemplazarlo por `getEdadGestacionalAiInsight`.

- [ ] **Step 3: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/utils/aiChartInsights.test.ts`
Expected: FAIL — `getEdadGestacionalAiInsight is not a function` (o error de import).

- [ ] **Step 4: Reemplazar la función en `aiChartInsights.ts`**

Buscar:

```ts
export function getEdadRiesgoAiInsight(
  data: { labels: string[]; valores: number[]; total: number } | null,
  evento: 'Morbilidad' | 'Mortalidad',
): string | null {
  if (!data || data.total === 0) return null

  const casosRiesgo = (data.valores[0] || 0) + (data.valores[2] || 0)
  const riesgoPct = pct(casosRiesgo, data.total)

  return `El ${riesgoPct}% de los casos de ${evento.toLowerCase()} (${casosRiesgo} de ${data.total} pacientes) ocurrieron en los grupos de mayor riesgo obstétrico: menores de 19 años o de 35 años en adelante.`
}
```

Reemplazar por:

```ts
export function getEdadGestacionalAiInsight(
  data: { labels: string[]; valores: number[]; total: number } | null,
  evento: 'Morbilidad' | 'Mortalidad',
): string | null {
  if (!data || data.total === 0) return null

  const casosATermino = data.valores[2] || 0
  const casosFueraDeTermino = data.total - casosATermino
  const riesgoPct = pct(casosFueraDeTermino, data.total)

  return `El ${riesgoPct}% de los casos de ${evento.toLowerCase()} (${casosFueraDeTermino} de ${data.total} pacientes) tuvieron una gestación fuera del rango a término (37-41 semanas): parto pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante).`
}
```

- [ ] **Step 5: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/utils/aiChartInsights.test.ts`
Expected: PASS (todos los tests del archivo).

- [ ] **Step 6: Reemplazar `barChartData` por `topCausasMortalidad`/`topCausasMorbilidad`, y renombrar `edadRiesgo*` en `useDashboardCharts.ts`**

Buscar el bloque completo de `barChartData`:

```ts
  const barChartData = useMemo(() => {
    const list: { label: string; casos: number; color: string }[] = []
    if ((segmento === 'ambos' || segmento === 'mortalidad') && mortalidadData?.causas_cie10?.top_causas) {
      mortalidadData.causas_cie10.top_causas.forEach((c) => {
        list.push({ label: getCie10Description(c.codigo), casos: c.casos, color: '#c0392b' })
      })
    }
    if ((segmento === 'ambos' || segmento === 'morbilidad') && morbilidadData?.criterios_inclusion) {
      Object.values(morbilidadData.criterios_inclusion).forEach((c) => {
        list.push({ label: `${c.nombre}`, casos: c.casos, color: '#2ca02c' })
      })
    }

    const sorted = list.sort((a, b) => b.casos - a.casos).slice(0, 5).reverse()
    return {
      labels: sorted.map((i) => i.label),
      values: sorted.map((i) => i.casos),
      colors: sorted.map((i) => i.color),
    }
  }, [segmento, mortalidadData, morbilidadData])
```

Reemplazarlo por:

```ts
  const topCausasMortalidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'mortalidad')) {
      return { labels: [], values: [], colors: [] }
    }
    const causas = mortalidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10).reverse()
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => '#c0392b'),
    }
  }, [segmento, mortalidadData])

  const topCausasMorbilidad = useMemo(() => {
    if (!(segmento === 'ambos' || segmento === 'morbilidad')) {
      return { labels: [], values: [], colors: [] }
    }
    const causas = morbilidadData?.causas_cie10?.top_causas ?? []
    const sorted = [...causas].sort((a, b) => b.casos - a.casos).slice(0, 10).reverse()
    return {
      labels: sorted.map((c) => getCie10Description(c.codigo)),
      values: sorted.map((c) => c.casos),
      colors: sorted.map(() => '#2ca02c'),
    }
  }, [segmento, morbilidadData])
```

Buscar:

```ts
  const edadRiesgoMortalidad = useMemo(() => {
    return mortalidadData?.distribucion_edad_riesgo ?? null
  }, [mortalidadData])

  const edadRiesgoMorbilidad = useMemo(() => {
    return morbilidadData?.distribucion_edad_riesgo ?? null
  }, [morbilidadData])
```

Reemplazar por:

```ts
  const edadGestacionalMortalidad = useMemo(() => {
    return mortalidadData?.distribucion_edad_gestacional ?? null
  }, [mortalidadData])

  const edadGestacionalMorbilidad = useMemo(() => {
    return morbilidadData?.distribucion_edad_gestacional ?? null
  }, [morbilidadData])
```

Por último, buscar la línea final de retorno del hook:

```ts
  return { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, edadRiesgoMortalidad, edadRiesgoMorbilidad, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData }
```

Reemplazarla por:

```ts
  return { lineChartData, topCausasMortalidad, topCausasMorbilidad, activeClusterData, clusteringChartData, demorasChartData, edadChartData, edadGestacionalMortalidad, edadGestacionalMorbilidad, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData }
```

- [ ] **Step 7: Verificar tipos**

Run: `cd FRONTED/maternanalytics && npx tsc --noEmit`
Expected: errores de tipos en `TrendChartsRow.tsx` y `AnalysisHomeSection.tsx` (esos archivos todavía usan `barChartData`/`edadRiesgo*`/`DistribucionEdadRiesgo` — se corrigen en las Tasks 5, 6 y 7). Estos errores son esperados en este punto del plan; no los arregles en esta task.

- [ ] **Step 8: Commit**

```bash
git add FRONTED/maternanalytics/src/types.ts FRONTED/maternanalytics/src/utils/aiChartInsights.ts FRONTED/maternanalytics/src/utils/aiChartInsights.test.ts FRONTED/maternanalytics/src/hooks/dashboard/useDashboardCharts.ts
git commit -m "feat: reemplazar edad de riesgo por edad gestacional y barChartData por top causas por evento"
```

Nota: este commit deja el build roto a propósito (TrendChartsRow y AnalysisHomeSection aún no se actualizaron); eso se corrige en las siguientes 3 tasks, que deben ejecutarse en orden inmediatamente después.

---

### Task 5: Frontend — reemplazar el componente `DistribucionEdadRiesgo` por `DistribucionEdadGestacional`

**Files:**
- Delete: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx`
- Delete: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.test.tsx`
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadGestacional.tsx`
- Create: `FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadGestacional.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DistribucionEdadGestacional } from './DistribucionEdadGestacional'

const sampleData = { labels: ['<28 semanas', '28-36 semanas', '37-41 semanas', '≥42 semanas'], valores: [1, 2, 2, 1], total: 6 }

describe('DistribucionEdadGestacional', () => {
  it('renderiza el titulo con el nombre del evento cuando hay datos', () => {
    render(<DistribucionEdadGestacional data={sampleData} evento="Mortalidad" />)
    expect(screen.getByText('Distribución por Edad Gestacional (Mortalidad)')).toBeInTheDocument()
  })

  it('muestra un mensaje de datos insuficientes cuando no hay datos', () => {
    render(<DistribucionEdadGestacional data={null} evento="Morbilidad" />)
    expect(screen.getByText('No hay datos suficientes de edad gestacional para generar esta gráfica.')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/DistribucionEdadGestacional.test.tsx`
Expected: FAIL — `Cannot find module './DistribucionEdadGestacional'`

- [ ] **Step 3: Crear el componente**

```tsx
import { useMemo } from 'react'
import { Bar } from 'react-chartjs-2'
import { CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import { getEdadGestacionalAiInsight } from '../../utils/aiChartInsights'

export interface DistribucionEdadGestacionalData {
  labels: string[]
  valores: number[]
  total: number
}

export interface DistribucionEdadGestacionalProps {
  data: DistribucionEdadGestacionalData | null
  evento: 'Morbilidad' | 'Mortalidad'
}

const GESTACIONAL_COLORS = ['#dc2626', '#f59e0b', '#0066cc', '#dc2626']

export function DistribucionEdadGestacional({ data, evento }: DistribucionEdadGestacionalProps) {
  const insight = useMemo(() => getEdadGestacionalAiInsight(data, evento), [data, evento])

  if (!data || data.labels.length === 0) {
    return (
      <div className="chart-card-col-12" style={{ textAlign: 'center', padding: '40px' }}>
        <h3 className="chart-card-title">Distribución por Edad Gestacional</h3>
        <p style={{ color: '#64748b' }}>No hay datos suficientes de edad gestacional para generar esta gráfica.</p>
      </div>
    )
  }

  return (
    <div className="chart-card-col-12">
      <h3 className="chart-card-title">Distribución por Edad Gestacional ({evento})</h3>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>
        Los partos pretérmino (antes de la semana 37) o postérmino (semana 42 en adelante) tienen mayor riesgo de morbilidad y mortalidad materna. El rango a término (37-41 semanas) es el de menor riesgo.
      </p>
      <div style={{ height: '280px' }}>
        <Bar
          data={{
            labels: data.labels,
            datasets: [
              {
                data: data.valores,
                backgroundColor: GESTACIONAL_COLORS,
                borderColor: '#475569',
                borderWidth: 1,
              },
            ],
          }}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false } },
              y: {
                title: { display: true, text: 'Casos', font: { family: CHART_FONT_FAMILY } },
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)' },
              },
            },
          }}
        />
      </div>
      <ChartAiInsight insight={insight} />
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/DistribucionEdadGestacional.test.tsx`
Expected: PASS (2 tests)

- [ ] **Step 5: Eliminar el componente viejo**

Run: `git rm FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.tsx FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadRiesgo.test.tsx`

(`AnalysisHomeSection.tsx` todavía importa `DistribucionEdadRiesgo` en este punto — eso se corrige en la Task 7. No te preocupes por el build roto en esta task.)

- [ ] **Step 6: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadGestacional.tsx FRONTED/maternanalytics/src/components/dashboard/DistribucionEdadGestacional.test.tsx
git commit -m "feat: reemplazar componente DistribucionEdadRiesgo por DistribucionEdadGestacional"
```

---

### Task 6: Frontend — `TrendChartsRow.tsx` con 2 gráficos de Top 10 separados

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx`
- Modify: `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Reemplazar el contenido completo de `FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx` por:

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { TrendChartsRow } from './TrendChartsRow'

const sampleProps = {
  lineChartData: {
    labels: ['Ene', 'Feb', 'Mar'],
    series: [{ name: 'Mortalidad', color: '#c0392b', data: [1, 2, 3] }],
  },
  topCausasMortalidad: { labels: ['Preeclampsia Severa'], values: [5], colors: ['#c0392b'] },
  topCausasMorbilidad: { labels: ['Eclampsia'], values: [3], colors: ['#2ca02c'] },
  demorasChartData: { labels: ['Demora 1'], values: [3] },
  edadChartData: { labels: ['20-29'], mortalidadValues: [2], morbilidadValues: [4] },
  momentoChartData: { labels: ['Parto'], mortalidadValues: [1], morbilidadValues: [2] },
}

const emptyProps = {
  lineChartData: { labels: [], series: [] },
  topCausasMortalidad: { labels: [], values: [], colors: [] },
  topCausasMorbilidad: { labels: [], values: [], colors: [] },
  demorasChartData: { labels: [], values: [] },
  edadChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
  momentoChartData: { labels: [], mortalidadValues: [], morbilidadValues: [] },
}

describe('TrendChartsRow', () => {
  it('renderiza los gráficos sin lanzar excepciones cuando hay datos', () => {
    render(<TrendChartsRow {...sampleProps} />)
    expect(screen.getByText('Evolución Temporal de Casos')).toBeInTheDocument()
    expect(screen.getByText('Top 10 Causas de Mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Top 10 Causas de Morbilidad')).toBeInTheDocument()
    expect(screen.getByText('Demoras Críticas en la Atención')).toBeInTheDocument()
    expect(screen.getByText('Distribución por Edad Materna')).toBeInTheDocument()
    expect(screen.getByText('Momento de Ocurrencia / Muerte')).toBeInTheDocument()
  })

  it('muestra los mensajes de estado vacío cuando no hay datos', () => {
    render(<TrendChartsRow {...emptyProps} />)
    expect(screen.getByText('Sin datos de evolución temporal')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas de mortalidad')).toBeInTheDocument()
    expect(screen.getByText('Sin registros de causas de morbilidad')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de demoras (Aplica principalmente a Mortalidad)')).toBeInTheDocument()
    expect(screen.getByText('Sin datos de distribución por edad')).toBeInTheDocument()
    expect(screen.getByText('Sin datos del momento del evento')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: FAIL — el componente actual no acepta `topCausasMortalidad`/`topCausasMorbilidad` y sigue mostrando "Top 5 Causas Principales" (o "Top 5 Criterios Principales"), no "Top 10 Causas de Mortalidad/Morbilidad".

- [ ] **Step 3: Reemplazar el contenido completo de `TrendChartsRow.tsx`**

```tsx
import { useMemo } from 'react'
import { Line, Bar, Pie } from 'react-chartjs-2'
import { CHART_COLORS, CHART_FONT_FAMILY } from '../../constants/chartTheme'
import { ChartAiInsight } from './ChartAiInsight'
import {
  getTimelineAiInsight,
  getTopCausasAiInsight,
  getDemorasAiInsight,
  getEdadAiInsight,
  getMomentoAiInsight,
} from '../../utils/aiChartInsights'

export interface TopCausasChartData {
  labels: string[]
  values: number[]
  colors: string[]
}

export interface TrendChartsRowProps {
  lineChartData: { labels: string[]; series: { name: string; color: string; data: number[] }[] }
  topCausasMortalidad: TopCausasChartData
  topCausasMorbilidad: TopCausasChartData
  demorasChartData: { labels: string[]; values: number[] }
  edadChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
  momentoChartData: { labels: string[]; mortalidadValues: number[]; morbilidadValues: number[] }
}

const wrapLabel = (text: string, maxLen: number = 45): string | string[] => {
  if (text.length <= maxLen) return text
  const words = text.split(' ')
  const lines: string[] = []
  let currentLine = ''
  for (const word of words) {
    if ((currentLine + word).length > maxLen) {
      if (currentLine) lines.push(currentLine.trim())
      currentLine = word + ' '
    } else {
      currentLine += word + ' '
    }
  }
  if (currentLine) lines.push(currentLine.trim())
  if (lines.length > 2) return [lines[0], lines[1] + '...']
  return lines
}

const legendBottom = {
  legend: { position: 'bottom' as const, labels: { font: { family: CHART_FONT_FAMILY } } },
}

export function TrendChartsRow({
  lineChartData,
  topCausasMortalidad,
  topCausasMorbilidad,
  demorasChartData,
  edadChartData,
  momentoChartData,
}: TrendChartsRowProps) {
  const timelineInsight = useMemo(
    () => getTimelineAiInsight(lineChartData.labels, lineChartData.series),
    [lineChartData],
  )

  const topCausasMortalidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMortalidad.labels, topCausasMortalidad.values, false),
    [topCausasMortalidad],
  )

  const topCausasMorbilidadInsight = useMemo(
    () => getTopCausasAiInsight(topCausasMorbilidad.labels, topCausasMorbilidad.values, true),
    [topCausasMorbilidad],
  )

  const demorasInsight = useMemo(
    () => getDemorasAiInsight(demorasChartData.labels, demorasChartData.values),
    [demorasChartData],
  )

  const edadInsight = useMemo(
    () => getEdadAiInsight(edadChartData.labels, edadChartData.mortalidadValues, edadChartData.morbilidadValues),
    [edadChartData],
  )

  const momentoInsight = useMemo(
    () => getMomentoAiInsight(momentoChartData.labels, momentoChartData.mortalidadValues, momentoChartData.morbilidadValues),
    [momentoChartData],
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="charts-grid-row">
        <div className="chart-card-col-12">
          <h3 className="chart-card-title">Evolución Temporal de Casos</h3>
          <div style={{ height: '320px' }}>
            {lineChartData.series.length > 0 ? (
              <Line
                data={{
                  labels: lineChartData.labels,
                  datasets: lineChartData.series.map((s) => ({
                    label: s.name,
                    data: s.data,
                    borderColor: s.color,
                    backgroundColor: s.color,
                    tension: 0.4,
                    pointRadius: 4,
                  })),
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Meses' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: {
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de evolución temporal
              </div>
            )}
          </div>
          <ChartAiInsight insight={timelineInsight} />
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 10 Causas de Mortalidad</h3>
          <div style={{ height: '320px' }}>
            {topCausasMortalidad.values.length > 0 ? (
              <Bar
                data={{
                  labels: topCausasMortalidad.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: topCausasMortalidad.values,
                      backgroundColor: topCausasMortalidad.colors,
                      borderColor: '#475569',
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  indexAxis: 'y' as const,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas de mortalidad
              </div>
            )}
          </div>
          <ChartAiInsight insight={topCausasMortalidadInsight} />
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Top 10 Causas de Morbilidad</h3>
          <div style={{ height: '320px' }}>
            {topCausasMorbilidad.values.length > 0 ? (
              <Bar
                data={{
                  labels: topCausasMorbilidad.labels.map((l) => wrapLabel(l)),
                  datasets: [
                    {
                      data: topCausasMorbilidad.values,
                      backgroundColor: topCausasMorbilidad.colors,
                      borderColor: '#475569',
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  indexAxis: 'y' as const,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { grid: { display: false } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin registros de causas de morbilidad
              </div>
            )}
          </div>
          <ChartAiInsight insight={topCausasMorbilidadInsight} />
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Demoras Críticas en la Atención</h3>
          <div style={{ height: '320px' }}>
            {demorasChartData.values.length > 0 ? (
              <Bar
                data={{
                  labels: demorasChartData.labels.map((l) => wrapLabel(l, 25)),
                  datasets: [
                    {
                      data: demorasChartData.values,
                      backgroundColor: ['#e74c3c', '#e67e22', '#f1c40f', '#3498db'],
                      borderColor: '#475569',
                      borderWidth: 1,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { grid: { display: false } },
                    y: {
                      title: { display: true, text: 'Casos' },
                      beginAtZero: true,
                      grid: { color: 'rgba(0,0,0,0.05)' },
                    },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de demoras (Aplica principalmente a Mortalidad)
              </div>
            )}
          </div>
          <ChartAiInsight insight={demorasInsight} />
        </div>

        <div className="chart-card-col-6">
          <h3 className="chart-card-title">Distribución por Edad Materna</h3>
          <div style={{ height: '320px' }}>
            {edadChartData.labels.length > 0 ? (
              <Bar
                data={{
                  labels: edadChartData.labels,
                  datasets: [
                    { label: 'Mortalidad', data: edadChartData.mortalidadValues, backgroundColor: CHART_COLORS.mortalidad },
                    { label: 'Morbilidad', data: edadChartData.morbilidadValues, backgroundColor: CHART_COLORS.morbilidad },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: legendBottom,
                  scales: {
                    x: { title: { display: true, text: 'Rango de Edad' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y: { title: { display: true, text: 'Casos' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                  },
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos de distribución por edad
              </div>
            )}
          </div>
          <ChartAiInsight insight={edadInsight} />
        </div>
      </div>

      <div className="charts-grid-row">
        <div className="chart-card-col-12">
          <h3 className="chart-card-title">Momento de Ocurrencia / Muerte</h3>
          <div style={{ height: '320px', maxWidth: '420px', margin: '0 auto' }}>
            {momentoChartData.labels.length > 0 ? (
              <Pie
                data={{
                  labels: momentoChartData.labels,
                  datasets: [
                    {
                      data: momentoChartData.labels.map(
                        (_, i) => momentoChartData.mortalidadValues[i] + momentoChartData.morbilidadValues[i],
                      ),
                      backgroundColor: ['#34495e', '#9b59b6', '#3498db', '#e74c3c', '#1abc9c'],
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  cutout: '40%',
                  plugins: legendBottom,
                }}
              />
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#888' }}>
                Sin datos del momento del evento
              </div>
            )}
          </div>
          <ChartAiInsight insight={momentoInsight} />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `cd FRONTED/maternanalytics && npx vitest run src/components/dashboard/TrendChartsRow.test.tsx`
Expected: PASS (2 tests).

(`AnalysisHomeSection.tsx` todavía pasa `barChartData`/`segmento` a `TrendChartsRow` en este punto — eso se corrige en la Task 7. Es normal que `tsc --noEmit` siga fallando ahí.)

- [ ] **Step 5: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.tsx FRONTED/maternanalytics/src/components/dashboard/TrendChartsRow.test.tsx
git commit -m "feat: dividir el grafico combinado de causas en 2 top-10 separados por evento"
```

---

### Task 7: Frontend — wiring final en `AnalysisHomeSection.tsx`

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx`

- [ ] **Step 1: Actualizar el import del componente**

Buscar:

```tsx
import { DistribucionEdadRiesgo } from './DistribucionEdadRiesgo'
```

Reemplazar por:

```tsx
import { DistribucionEdadGestacional } from './DistribucionEdadGestacional'
```

- [ ] **Step 2: Actualizar la destructuración de `useDashboardCharts`**

Buscar:

```tsx
  const { lineChartData, barChartData, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData, edadRiesgoMortalidad, edadRiesgoMorbilidad } = useDashboardCharts({
```

Reemplazar por:

```tsx
  const { lineChartData, topCausasMortalidad, topCausasMorbilidad, activeClusterData, clusteringChartData, demorasChartData, edadChartData, momentoChartData, heatmapDemorasData, sankeyFlujoData, severidadFallasData, morbKpis, criteriosInclusionData, momentoOcurrenciaData, tiempoRemisionData, atencionKpis, institucionReferenciaData, obstetricoEdadData, edadGestacionalMortalidad, edadGestacionalMorbilidad } = useDashboardCharts({
```

- [ ] **Step 3: Actualizar `reportExportData.causasPrincipales` y su dependencia**

Buscar:

```tsx
      causasPrincipales: {
        causas: barChartData.labels,
        valores: barChartData.values,
      },
```

Reemplazar por:

```tsx
      causasPrincipales: {
        causas: [...topCausasMortalidad.labels, ...topCausasMorbilidad.labels],
        valores: [...topCausasMortalidad.values, ...topCausasMorbilidad.values],
      },
```

Y en el arreglo de dependencias del mismo `useMemo`, buscar:

```tsx
  }, [
    filterYear,
    filterMonth,
    segmento,
    metrics,
    lineChartData,
    barChartData,
    demorasChartData,
    edadChartData,
    severidadFallasData,
  ])
```

Reemplazar por:

```tsx
  }, [
    filterYear,
    filterMonth,
    segmento,
    metrics,
    lineChartData,
    topCausasMortalidad,
    topCausasMorbilidad,
    demorasChartData,
    edadChartData,
    severidadFallasData,
  ])
```

- [ ] **Step 4: Actualizar el uso de `TrendChartsRow`**

Buscar:

```tsx
              <TrendChartsRow
                lineChartData={lineChartData}
                barChartData={barChartData}
                demorasChartData={demorasChartData}
                edadChartData={edadChartData}
                momentoChartData={momentoChartData}
                segmento={segmento}
              />
```

Reemplazar por:

```tsx
              <TrendChartsRow
                lineChartData={lineChartData}
                topCausasMortalidad={topCausasMortalidad}
                topCausasMorbilidad={topCausasMorbilidad}
                demorasChartData={demorasChartData}
                edadChartData={edadChartData}
                momentoChartData={momentoChartData}
              />
```

- [ ] **Step 5: Reemplazar `DistribucionEdadRiesgo` por `DistribucionEdadGestacional` en ambas subpestañas**

Buscar (dentro de `{activeTab === 'morbilidad' && (`):

```tsx
                  <DistribucionEdadRiesgo data={edadRiesgoMorbilidad} evento="Morbilidad" />
```

Reemplazar por:

```tsx
                  <DistribucionEdadGestacional data={edadGestacionalMorbilidad} evento="Morbilidad" />
```

Buscar (dentro de `{activeTab === 'mortalidad' && (`):

```tsx
                  <DistribucionEdadRiesgo data={edadRiesgoMortalidad} evento="Mortalidad" />
```

Reemplazar por:

```tsx
                  <DistribucionEdadGestacional data={edadGestacionalMortalidad} evento="Mortalidad" />
```

- [ ] **Step 6: Verificar tipos y tests**

Run: `cd FRONTED/maternanalytics && npx tsc --noEmit && npm test`
Expected: sin errores de tipos (todos los archivos de las Tasks 4-7 ahora son consistentes entre sí); toda la suite pasa.

- [ ] **Step 7: Commit**

```bash
git add FRONTED/maternanalytics/src/components/dashboard/AnalysisHomeSection.tsx
git commit -m "feat: conectar edad gestacional y top 10 causas separadas en AnalysisHomeSection"
```

---

### Task 8: Verificación completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Suite completa de backend**

Run: `cd BACKEND && ./venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests pasan.

- [ ] **Step 2: Suite completa de frontend + build + lint**

Run: `cd FRONTED/maternanalytics && npm test && npm run build && npm run lint`
Expected: tests en verde; build sin errores (nota: el bundle crecerá por el JSON de CIE-10 de ~880KB, es esperado); lint sin errores nuevos respecto a los ya preexistentes en archivos no tocados por este plan.

- [ ] **Step 3: Verificación manual en el navegador**

Con backend y frontend corriendo y datos de mortalidad/morbilidad cargados:

1. En Generalidades: confirmar que aparecen 2 gráficos separados "Top 10 Causas de Mortalidad" y "Top 10 Causas de Morbilidad" (no el combinado "Top 5" de antes), con nombres reales de enfermedades (no códigos ni "Descripción no disponible" para códigos comunes).
2. Confirmar que "Demoras Críticas", "Distribución por Edad Materna" (sin cambios) y "Momento de Ocurrencia / Muerte" (ahora a ancho completo) siguen mostrando datos correctamente.
3. En Morbilidad (Ev. 549) → Factores Sociodemográficos: confirmar que se ve "Distribución por Edad Gestacional (Morbilidad)" con 4 barras (`<28`, `28-36`, `37-41`, `≥42 semanas`), NO la gráfica de edad materna de antes.
4. Repetir en Mortalidad (Ev. 550) → Factores Sociodemográficos.
5. Confirmar que "Variables Obstétricas por Edad" (Morbilidad → Clínico) y "Modelos de Clustering" siguen usando los 4 grupos de edad de siempre (`<20/20-29/30-39/≥40`), sin cambios — no deben verse afectados por este plan.
6. Exportar un reporte (botón "Exportar Reporte") y confirmar que la tabla de causas principales no está vacía ni rota.
7. Sin errores en la consola del navegador.

- [ ] **Step 4: Commit final si hubo ajustes**

Si la verificación manual no requirió cambios, no hay nada que commitear. Si se detectaron ajustes menores:

```bash
git add -A
git commit -m "fix: ajustes tras verificacion manual de graficas actualizadas con CIE-10 real"
```
