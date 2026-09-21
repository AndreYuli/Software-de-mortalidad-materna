# Rediseño de Login y Register (Tailwind + lucide-react)

Fecha: 2026-09-20
Alcance: primera parte del rediseño total del frontend. Solo `Login` y `Register`.
Las demás partes (layout del dashboard, análisis y gráficas, carga e historial) tendrán su propio diseño.

## Contexto

- El frontend (`frontend/maternanalytics`, Vite + React + TypeScript) no tiene CSS ni estilos inline desde el commit `6ba5c070`.
- Tailwind v4 ya está configurado (`@tailwindcss/vite`, `src/index.css` con `@theme`).
- `lucide-react` ya está instalado.
- Tokens de marca disponibles como clases: `brand-deep` (#290764), `brand-violet` (#4b0453), `brand-magenta` (#89005e).

## Decisiones

- Distribución: **tarjeta centrada** (no dos paneles).
- Decoración de fondo: **ninguna**. Se eliminan los ~14 `div` decorativos (burbujas, nodos, líneas de pulso).
- Logo: **ícono de lucide** (`Heart`) en un círculo `brand-magenta`, sobre el título.
- Se añade botón para **ver/ocultar contraseña**.

## Componentes

### `AuthCard` (nuevo, `src/components/auth/AuthCard.tsx`)

Esqueleto común de ambas pantallas. Props: `title`, `subtitle`, `children`, `footer`.

- Fondo de pantalla completa `bg-slate-50`, contenido centrado.
- Tarjeta blanca, `max-w-md`, esquinas redondeadas, sombra suave.
- Cabecera: círculo `bg-brand-magenta` con `Heart` blanco, título "Vida**Materna**" ("Vida" en `brand-deep`, "Materna" en `brand-magenta`).
- Debajo: `title` en `text-brand-deep` y `subtitle` en gris.

### `AuthField` (nuevo, `src/components/auth/AuthField.tsx`)

Campo de formulario reutilizable. Props: `id`, `label`, `icon` (componente lucide), `type`, `placeholder`, `error`, más el `register(...)` de react-hook-form.

- Ícono a la izquierda dentro del input.
- Si `type="password"`, botón `Eye` / `EyeOff` a la derecha que alterna entre `password` y `text`. El botón lleva `aria-label` ("Mostrar contraseña" / "Ocultar contraseña") y `type="button"`.
- Con `error`: borde rojo y mensaje bajo el campo.

### `Login` y `Register` (modificados)

Solo cambia el JSX y las clases. Usan `AuthCard` y `AuthField`.

Iconos por campo: correo `Mail`, contraseña `Lock`, nombre completo `User`, confirmar contraseña `Lock`.

Login conserva: casilla "Recordarme", enlace "¿Olvidaste tu contraseña?", enlace "Crear cuenta".
Register conserva su enlace de vuelta al login.

## Estados

| Estado | Presentación |
|---|---|
| Error de validación de un campo | borde rojo + texto rojo bajo el campo |
| Error del servidor / red | aviso rojo con `AlertCircle` |
| Mensaje informativo (recuperar contraseña) | aviso azul con `Info` (sustituye al emoji) |
| Éxito de registro | aviso verde con `CheckCircle` |
| Enviando | botón deshabilitado con `Loader2` girando y el texto actual ("Verificando...") |

Botón principal: `bg-brand-magenta`, ancho completo. Enlaces secundarios: `text-brand-violet`.

## Sin cambios

La lógica no se toca: `react-hook-form` con los esquemas zod (`loginSchema`, `registerSchema`), llamadas a la API, mensajes de error, escritura en `localStorage`, navegación y las props opcionales (`onLogin`, `onRegister`, `onRegistered`, `onBack`).

## Se elimina

- Los `div` decorativos del panel izquierdo.
- Los SVG en línea de los campos.
- El uso de `LogoIcon` en estas dos pantallas (el componente sigue existiendo para el resto de la app).

## Accesibilidad

- Cada input mantiene su `<label htmlFor>`.
- Íconos decorativos con `aria-hidden="true"`.
- Botón de ver contraseña con `aria-label`.
- Los mensajes de error del servidor con `role="alert"`.

## Pruebas

- Revisar los tests existentes de Login y Register; si dependen de `className` o de textos que cambian, ajustarlos.
- Añadir un test para el botón de ver contraseña (alterna `type`).
- Verificar `tsc -b`, `vite build` y `vitest run`.
