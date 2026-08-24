# Migración del frontend a TypeScript — Spec de Diseño

**Fecha:** 2026-08-20
**Depende de:** ninguna (spec previa a `2026-08-20-microservicio-ia-generativa-design.md`)
**Contexto:** Fase 1 del plan de tesis (`GAPS_ANALISIS.md`) exigía React + TypeScript + Vite; hoy el frontend es 100% JavaScript. Esta spec cubre solo la migración de infraestructura y tipado — no agrega funcionalidad nueva.

---

## Objetivo

Migrar `FRONTED/maternanalytics` de JavaScript a TypeScript sin cambiar comportamiento visible, y dejar en pie un runner de tests (`vitest`) que hoy no existe, para poder verificar que la migración no rompió nada y para que la spec de IA generativa (que se construye encima) tenga tests desde el día uno.

## Fuera de alcance

- No se cambia Plotly por ECharts (decisión ya tomada: se documenta como "elección pragmática" en `docs/decisiones-tecnicas.md`, fuera de esta spec).
- No se agrega D3.js ni Cytoscape.js (Fase 2 del `GAPS_ANALISIS.md`, spec separada).
- No se toca lógica de negocio ni estilos.

---

## Estado actual (verificado en código)

- `package.json`: sin `typescript`, sin `tsconfig.json`. `@types/react`/`@types/react-dom` están en `devDependencies` pero sin uso real (vestigio del template de Vite).
- Todo el código fuente en `src/` es `.jsx`/`.js`.
- Sin ningún test ni test runner configurado.
- Componentes principales: `App.jsx`, `Dashboard.jsx`, `DashboardOKD.jsx` (grande, ~1150 líneas, incluye `AnalysisHomeSection` con la tarjeta IA hardcodeada), `AnalisisView.jsx` (~1293 líneas), `api.js` (fetch wrapper).

---

## Estructura final

```
FRONTED/maternanalytics/
├── tsconfig.json            ← NUEVO — configuración TS para src/
├── tsconfig.node.json       ← NUEVO — configuración TS para vite.config
├── vite-env.d.ts            ← NUEVO — tipos de Vite (import.meta.env, etc.)
├── vitest.config.ts         ← NUEVO — config de vitest (jsdom, setup)
├── src/
│   ├── setupTests.ts        ← NUEVO — jest-dom matchers para vitest
│   ├── types.ts             ← NUEVO — interfaces compartidas de dominio
│   ├── api.ts                ← migrado desde api.js, tipado
│   ├── App.tsx                ← migrado
│   ├── main.tsx                ← migrado
│   └── components/
│       ├── Dashboard.tsx
│       ├── DashboardOKD.tsx
│       ├── AnalisisView.tsx
│       └── *.test.tsx        ← NUEVOS — smoke tests por componente
└── package.json               ← + typescript, vitest, @testing-library/*, jsdom
```

---

## Tipado de dominio (`types.ts`)

Interfaces derivadas de lo que hoy devuelve `BACKEND/services/_analisis_calculo.py::calcular_completo` (verificado leyendo el código, no inventado):

```ts
export interface AnalisisMeta {
  id: number;
  nombre_archivo: string;
  fecha_carga: string;
  limpieza_datos: Record<string, unknown>;
  anos_disponibles: number[];
  filtros_activos: { year: string | null; month: string | null };
  distribucion_mensual: Record<string, unknown>;
}

export interface IndicadoresMortalidad extends AnalisisMeta {
  tipo: 'mortalidad';
  estadisticas_basicas: Record<string, unknown>;
  momento_muerte: Record<string, unknown>;
  demoras: Record<string, { nombre: string; casos_con_demora: number; porcentaje: number }>;
  causas_cie10: { top_causas: { codigo: string; casos: number }[]; total_causas_unicas: number };
  obstetrico_edad: Record<string, unknown>;
}

export interface IndicadoresMorbilidad extends AnalisisMeta {
  tipo: 'morbilidad';
  estadisticas_basicas: Record<string, unknown>;
  criterios_inclusion: Record<string, { nombre: string; casos: number }>;
  momento_ocurrencia: Record<string, unknown>;
  institucion_referencia: Record<string, unknown>;
  tiempo_remision: Record<string, unknown>;
  obstetrico_edad: Record<string, unknown>;
}

export type AnalisisCompleto = IndicadoresMortalidad | IndicadoresMorbilidad;
```

Los campos marcados `Record<string, unknown>` se tipan con precisión solo si un componente ya los desestructura hoy (evitar tipar de más sin uso real — YAGNI). Si al migrar un componente se usa un campo específico, se agrega su tipo puntual en ese momento.

---

## Estrategia de migración

1. Instalar dependencias (`typescript`, `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `@vitejs/plugin-react` ya está).
2. Agregar `tsconfig.json` (`strict: true`, `jsx: react-jsx`, `allowJs: false` una vez terminada la migración).
3. Migrar archivo por archivo, de hoja a raíz (los que no importan nada propio primero): `api.js`→`api.ts`, luego componentes chicos, luego `Dashboard.jsx`, luego `DashboardOKD.jsx` y `AnalisisView.jsx` al final (son los más grandes/complejos).
4. Por cada componente migrado: renombrar, tipar props (`interface XProps`), tipar `useState`, correr `tsc --noEmit` y arreglar errores, agregar un test de humo (`renderiza sin crashear con props mínimas`).
5. Cuando no queden `.jsx`/`.js` en `src/`, poner `allowJs: false` en `tsconfig.json` para que el compilador exija TS en todo.

---

## Testing

- **Runner:** `vitest` (integra nativo con Vite, no requiere config paralela como Jest).
- **Librería:** `@testing-library/react` + `@testing-library/jest-dom`.
- **Cobertura mínima por componente migrado:** un test que lo renderiza con props/mocks mínimos y verifica que no lanza y que un elemento clave existe (p. ej. un `heading` o texto esperado). No se busca cobertura exhaustiva de lógica visual en esta spec — eso lo cubre la spec de IA generativa para los componentes nuevos que sí tienen lógica de estados (loading/error/éxito).
- **`api.ts`:** tests unitarios mockeando `global.fetch`, verificando URL y método por cada función exportada.
- **Comando:** `pnpm test` (nuevo script) corre `vitest run`.

## Criterio de aceptación

- `pnpm run build` compila sin errores de TypeScript.
- `pnpm test` pasa en verde.
- La app corre igual que antes (`pnpm dev`), sin cambios visuales ni de comportamiento.
- Cero archivos `.jsx`/`.js` restantes en `src/` (excepto config si aplica).
