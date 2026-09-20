# Rediseño del ícono/logo de VidaMaterna — Spec de Diseño

**Fecha:** 2026-08-22
**Depende de:** ninguna
**Contexto:** Durante una revisión de frontend se detectó que el ícono actual (`src/components/icons/LogoIcon.tsx`) es una forma orgánica sin relación clara con lo que hace la plataforma (análisis epidemiológico de mortalidad/morbilidad materna). Esta spec define un ícono nuevo, explorado y aprobado con el usuario vía el companion visual de brainstorming, que comunique institucionalidad clínica + análisis de datos.

---

## Objetivo

Reemplazar la geometría interna de `LogoIcon.tsx` (y el `public/favicon.svg` derivado) por un ícono nuevo — sin cambiar la API del componente, sin restructurar los componentes que ya lo consumen (`Login.tsx`, `Register.tsx`, `Sidebar.tsx`).

## Fuera de alcance

- No se cambia la tipografía del wordmark "VidaMaterna" (sigue en `DM Serif Display` + acento en azul claro sobre el "Materna").
- No se crea un componente "Lockup" nuevo — los layouts horizontal (sidebar) y apilado (login/registro) ya existen en el JSX/CSS actual; solo cambia el ícono que envuelven.
- No se toca `src/components/LogoIcon.tsx` (el shim de re-export) — sigue re-exportando `./icons/LogoIcon`.

---

## Concepto elegido

Explorado con el companion visual (4 conceptos iniciales → 4 variaciones → 2 detalles de color/lockup, todos aprobados por el usuario en la conversación):

**"Sello + barras + línea de tendencia"**: un círculo (sello institucional, evoca una entidad oficial de salud pública — encaja con el contexto SIVIGILA) con 3 barras ascendentes de fondo (analítica/tendencia de casos) y una línea de tendencia en rosa con un punto de dato en el pico (el hallazgo/caso individual que la plataforma resalta).

Reemplaza al ícono anterior (forma orgánica tipo escudo con curvas) que no comunicaba con claridad ni "institucional" ni "datos".

## Estado actual (verificado en código)

- `src/components/icons/LogoIcon.tsx`: SVG de 64x64 con colores hardcodeados (`rgba(255,255,255,...)`, `#F4C0D1`) — diseñado únicamente para fondos oscuros. Nunca se usa sobre fondo claro en la app hoy.
- `src/components/LogoIcon.tsx`: shim, `export { LogoIcon as default, LogoIcon } from './icons/LogoIcon'`.
- Usos actuales: `Login.tsx` (`<LogoIcon className="logo-icon" aria-hidden="true" />` sobre gradiente azul oscuro), `Register.tsx` (igual, tras el fix de esta sesión), `Sidebar.tsx` (`<LogoIcon width="100%" height="100%" />` sobre `#151515`, dentro de `.logo-icon-okd`).
- `public/favicon.svg`: archivo estático independiente, enlazado en `index.html` vía `<link rel="icon">`.
- `src/index.css`: define `--blue-900` a `--blue-100` en `:root`. No existe ningún tono de rosa como variable — el `#F4C0D1` vive hardcodeado dentro del propio `LogoIcon.tsx` y en `Login.css`/`Register` inline.

---

## Especificación visual

**Geometría (viewBox 0 0 64 64):**

```
Círculo:  cx=32 cy=32 r=26, stroke-width=2.5, fill=none
Barra 1:  x=20 y=34 width=6 height=12 rx=1.5   (opacity 0.55)
Barra 2:  x=29 y=28 width=6 height=18 rx=1.5   (opacity 0.55)
Barra 3:  x=38 y=20 width=6 height=26 rx=1.5   (opacity 0.55)
Línea:    M23 34 L32 28 L41 20  (stroke-width=2.5, round cap/join)
Punto:    cx=41 cy=20 r=3
```

**Color — dos tratamientos** (el ícono anterior solo tenía uno):

| Elemento | Contexto claro (favicon) | Contexto oscuro (sidebar, panel login) |
|---|---|---|
| Círculo + barras | `--blue-700` (#2a5298) | `--blue-400` (#7aaee8) |
| Línea + punto | `--pink-500` (nuevo, #E8829F) | `--pink-500` (igual en ambos) |

**Nueva variable de color**: `--pink-500: #E8829F;` se agrega a `:root` en `src/index.css`, junto a los `--blue-*` existentes. Reemplaza el `#F4C0D1` hardcodeado del ícono anterior (que era demasiado pálido para leerse a tamaño de favicon — decisión tomada con el usuario tras comparar ambos tonos en el companion visual).

**Mecanismo de color claro/oscuro**: el círculo y las barras usan `stroke="currentColor"` / `fill="currentColor"` en el SVG, y cada sitio de uso controla el tono vía la propiedad CSS `color` en la clase que ya envuelve al ícono (`.logo-icon` en `LoginDecorations.css`, `.logo-icon-okd` en `Sidebar.css`) — sin necesidad de una prop `variant` en el componente. La línea/punto rosa usa `var(--pink-500)` directamente (constante en ambos contextos, ya tiene suficiente contraste sobre azul oscuro y sobre `#151515`).

**Lockups** (sin componente nuevo — ya existen en el JSX actual):
- Horizontal (`Sidebar.tsx`, `.sidebar-header-okd`): ícono + wordmark en fila, ya es `display:flex` con `gap`.
- Apilado (`Login.tsx`/`Register.tsx`, `.left-content`): ícono arriba, wordmark abajo, ya es `flex-direction:column`.

---

## Cambios de archivo

1. **`src/index.css`** — agregar `--pink-500: #E8829F;` al bloque `:root`.
2. **`src/components/icons/LogoIcon.tsx`** — reemplazar el contenido de `<svg>` por la geometría de arriba (círculo + 3 barras `currentColor`, línea + punto `var(--pink-500)`). Mantiene la firma `SVGProps<SVGSVGElement>` actual.
3. **`src/components/LoginDecorations.css`** — en la regla `.logo-icon`, agregar `color: var(--blue-400);` (fondo oscuro del panel izquierdo de login/registro).
4. **`src/components/dashboard/Sidebar.css`** — en la regla `.logo-icon-okd`, agregar `color: var(--blue-400);` (fondo `#151515` del sidebar).
5. **`public/favicon.svg`** — reescribir con la misma geometría, colores hardcodeados en claro (`#2a5298` / `#E8829F`) porque es un archivo estático sin acceso al CSS de la app.

No se toca `Login.tsx`, `Register.tsx`, `Sidebar.tsx`, `src/components/LogoIcon.tsx` (el shim) ni `index.html`.

---

## Verificación

- `pnpm exec tsc -b`, `pnpm run lint`, `pnpm run test` deben seguir en verde (ningún cambio de tipos/props).
- Verificación visual manual: `pnpm run dev`, revisar el ícono en Login, Register y el Sidebar del dashboard (fondo oscuro en los tres casos), y el favicon en la pestaña del navegador (fondo claro).
