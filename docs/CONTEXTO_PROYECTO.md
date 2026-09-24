# Contexto del proyecto

## Nombre de la aplicacion

**MaternAnalytics**

Nombre provisional/publico pensado para la aplicacion. Resume la idea central del sistema: analitica aplicada a salud materna.

## Descripcion

MaternAnalytics es una pagina web para apoyar el analisis de mortalidad materna y morbilidad materna extrema a partir de registros SIVIGILA. La aplicacion permite cargar archivos de casos, procesarlos, almacenarlos en una base de datos y visualizar la informacion mediante dashboards, graficas, filtros, historial de cargas y analisis estadistico.

El sistema tambien incorpora narrativa con inteligencia artificial local para generar interpretaciones de indicadores agregados. Como evolucion pendiente, se contempla un chatbot conversacional que permita consultar y explorar la informacion de forma asistida.

## Objetivo

El objetivo del proyecto es ayudar a las entidades de salud a comprender mejor los casos de morbilidad y mortalidad materna, identificar patrones, revisar causas, analizar tendencias y apoyar la toma de decisiones para prevenir nuevos eventos y mejorar la salud materna.

La aplicacion busca reducir el trabajo manual de consolidacion y analisis de archivos, facilitar la revision periodica de casos y ofrecer una herramienta clara para vigilancia epidemiologica, gestion institucional, analisis academico y apoyo a decisiones en salud publica.

## Usuarios principales

- Secretaria de Salud.
- Profesionales encargados de vigilancia epidemiologica.
- Analistas de salud publica.
- Personal institucional que realiza seguimiento a casos de morbilidad y mortalidad materna.
- Investigadores, docentes o estudiantes que trabajen con informacion agregada de salud materna.

## Datos que analiza

La aplicacion analiza registros de mujeres en condicion de morbilidad materna extrema o casos de mortalidad materna, incluyendo causas, caracteristicas del caso y variables disponibles en los archivos oficiales.

Los datos principales provienen de archivos Excel basados en eventos SIVIGILA:

- **SIVIGILA 549:** Morbilidad materna extrema.
- **SIVIGILA 550:** Mortalidad materna.

Estos archivos se cargan semanalmente en la aplicacion y se procesan para almacenar la informacion en una base de datos PostgreSQL. A partir de esa informacion se generan indicadores, graficas, filtros, historiales y analisis.

## Funcionalidades principales

- Carga de archivos Excel de mortalidad y morbilidad materna.
- Procesamiento de archivos SIVIGILA 549/550.
- Almacenamiento de los registros procesados en PostgreSQL.
- Dashboard con indicadores y visualizaciones.
- Graficas estadisticas para analizar distribuciones, causas, tendencias y cruces de variables.
- Filtros para explorar la informacion por variables relevantes.
- Historial de cargas realizadas.
- Narrativa con IA para interpretar indicadores agregados.
- Login y registro de usuarios.
- Exportacion o generacion de reportes, si aplica segun el estado actual del codigo.
- Chatbot conversacional con IA como funcionalidad pendiente o en evolucion.

## Modulos principales

- **Autenticacion:** login, registro y control de acceso.
- **Carga de archivos:** subida semanal de registros SIVIGILA 549/550.
- **Dashboard:** vista principal de indicadores y resumen analitico.
- **Graficas:** visualizacion de datos mediante ECharts y componentes existentes.
- **Filtros:** seleccion de variables para explorar y comparar datos.
- **Historial:** seguimiento de archivos y analisis cargados.
- **Narrativa IA:** interpretaciones generadas a partir de indicadores agregados.
- **Chatbot IA:** modulo pendiente para conversar con el sistema sobre los datos.
- **Backend/API:** servicios de procesamiento, persistencia y consulta.
- **Base de datos:** almacenamiento relacional en PostgreSQL.
- **IA-SERVICE:** microservicio local para generacion de narrativas con Ollama.

## Estado actual

La aplicacion se encuentra actualmente en desarrollo.

Estado conocido:

- Ya existe carga de archivos.
- Ya existe historial de cargas o analisis.
- Ya se visualizan graficas, aunque hay recomendaciones de mejora y ajustes de diseno pendientes.
- Existen filtros, pero falta validar completamente su funcionamiento.
- Existe narrativa IA, pero falta completar o integrar el chatbot conversacional.
- Existen login y registro.
- Hay decisiones tecnicas pendientes de conversar, especialmente alrededor de Docker y despliegue.

## Tecnologias

- **Frontend:** React, TypeScript, Vite.
- **Graficas:** ECharts; revisar componentes existentes antes de agregar otra libreria.
- **Backend:** Python, FastAPI.
- **Base de datos:** PostgreSQL.
- **Inteligencia artificial:** Ollama / IA generativa local.
- **Infraestructura:** Docker, pendiente de definicion final segun el despliegue esperado.

## Documentacion relacionada

Antes de modificar el proyecto, revisar tambien:

- `README.md`: instalacion, ejecucion y estructura general.
- `docs/PRODUCT.md`: decisiones y alcance de producto.
- `docs/ARCHITECTURE.md`: arquitectura tecnica comprobada contra el codigo.
- `docs/RULES.md`: reglas para agentes de IA.
- `docs/DESIGN.md`: reglas visuales y de diseno, si la tarea afecta la interfaz.
- `docs/TASKS.md`: tareas pendientes, si aplica.
- `docs/CHANGELOG.md`: historial de cambios relevantes.

## Regla principal para las IA

Antes de modificar codigo, cualquier IA o agente debe leer este documento y revisar el codigo existente relacionado con la tarea.

No asumir que una funcionalidad debe crearse desde cero si ya existe una implementacion parcial o completa.

No realizar cambios fuera del alcance de la tarea solicitada.

No cambiar arquitectura, librerias, estilos globales, rutas, modelos de datos o reglas de negocio sin revisar primero la implementacion actual y la documentacion relacionada.

Si la tarea toca visualizaciones, filtros, graficas, carga de archivos, historial, IA o autenticacion, primero se deben identificar los componentes, hooks, servicios y endpoints ya existentes.

## Criterios de trabajo recomendados

- Mantener cambios pequenos y enfocados.
- Respetar la estructura actual del proyecto.
- Reutilizar componentes, hooks y servicios existentes.
- Validar que los filtros afecten correctamente las graficas e indicadores.
- Proteger la informacion sensible y evitar enviar datos crudos de pacientes a servicios externos.
- Priorizar claridad, utilidad y consistencia sobre cambios visuales innecesarios.
- Documentar cambios importantes cuando afecten comportamiento, arquitectura o reglas de producto.

## Notas sobre el nombre

**MaternAnalytics** es un buen nombre para una herramienta de analisis en salud materna: es corto, profesional y conecta claramente maternidad con analitica.

Alternativas posibles, si el equipo quiere explorar nombres mas institucionales o en espanol:

- **VidaMaterna Analytics**
- **MaternaData**
- **SIVIMaterna**
- **Vigilancia Materna**
- **MaternaInsight**

Por ahora, MaternAnalytics funciona bien como nombre de producto, especialmente si se quiere conservar una identidad moderna y tecnica.
