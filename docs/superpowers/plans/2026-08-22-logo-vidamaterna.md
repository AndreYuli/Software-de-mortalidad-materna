# Rediseño del ícono/logo de VidaMaterna Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el ícono/favicon actual de VidaMaterna por el nuevo diseño "sello + barras + línea de tendencia" aprobado en `docs/superpowers/specs/2026-08-22-logo-vidamaterna-design.md`, sin cambiar la API de ningún componente.

**Architecture:** 5 ediciones independientes y acumulativas (variable CSS → geometría del ícono → color en cada contexto de uso → favicon estático) más una verificación final. No hay lógica nueva que testear con TDD clásico (es geometría SVG y color CSS); cada tarea usa `grep` para confirmar que el contenido exacto quedó escrito, y la tarea final corre la suite completa (`tsc`/`lint`/`test`/`build`) más una verificación visual manual.

**Tech Stack:** React 18 + TypeScript (Vite), CSS con custom properties (`:root` en `index.css`), SVG inline.

---

### Task 1: Nueva variable de color `--pink-500`

**Files:**
- Modify: `FRONTED/maternanalytics/src/index.css`

- [ ] **Step 1: Agregar la variable al bloque `:root`**

Contenido actual del bloque (líneas 7-17):

```css
:root {
  --blue-900: #1a2e4a;
  --blue-800: #1e3a5f;
  --blue-700: #2a5298;
  --blue-600: #3a6bc4;
  --blue-500: #4d7fd4;
  --blue-400: #7aaee8;
  --blue-300: #a8cdf0;
  --blue-200: #dceeff;
  --blue-100: #f0f7ff;
}
```

Reemplazar por:

```css
:root {
  --blue-900: #1a2e4a;
  --blue-800: #1e3a5f;
  --blue-700: #2a5298;
  --blue-600: #3a6bc4;
  --blue-500: #4d7fd4;
  --blue-400: #7aaee8;
  --blue-300: #a8cdf0;
  --blue-200: #dceeff;
  --blue-100: #f0f7ff;

  --pink-500: #e8829f;
}
```

- [ ] **Step 2: Verificar que quedó escrita**

Run (desde `FRONTED/maternanalytics`): `grep -n "pink-500" src/index.css`
Expected: `--pink-500: #e8829f;` aparece una vez.

- [ ] **Step 3: Commit**

```bash
git add src/index.css
git commit -m "feat: agregar variable --pink-500 para el acento del nuevo logo"
```

---

### Task 2: Reemplazar la geometría de `LogoIcon.tsx`

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/icons/LogoIcon.tsx`

- [ ] **Step 1: Reemplazar el contenido completo del archivo**

Archivo completo actual:

```tsx
import type { SVGProps } from 'react'

export function LogoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <path
        d="M32 4 C52 4 58 20 58 34 C58 52 46 60 32 60 C18 60 6 52 6 34 C6 20 12 4 32 4Z"
        fill="rgba(255,255,255,0.06)"
        stroke="rgba(255,255,255,0.35)"
        strokeWidth="1.2"
      />
      <path
        d="M26 16 C18 24 16 34 22 44 C26 48 30 52 32 54"
        fill="none"
        stroke="#F4C0D1"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M38 14 C46 22 48 34 42 44 C38 48 34 52 32 54"
        fill="none"
        stroke="rgba(255,255,255,0.85)"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="32" cy="36" r="5" fill="none" stroke="#F4C0D1" strokeWidth="1.2" />
      <circle cx="32" cy="36" r="1.8" fill="#F4C0D1" />
      <circle cx="20" cy="26" r="1.5" fill="rgba(255,255,255,0.35)" />
      <circle cx="17" cy="36" r="1.5" fill="rgba(255,255,255,0.35)" />
      <circle cx="20" cy="44" r="1.5" fill="rgba(255,255,255,0.35)" />
      <circle cx="44" cy="24" r="1.5" fill="rgba(255,255,255,0.25)" />
      <circle cx="47" cy="34" r="1.5" fill="rgba(255,255,255,0.25)" />
      <circle cx="44" cy="44" r="1.5" fill="rgba(255,255,255,0.25)" />
    </svg>
  )
}

export default LogoIcon
```

Reemplazar por:

```tsx
import type { SVGProps } from 'react'

export function LogoIcon({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      aria-hidden="true"
      {...props}
    >
      <circle cx="32" cy="32" r="26" fill="none" stroke="currentColor" strokeWidth="2.5" />
      <rect x="20" y="34" width="6" height="12" rx="1.5" fill="currentColor" opacity="0.55" />
      <rect x="29" y="28" width="6" height="18" rx="1.5" fill="currentColor" opacity="0.55" />
      <rect x="38" y="20" width="6" height="26" rx="1.5" fill="currentColor" opacity="0.55" />
      <path
        d="M23 34 L32 28 L41 20"
        fill="none"
        stroke="var(--pink-500)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="41" cy="20" r="3" fill="var(--pink-500)" />
    </svg>
  )
}

export default LogoIcon
```

Nota: la firma del componente (`SVGProps<SVGSVGElement>`, `className`, `aria-hidden`, spread de `props`) no cambia — solo el contenido interno del `<svg>`. Esto es intencional: ningún componente que lo consume (`Login.tsx`, `Register.tsx`, `Sidebar.tsx`, el shim `src/components/LogoIcon.tsx`) necesita cambios.

- [ ] **Step 2: Verificar que compila sin errores de tipos**

Run (desde `FRONTED/maternanalytics`): `pnpm exec tsc -b`
Expected: sin salida (build limpio).

- [ ] **Step 3: Verificar que la geometría vieja desapareció y la nueva quedó**

Run: `grep -c "F4C0D1" src/components/icons/LogoIcon.tsx`
Expected: `0`

Run: `grep -c "currentColor" src/components/icons/LogoIcon.tsx`
Expected: `4`

- [ ] **Step 4: Commit**

```bash
git add src/components/icons/LogoIcon.tsx
git commit -m "feat: reemplazar geometría de LogoIcon por el nuevo diseño sello+barras+tendencia"
```

---

### Task 3: Color del ícono en el panel de login/registro

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/LoginDecorations.css:141-145`

- [ ] **Step 1: Agregar `color` a la regla `.logo-icon`**

Bloque actual:

```css
.logo-icon {
  margin-bottom: 2rem;        /* ~32px */
  filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.15));
  animation: fadeUp 1s ease-out 0.2s both;
}
```

Reemplazar por:

```css
.logo-icon {
  color: var(--blue-300);
  margin-bottom: 2rem;        /* ~32px */
  filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.15));
  animation: fadeUp 1s ease-out 0.2s both;
}
```

- [ ] **Step 2: Verificar**

Run: `grep -A1 "^\.logo-icon {" src/components/LoginDecorations.css`
Expected: la primera línea dentro de la regla es `color: var(--blue-300);`

- [ ] **Step 3: Commit**

```bash
git add src/components/LoginDecorations.css
git commit -m "feat: aplicar --blue-300 al ícono del panel de login/registro"
```

---

### Task 4: Color del ícono en el sidebar del dashboard

**Files:**
- Modify: `FRONTED/maternanalytics/src/components/dashboard/Sidebar.css:31-35`

- [ ] **Step 1: Agregar `color` a la regla `.logo-icon-okd`**

Bloque actual:

```css
.logo-icon-okd {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
}
```

Reemplazar por:

```css
.logo-icon-okd {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  color: var(--blue-300);
}
```

- [ ] **Step 2: Verificar**

Run: `grep -A4 "^\.logo-icon-okd {" src/components/dashboard/Sidebar.css`
Expected: incluye la línea `color: var(--blue-300);`

- [ ] **Step 3: Commit**

```bash
git add src/components/dashboard/Sidebar.css
git commit -m "feat: aplicar --blue-300 al ícono del sidebar del dashboard"
```

---

### Task 5: Reescribir el favicon

**Files:**
- Modify: `FRONTED/maternanalytics/public/favicon.svg`

- [ ] **Step 1: Reemplazar el contenido completo del archivo**

El archivo actual es un blob morado/azul genérico sin relación con VidaMaterna (verificado leyendo el archivo — no es una versión antigua del logo, es contenido no relacionado). Reemplazar el archivo completo por:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="26" fill="none" stroke="#2a5298" stroke-width="2.5"/>
  <rect x="20" y="34" width="6" height="12" rx="1.5" fill="#2a5298" opacity="0.55"/>
  <rect x="29" y="28" width="6" height="18" rx="1.5" fill="#2a5298" opacity="0.55"/>
  <rect x="38" y="20" width="6" height="26" rx="1.5" fill="#2a5298" opacity="0.55"/>
  <path d="M23 34 L32 28 L41 20" fill="none" stroke="#e8829f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="41" cy="20" r="3" fill="#e8829f"/>
</svg>
```

Los colores van hardcodeados en hex (no `currentColor`/`var()`) porque es un archivo `.svg` estático cargado por el navegador vía `<link rel="icon">` en `index.html`, sin acceso al CSS de la aplicación React.

- [ ] **Step 2: Verificar**

Run: `grep -c "863bff\|7e14ff" public/favicon.svg`
Expected: `0` (el blob morado viejo ya no está)

Run: `grep -c "#2a5298" public/favicon.svg`
Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add public/favicon.svg
git commit -m "feat: reemplazar favicon.svg por el nuevo ícono de VidaMaterna"
```

---

### Task 6: Verificación completa y check visual

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Suite completa**

Run (desde `FRONTED/maternanalytics`):

```bash
pnpm exec tsc -b
pnpm run lint
pnpm run test
pnpm run build
```

Expected: los 4 comandos terminan sin errores (mismo resultado que antes de esta serie de cambios — ningún tipo, prop ni lógica cambió).

- [ ] **Step 2: Verificación visual manual**

Run: `pnpm run dev` y abrir la URL que imprime (por defecto `http://localhost:5173`).

Revisar:
- Pantalla de login (`/`): el ícono nuevo (círculo + barras + línea rosa) debe verse en azul claro sobre el panel izquierdo oscuro, junto al wordmark "VidaMaterna".
- Botón "Crear cuenta" → pantalla de registro: mismo ícono, mismo tratamiento.
- Iniciar sesión → dashboard: el ícono debe verse en azul claro en la esquina superior del sidebar oscuro (`#151515`), junto a "VidaMaterna".
- Pestaña del navegador: el favicon debe mostrar el ícono en azul oscuro sobre fondo transparente (ya no el blob morado).

- [ ] **Step 3: Commit final (si hubo algún ajuste visual)**

Si el check visual no requirió cambios, no hay nada que commitear en este paso — los 5 commits de las tareas anteriores ya dejan el trabajo completo.
