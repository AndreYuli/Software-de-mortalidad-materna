# Tareas Pendientes (TASKS)

Este documento coordina la ejecución de las reparaciones críticas y requerimientos detectados en el análisis del producto contra el código fuente real.

---

## Tareas priorizadas por producto

Estas tareas normalizan las correcciones solicitadas en la reunión del 2026-09-17 y en `correciones_mortalidad.md`. Los documentos adjuntos se usan como contexto; las instrucciones vigentes para implementación son las registradas aquí y en `PRODUCT.md`, `DESIGN.md`, `ARCHITECTURE.md` y `DECISIONS.md`.

---

## TASK-001 — Historial

### Objetivo

Mejorar la consulta y administración del historial de registros.

### Contexto

El historial actual permite revisar cargas, pero puede crecer mucho con el uso semanal. La usuaria solicitó agregar año, mes, semana, buscador, filtros y acciones para corregir cargas equivocadas.

### Requisitos

- Agregar columna de año.
- Agregar columna de mes.
- Agregar columna de semana.
- Agregar buscador.
- Agregar filtros.
- Agregar acciones para actualizar registros.
- Agregar acciones para eliminar registros.

### Restricciones

- No modificar información existente sin una acción explícita del usuario.
- No eliminar funcionalidades actuales.
- No modificar componentes no relacionados.
- Mantener el diseño existente.
- Proteger acciones destructivas con confirmación.
- Revisar impacto en datos consolidados antes de implementar actualización o eliminación.

### Archivos probables

- `frontend/maternanalytics/src/components/dashboard/UploadHistorySection.tsx`
- `frontend/maternanalytics/src/components/dashboard/UploadHistorySection.css`
- `frontend/maternanalytics/src/hooks/dashboard/useUploadHistory.ts`
- `frontend/maternanalytics/src/api.ts`
- `backend/api/routers/analisis.py`
- `backend/services/analisis_service.py`

### Criterios de aceptación

- [ ] Año visible.
- [ ] Mes visible.
- [ ] Semana visible.
- [ ] Buscador funcional.
- [ ] Filtros funcionales.
- [ ] Actualizar funciona según definición de producto.
- [ ] Eliminar funciona con confirmación y seguridad.
- [ ] No se rompen funcionalidades existentes.

### Relación con tareas existentes

Relacionado con la antigua **TAREA 6: Historial con columnas de periodo, buscador, filtros y acciones**.

---

## TASK-002 — Distribución de gráficas

### Objetivo

Mejorar la distribución de las visualizaciones.

### Contexto

Las gráficas relacionadas no deben obligar al usuario a hacer desplazamiento vertical innecesario cuando hay espacio horizontal disponible. Esta decisión quedó aprobada en `DEC-001`.

### Requisitos

- Permitir visualizar gráficas relacionadas lado a lado cuando el espacio lo permita.
- Reducir desplazamiento vertical innecesario.
- Mantener legibilidad.
- Mantener diseño responsive.

### Restricciones

- No rediseñar toda la aplicación.
- No agregar elementos decorativos.
- No cambiar la identidad visual.
- No modificar la lógica de datos.

### Archivos probables

- `frontend/maternanalytics/src/components/dashboard/SociodemographicChartsSection.tsx`
- `frontend/maternanalytics/src/components/dashboard/StrategicDashboard.css`

### Criterios de aceptación

- [x] Las gráficas relacionadas pueden aparecer en la misma fila.
- [x] En pantallas pequeñas se reorganizan correctamente.
- [x] Los filtros continúan funcionando.
- [x] Las gráficas continúan funcionando.
- [x] No se agregan dependencias visuales innecesarias.

### Relación con tareas existentes

Reemplaza o normaliza **TASK-023 — Reorganizar gráficas sociodemográficas**.

---

## TASK-003 — Ejes dinámicos

### Objetivo

Hacer que las etiquetas de las gráficas sean coherentes con las variables seleccionadas.

### Problema actual

Algunas gráficas mantienen etiquetas genéricas como "Casos" aunque la variable representada haya cambiado. Esto dificulta entender qué dato se está leyendo.

### Requisitos

Cuando el usuario cambie la variable:

- actualizar el título correspondiente;
- actualizar el eje X cuando corresponda;
- actualizar el eje Y cuando corresponda;
- mantener coherencia con los datos representados;
- actualizar textos de apoyo o lecturas automatizadas si dependen de la variable.

### Restricciones

- No modificar la lógica de datos.
- No cambiar la librería de gráficas.
- No rediseñar el componente completo.
- Mantener estilos existentes.

### Archivos probables

- `frontend/maternanalytics/src/components/dashboard/CruceVariablesSection.tsx`
- `frontend/maternanalytics/src/hooks/dashboard/useCruceVariables.ts`
- `frontend/maternanalytics/src/utils/aiChartInsights.ts`

### Criterios de aceptación

- [x] Las etiquetas corresponden a la variable seleccionada.
- [x] Los títulos cambian correctamente.
- [x] Los filtros continúan funcionando.
- [x] No existen etiquetas contradictorias.
- [x] El eje indica claramente si representa número de casos, categorías o la variable seleccionada.

### Relación con decisiones

Implementa `DEC-002`.

---

## TASK-004 — Chatbot

### Objetivo

Implementar un chatbot que ayude al usuario a interpretar la información presentada.

### Contexto

La reunión menciona un "chat para charlar con la guía" que ayude en la interpretación. El documento de correcciones lo describe como chatbot de preguntas frecuentes. Actualmente existe narrativa IA local, pero no un chatbot conversacional completo.

### Requisitos iniciales

- Incorporar un espacio de chatbot dentro de la plataforma.
- Permitir preguntas frecuentes sobre uso, interpretación de gráficas e indicadores.
- Responder con base en información agregada y segura.
- Mantener la regla de privacidad: no enviar datos crudos de pacientes a servicios externos.
- Definir si será un FAQ guiado, un chatbot con IA local o una combinación.

### Pendiente de definición

- Alcance exacto de preguntas.
- Ubicación en la interfaz.
- Si consulta datos filtrados del dashboard o solo responde preguntas generales.
- Si usa `IA-SERVICE`/Ollama o respuestas predefinidas.
- Criterios de seguridad y auditoría.

### Restricciones

- No usar servicios externos de IA con datos sensibles.
- No bloquear el dashboard si el servicio de IA no está disponible.
- No exponer registros individuales de pacientes.
- No implementar hasta cerrar alcance mínimo de producto.

### Archivos probables

- `frontend/maternanalytics/src/components/`
- `frontend/maternanalytics/src/api.ts`
- `backend/api/routers/analisis.py` o un router nuevo si se justifica.
- `ia-service/` si se decide usar IA local.

### Criterios de aceptación

- [ ] Alcance del chatbot definido.
- [ ] Interfaz integrada sin romper el dashboard.
- [ ] Respuestas útiles para interpretar la información.
- [ ] No se envían datos crudos de pacientes a servicios externos.
- [ ] El sistema maneja errores o indisponibilidad de IA.
- [ ] Se documenta el comportamiento en `PRODUCT.md` y `ARCHITECTURE.md`.

### Estado

PROPUESTA. Requiere definición de producto antes de implementación.

---

## TAREA 1: Aseguramiento de la API (Endpoints desprotegidos)

**Problema:**
Durante la revisión del código se comprobó que `api/routers/analisis.py` y `api/routers/sivigila.py` no implementan dependencias de seguridad. Cualquier cliente que haga peticiones a estos endpoints obtendrá los datos sin verificar el token de sesión. Además, en el frontend (`App.tsx`), `ProtectedRoute` solo comprueba que el token exista en `localStorage`, lo cual es fácilmente falsificable.

**Resultado Esperado:**
Bloquear el acceso a todos los datos epidemiológicos y de pacientes para que solo los usuarios logueados válidos (con JWT emitido por FastAPI) puedan leer o escribir. Si un usuario tiene un token caducado, la interfaz debe obligarlo a iniciar sesión.

**Impacto:** Evita fuga de datos sensibles clínicos.

**Criterios de Aceptación:**
- [x] Proteger `analisis.py` y `sivigila.py` con `APIRouter(..., dependencies=[Depends(get_current_user)])` (Backend). `auth.py` queda público. *(Corregido 2026-09-19: la versión anterior proponía `db: Session = Depends(get_current_user)`, que rompería la inyección de la sesión de BD.)*
- [x] `/media` no debe servirse como estático público (contiene los Excel con datos de pacientes): quitar el `mount` o servirlo con endpoint autenticado.
- [x] `ProtectedRoute`/`PublicOnlyRoute` (`App.tsx`) deben exigir `token`, no `username`.
- [x] Implementar un interceptor o lógica de Fetch en React (`api.ts`) que adjunte el token como `Bearer` en los headers de todas las llamadas.
- [x] Si una petición al backend devuelve `401 Unauthorized`, el frontend debe eliminar el token local y redirigir a `/login`.

---

## TAREA 2: Corrección de Fórmula Epidemiológica (Tasa de Letalidad)

**Problema:**
En `frontend/maternanalytics/src/hooks/dashboard/useDashboardMetrics.ts` (Línea 82), la Tasa de Letalidad se calcula como `(totalMortalidad / totalMorbilidad * 100)`. Matemáticamente esto es una "Razón de Mortalidad/Morbilidad", no la verdadera "Tasa de Letalidad", que debería calcular la proporción de muertes sobre el **total de los casos**. Además, si no hay registros de morbilidad, puede ocasionar errores de división por cero o resultados estadísticamente inválidos.

**Resultado Esperado:**
Un cálculo estadístico fiel al concepto epidemiológico y resistente a ceros en el denominador.

**Impacto:** Recuperar la validez de la información entregada a los analistas de salud pública.

**Criterios de Aceptación:**
- [x] Cambiar la fórmula en `useDashboardMetrics.ts` para que sea: `(totalMortalidad / (totalMortalidad + totalMorbilidad)) * 100`. (O simplemente dividir entre `totalCasos` asumiendo que `totalCasos = Mortalidad + Morbilidad`).
- [x] Ajustar la condicional para prevenir división por 0 cuando `totalCasos === 0`.
- [x] Cambiar las etiquetas correspondientes en las tarjetas UI para que se llame apropiadamente "Tasa de Letalidad" con el cálculo modificado.

---

## TAREA 3: Arreglo de Navegación Post-Carga y UX (Código Muerto)

**Problema:**
Tras subir un Excel exitosamente en `UploadSection`, la función `handleUploadSuccess` ejecuta un `setActiveView('analisis')` esperando que cambie la pantalla. Sin embargo, en `DashboardOKD.tsx`, `activeView` está atado a un `useMemo` dependiente de `location.pathname` (la URL). Como la URL nunca cambia en esa función, el usuario se queda atascado viendo el formulario de subida en vez de los resultados.

**Resultado Esperado:**
Tras una subida exitosa, la página navega físicamente hacia el panel estadístico del dashboard.

**Impacto:** Evita la frustración de la usuaria, completando el flujo natural de carga -> análisis.

**Criterios de Aceptación:**
- [x] Reemplazar `setActiveView('analisis')` por `navigate('/dashboard')` (o la ruta correspondiente al panel de control) en `useDashboardData.ts` o donde aplique el router hook.
- [x] Remover cualquier `useState` de vistas muertas si toda la app va a depender de las rutas (`location.pathname`).

---

## TAREA 4: Reactivar y Mostrar Narrativas IA

**Problema:**
El backend de IA procesa, guarda en DB y genera resúmenes. Existe un componente `<NarrativaIA />` en React ya programado y funcional, pero **no está siendo invocado ni mostrado en ninguna de las vistas principales** del `DashboardOKD.tsx`. 

**Resultado Esperado:**
Aprovechar la infraestructura local desplegada de Ollama, mostrando el texto generado de manera prominente pero opcional.

**Impacto:** Cierra el ciclo de valor prometido por el sistema sin alterar la exploración manual de datos.

**Criterios de Aceptación:**
- [x] Importar `<NarrativaIA />` en la vista que muestra el resumen estadístico principal (probablemente `AnalysisHomeSection.tsx`).
- [x] Asegurarse de que el componente reacciona asincrónicamente y no bloquea el render de los KPIs circundantes.

---

## TAREA 5: Una sola ruta con layout anidado

**Problema:** `App.tsx` repite 5 `<Route>` que montan `<DashboardOKD/>`; al navegar entre carga/historial/dashboard el componente se remonta y se pierden pestañas y segmento seleccionado (AUDITORIA-01 H-21).
**Resultado esperado:** `DashboardOKD` como layout con `<Outlet/>`; las vistas son rutas hijas. La URL sigue siendo la fuente de verdad (ARCHITECTURE §4).
**Archivos:** `src/App.tsx`, `src/components/DashboardOKD.tsx`, `src/components/dashboard/ViewRouter.tsx`.
**Criterios de aceptación:**
- [x] Una sola `ProtectedRoute` envuelve el layout.
- [x] Cambiar de /dashboard a /historial y volver conserva pestaña y filtros.
- [x] Se elimina el `setActiveView` muerto (coordinar con TAREA 3). `tsc -b` y `vitest run` en verde.

---

## TAREA 6: Historial con columnas de periodo, buscador, filtros y acciones

**Origen:** reunión 2026-09-17 y `notes/notas.md`. **Depende de decisión de producto** en las acciones (ver abajo).
**Problema:** el historial crecerá mucho; hoy no permite buscar ni corregir cargas equivocadas.
**Resultado esperado:** tabla con columnas **Año, Mes, Semana**, buscador de texto, filtros por tipo/año/mes/semana y columna **Acción**.
**Archivos:** `UploadHistorySection.tsx/.css`, `hooks/dashboard/useUploadHistory.ts`, `backend/api/routers/analisis.py` (`/analisis/historial/` con parámetros de búsqueda/filtro).
**Criterios de aceptación:**
- [ ] Buscador y filtros funcionan en el servidor (paginación intacta) y hay estado vacío "sin resultados".
- [ ] Acción **Eliminar**: `DELETE /analisis/{pk}/` autenticado, con modal de confirmación accesible (DESIGN §4). Debe definirse qué pasa con los pacientes/casos ya consolidados de esa carga.
- [ ] Acción **Actualizar**: **NO implementar** hasta que producto defina si significa reemplazar el archivo de una semana. PRODUCT §4.3 hoy dice "sin edición/borrado desde la app": esta tarea lo modifica y requiere actualizar PRODUCT.md primero.
- [ ] Tests de backend para filtro/búsqueda y borrado.

---

## TAREA 7: Gráficos sociodemográficos en rejilla de 2 columnas

> **Reemplazada por TASK-023** (más abajo). No implementar esta; se conserva solo por trazabilidad. El punto del eje X del cruce sigue pendiente de tarea aparte.

**Origen:** reunión 2026-09-17 ("más estilo dashboard, todas más chiquitas, no hacia abajo").
**Archivos:** `SociodemographicChartsSection.tsx`, `StrategicDashboard.css`.
**Criterios de aceptación:**
- [ ] Rejilla de 2 columnas ≥ 1024 px, 1 columna en móvil; gráficos de igual altura por fila.
- [ ] Sin `style={{}}` nuevos ni hex sueltos; tipografía y colores según DESIGN §2.
- [ ] Verificación visual a 375/768/1280 px con capturas.
- [ ] Relacionado: al cambiar la variable del cruce, el eje X debe reflejar esa variable (`notes/notas.md`) — especificar en tarea aparte tras revisar `CruceVariablesSection.tsx`.

---

## Fuera de tareas (pendiente de decisión de producto)
- **Chatbot** (`notes/notas.md`): sin alcance definido y en tensión con la regla de privacidad de IA. No se planifica hasta que producto lo especifique.

---

# TASK-023

## Título

Reorganizar gráficas sociodemográficas

## Contexto

Actualmente las gráficas aparecen verticalmente.

## Problema

La distribución genera demasiado desplazamiento vertical y dificulta comparar visualizaciones relacionadas.

## Objetivo

Mejorar la distribución espacial de las visualizaciones.

## Requisitos

- Mostrar dos gráficas relacionadas en una fila cuando sea posible.
- Mantener responsive.
- Mantener legibilidad.
- Mantener filtros existentes.
- Mantener lógica de datos.

## No hacer

- No cambiar colores.
- No rediseñar toda la página.
- No agregar nuevas métricas.
- No modificar la lógica de generación de datos.

## Notas de arquitectura/diseño (Claude Code, 2026-09-19)

- **Archivos probables:** `frontend/maternanalytics/src/components/dashboard/SociodemographicChartsSection.tsx` y `StrategicDashboard.css`. Confirmar antes de editar; el cambio debe ser de layout (CSS grid), no de datos.
- **Origen:** reunión 2026-09-17 ("más estilo dashboard, más chiquitas, no hacia abajo"). Pares sugeridos: los que comparten variable o dominio (p. ej. zona de residencia / población vulnerable; etnia / tipo de afiliación). Un gráfico ancho por naturaleza (muchas categorías, top-10 causas) puede permanecer a ancho completo.
- **Breakpoints:** 2 columnas desde ≥ 1024 px; 1 columna en móvil. Ambas gráficas de una fila con la misma altura.
- **ECharts/Chart.js** deben redimensionarse al cambiar el ancho del contenedor (comprobar que no queden con el ancho anterior).
- Sin `style={{}}` nuevos ni hex sueltos (DESIGN §5); el layout va en clases CSS.
- Verificar con la app levantada a 375 / 768 / 1280 px, con capturas (RULES §8 y DESIGN §8).

## Criterios de aceptación

- [x] Las gráficas relacionadas pueden aparecer lado a lado.
- [x] En móvil se muestran en una columna.
- [x] Los filtros siguen funcionando.
- [x] Las gráficas siguen actualizándose.
- [x] No aparecen errores en consola.
- [x] No se modificaron funcionalidades no relacionadas.
