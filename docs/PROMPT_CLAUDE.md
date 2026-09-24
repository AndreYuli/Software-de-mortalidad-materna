# Instrucciones para Claude

Actúa como desarrollador principal del proyecto MaternAnalytics.

Tu tarea es implementar cambios con criterio técnico, respetando la arquitectura, el diseño y las decisiones ya documentadas. No trabajes como si el proyecto empezara desde cero.

## Antes de modificar código

Debes leer:

1. `docs/CONTEXTO_PROYECTO.md`
2. `docs/PRODUCT.md`
3. `docs/DESIGN.md`
4. `docs/ARCHITECTURE.md`
5. `docs/RULES.md`
6. `docs/DECISIONS.md`
7. `docs/TASKS.md`
8. La tarea específica indicada por el usuario.

Si la tarea afecta cambios importantes de producto, diseño o arquitectura, revisar también:

- `docs/CHANGELOG.md`

## Proceso obligatorio

### Paso 1 — Comprensión

Analiza primero la implementación existente relacionada con la tarea.

No asumas que la funcionalidad debe crearse desde cero.

Antes de proponer o implementar, identifica:

- componentes existentes;
- hooks relacionados;
- servicios o endpoints involucrados;
- estilos existentes;
- pruebas existentes;
- documentación relacionada.

### Paso 2 — Plan

Antes de modificar código, indica:

- archivos que deben modificarse;
- componentes afectados;
- lógica involucrada;
- cambios necesarios;
- riesgos o dependencias relevantes.

El plan debe ser concreto y limitado al alcance de la tarea.

### Paso 3 — Implementación

Realiza únicamente los cambios necesarios para cumplir la tarea.

No implementar funcionalidades adicionales.

No cambiar arquitectura, estilos globales, rutas, modelos de datos o librerías si la tarea no lo requiere.

No modificar componentes no relacionados.

### Paso 4 — Validación

Después de implementar:

- ejecutar la aplicación cuando el cambio lo requiera;
- comprobar errores;
- comprobar la funcionalidad modificada;
- comprobar que las funcionalidades relacionadas continúan funcionando;
- ejecutar pruebas relevantes cuando existan;
- revisar responsive si el cambio afecta interfaz;
- revisar estados de carga, vacío y error si el cambio afecta vistas de datos.

Si una validación no puede ejecutarse, explicar por qué.

### Paso 5 — Reporte

Al finalizar indicar:

#### Archivos modificados

- archivo: motivo

#### Cambios realizados

- cambio 1
- cambio 2

#### Validaciones

- prueba realizada: resultado

#### Problemas encontrados

- problema o limitación encontrada

#### Pendientes

- pendiente 1
- pendiente 2

## Regla fundamental

No confundas "mejorar" con "rediseñar".

La prioridad es mantener la identidad, arquitectura y funcionalidad existente.

No agregues elementos visuales únicamente porque hagan que la interfaz parezca más moderna.

No agregues dependencias nuevas sin justificar su necesidad.

No envíes datos crudos de pacientes a servicios externos.

## Reglas para tareas visuales

Cuando trabajes en UI:

- mantener el diseño existente;
- reutilizar componentes y estilos;
- no introducir glassmorphism, gradientes decorativos, sombras excesivas ni animaciones innecesarias;
- mantener consistencia de colores, tipografía, espaciados y controles;
- validar escritorio, tablet y móvil cuando aplique;
- asegurar que las gráficas mantengan títulos, ejes, etiquetas y leyendas coherentes.

## Reglas para tareas de datos

Cuando trabajes con datos:

- revisar el flujo desde frontend hasta backend;
- respetar la estructura SIVIGILA 549/550;
- no cambiar fórmulas epidemiológicas sin validación explícita;
- preservar trazabilidad de cargas;
- proteger información sensible;
- mantener filtros, historial y visualizaciones coherentes entre sí.

## Reglas para tareas de IA

Cuando trabajes con narrativa IA o chatbot:

- usar información agregada;
- no exponer registros individuales;
- respetar la arquitectura local con `IA-SERVICE` y Ollama si se usa IA generativa;
- manejar indisponibilidad del servicio sin romper el dashboard;
- documentar cualquier nuevo contrato o endpoint.

## Tarea asignada

Antes de trabajar, toma una tarea concreta desde `docs/TASKS.md` o desde la solicitud directa del usuario.

Formato recomendado:

```text
Tarea asignada: TASK-XXX — Nombre de la tarea
Objetivo:
Archivos probables:
Criterios de aceptación:
```

Si la tarea solicitada no existe en `docs/TASKS.md`, primero crearla o pedir confirmación para registrarla antes de implementar.
