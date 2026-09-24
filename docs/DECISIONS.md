# Decisiones del proyecto

Este documento registra decisiones importantes para evitar que el equipo o los agentes de IA vuelvan a cuestionar o modificar decisiones previamente aprobadas.

Cada decisión debe mantenerse breve, concreta y trazable. Si una decisión cambia, no se debe borrar sin más: agregar una nueva decisión que la reemplace o actualizar su estado explicando el motivo.

## Estados posibles

- **PROPUESTA:** decisión sugerida, pendiente de validación.
- **APROBADA:** decisión aceptada y vigente.
- **REEMPLAZADA:** decisión sustituida por una decisión posterior.
- **DESCARTADA:** decisión que ya no se seguirá.

---

## DEC-001

### Fecha

2026-09-19

### Decisión

Las visualizaciones relacionadas deben aprovechar el espacio horizontal disponible cuando sea adecuado.

### Motivo

Facilitar la comparación entre visualizaciones y reducir desplazamiento vertical.

### Estado

APROBADA

---

## DEC-002

### Fecha

2026-09-19

### Decisión

Las gráficas dinámicas deben actualizar sus etiquetas, ejes, títulos y textos asociados cuando cambie la variable seleccionada.

### Motivo

Evitar etiquetas genéricas que no permitan identificar correctamente la información representada.

### Estado

APROBADA

---

## DEC-003

### Fecha

2026-09-20

### Decisión

Renombrar las carpetas `BACKEND`, `IA-SERVICE` y `FRONTED` a `backend`, `ia-service` y `frontend`, y separar el material no ejecutable en `data/` (referencia, pruebas sintéticas y `local` sin versionar), `notes/` (notas; `notes/local` sin versionar) y `scripts/` (arranque y pruebas e2e). Los planes y specs anteriores pasan a `docs/historico/`.

### Motivo

Nombres consistentes (`FRONTED` era un typo; en Linux `./BACKEND` y `./backend` son carpetas distintas) y separar código, documentación, notas y datos. Solo se versionan datos con procedencia confirmada: las fichas oficiales, la tabla CIE-10 y los Excel sintéticos generados por `backend/scripts`.

### Estado

APROBADA. Reemplaza la nota anterior de `ARCHITECTURE.md` que pedía no renombrar `FRONTED`.

---

## DEC-004

### Fecha

2026-09-20

### Decisión

No mover el código de `backend` ni de `ia-service` a una subcarpeta `app/`, y usar comillas simples en Python (`ruff format`, `quote-style = "single"`).

### Motivo

Pasar a `app/` obliga a reescribir unos 110 imports de primer nivel, `Path('media')` (relativo al directorio de arranque), los scripts, los tests y el `CMD` de Docker, sin aportar funcionalidad. Se puede retomar como tarea aparte. Las comillas simples son la preferencia del equipo.

### Estado

APROBADA
