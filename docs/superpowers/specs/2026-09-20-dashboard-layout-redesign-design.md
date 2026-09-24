# Rediseño del layout del dashboard (Tailwind + lucide-react)

Fecha: 2026-09-20
Alcance: segunda parte del rediseño total del frontend. Solo el marco del dashboard: `DashboardOKD`, `Sidebar`, `NavItem` y `Avatar`.
Pendientes (cada una con su propio diseño): análisis y gráficas, carga de archivos, historial.
Parte anterior: `2026-09-20-auth-redesign-design.md` (Login y Register, ya implementada).

## Contexto

- Tailwind v4 y `lucide-react` ya están configurados.
- Tokens de marca como clases: `brand-deep` (#290764), `brand-violet` (#4b0453), `brand-magenta` (#89005e).
- Login y Register usan como logo un `Heart` de lucide en un círculo `brand-magenta`; el layout debe usar el mismo.
- Los componentes del layout están en `frontend/maternanalytics/src/components/` (`DashboardOKD.tsx`) y `src/components/dashboard/` (`Sidebar.tsx`, `NavItem.tsx`, `Avatar.tsx`).
- No existen tests del layout.

## Decisiones

- Barra lateral **clara** (fondo blanco, borde a la derecha).
- Sin componentes nuevos: se reescribe solo el JSX y las clases de los cuatro existentes. Las props y la lógica no cambian.
- Íconos de lucide en todo el layout.

## Componentes

### `DashboardOKD`

- Contenedor: `flex min-h-screen bg-slate-50`.
- Zona de contenido: `main` con `min-w-0 flex-1`; dentro, un contenedor `mx-auto max-w-7xl p-4 lg:p-8` que aloja el `Outlet`.
- Barra superior móvil (visible solo bajo el punto `lg`): fija arriba, fondo blanco, borde inferior, con el botón de menú (`Menu`, `aria-label="Abrir menú"`) y el nombre de la marca.
- Overlay del cajón (solo móvil, solo cuando está abierto): `fixed inset-0 bg-slate-900/40`; al pulsarlo se cierra el menú.

### `Sidebar`

- Contenedor `aside`: fondo blanco, `border-r border-slate-200`, ancho `w-64`, columna a altura completa.
  - Desde `lg`: fija en el flujo, siempre visible.
  - Bajo `lg`: cajón `fixed inset-y-0 left-0` que entra y sale con `translate-x` y transición; abierto cuando `isMobileOpen`.
- Cabecera: círculo `bg-brand-magenta` con `Heart` blanco y texto "Vida**Materna**" ("Vida" en `brand-deep`, "Materna" en `brand-magenta`). Botón `X` (`aria-label="Cerrar menú"`) visible solo bajo `lg`.
- Navegación con tres grupos, igual que hoy:
  - "Dashboard Analítico" (`LayoutDashboard`)
  - título "Carga de Datos": "Mortalidad Materna" y "Morbilidad Extrema" (`Upload` en ambos)
  - título "Administración": "Historial de Cargas" (`History`)
- Títulos de grupo: mayúsculas pequeñas, `text-slate-400`.
- Pie: separador superior; `Avatar`, nombre y correo (truncados, con `title`; si falta el correo se muestra "VidaMaterna Analytics"), y botón de cerrar sesión (`LogOut`, `aria-label="Cerrar sesión"`).

### `NavItem`

- Botón de ancho completo con ícono, etiqueta e indicador opcional.
- Inactivo: `text-slate-600 hover:bg-slate-100`.
- Activo: `bg-brand-magenta/10 text-brand-magenta`, con `aria-current="page"`.
- Indicador de archivo cargado: `CheckCircle` verde, `aria-label="Archivo cargado correctamente"`.
- Indicador de error: `AlertCircle` rojo, `aria-label="Error en el archivo cargado"`.
- Con error el indicador tiene prioridad sobre el de éxito (como hoy: `isSuccess` exige `!hasError`).
- El ícono llega como `ReactNode` por props, sin cambios en la interfaz.

### `Avatar`

- Círculo `bg-brand-deep` con la inicial en blanco, `aria-hidden="true"`. Sigue aceptando `className`.

## Sin cambios

La lógica de `DashboardOKD`: vista activa derivada de la URL, `handleNavigate` (que además cierra el menú móvil), `handleLogout` (`clearSession` y navegación a `/login`), estado `isMobileNavOpen`, `Outlet` con su contexto `{ data, onNavigate }` y las props públicas de `Sidebar` y `DashboardOKD`.

## Se elimina

- El SVG en línea del reloj en `Sidebar`.
- En estos cuatro archivos, el uso de `LogoIcon`, `MenuIcon`, `CloseIcon`, `DashboardIcon`, `UploadIcon` y `LogoutIcon` de `components/icons`. Los archivos de `components/icons` **no se borran** en esta parte: otras vistas todavía los usan. Se limpiarán al terminar todo el rediseño.

## Accesibilidad

- Todos los íconos decorativos con `aria-hidden="true"`.
- Botones solo-ícono con `aria-label`.
- El `aside` conserva su rol de navegación mediante `nav` con `aria-label="Navegación principal"`.
- Ítem activo con `aria-current="page"`.

## Pruebas

- Nuevo `Sidebar.test.tsx`: renderiza los tres grupos; marca el ítem activo con `aria-current`; llama a `onNavigate` con la vista correcta; muestra los indicadores de éxito y de error (y el de error gana al de éxito); llama a `onLogout`; muestra el correo por defecto si falta.
- Nuevo `DashboardOKD.test.tsx`: el botón "Abrir menú" abre el cajón (el overlay aparece), pulsar el overlay lo cierra y navegar cierra el menú. Debe mockear `useDashboardData`.
- `App.test.tsx` sigue pasando.
- Verificar `tsc -b`, `vite build`, y `vitest run` (nota: con la suite completa hay timeouts esporádicos a 5 s en esta máquina; usar `--testTimeout=30000` si ocurre).
