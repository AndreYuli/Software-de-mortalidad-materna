# Producto: MaternAnalytics

Este documento describe el producto desde la perspectiva funcional. Debe servir tanto para el equipo humano como para agentes de IA que necesiten entender qué problema resuelve la aplicación antes de modificar código.

## Problema que resuelve

Las entidades de salud deben revisar periódicamente registros de morbilidad materna extrema y mortalidad materna reportados en SIVIGILA. Cuando este análisis se realiza de forma manual en archivos Excel, el proceso puede volverse lento, repetitivo y propenso a errores: se dificulta consolidar casos, comparar periodos, identificar causas frecuentes, detectar perfiles de riesgo y producir una lectura clara para la toma de decisiones.

MaternAnalytics busca convertir esos registros semanales en información interpretable: indicadores, gráficas, cruces de variables, historial de cargas y narrativas de apoyo que permitan entender mejor la situación de salud materna y actuar de forma preventiva.

## Objetivo del producto

El producto debe permitir que una persona encargada de la Secretaría de Salud o del seguimiento epidemiológico pueda:

- cargar archivos Excel de SIVIGILA 549 y 550;
- validar y procesar registros de morbilidad y mortalidad materna;
- consultar indicadores generales y específicos;
- filtrar la información por periodo y tipo de evento;
- analizar causas, tendencias, perfiles sociodemográficos y variables clínicas;
- revisar el historial de cargas realizadas;
- apoyarse en narrativa de IA local para interpretar indicadores agregados;
- consultar información adicional mediante un chatbot conversacional, cuando este módulo sea implementado.

La aplicación no reemplaza el criterio epidemiológico ni clínico. Su propósito es organizar la información, facilitar la interpretación y apoyar decisiones institucionales.

## Usuarios

- **Secretaría de Salud:** usuaria principal del sistema, encargada de cargar registros, revisar indicadores y hacer seguimiento institucional.
- **Profesionales de vigilancia epidemiológica:** analizan tendencias, eventos, causas, demoras y grupos de riesgo.
- **Analistas de salud pública:** exploran datos consolidados, filtros y cruces de variables para producir reportes o hallazgos.
- **Auditores, gestores e instituciones de salud:** consultan resúmenes y visualizaciones para apoyar decisiones de mejora.
- **Investigadores, docentes o estudiantes:** pueden usar información agregada para análisis académico, siempre respetando la protección de datos sensibles.

## Flujo principal

1. El usuario ingresa a la aplicación mediante login.
2. El usuario carga archivos Excel de mortalidad materna 550 o morbilidad materna extrema 549.
3. El sistema valida la estructura del archivo, procesa los registros y guarda la información en la base de datos.
4. El usuario entra al dashboard de análisis.
5. El usuario selecciona el evento o cohorte de análisis: 549 + 550 integrados, solo mortalidad 550 o solo morbilidad 549.
6. El usuario aplica los filtros necesarios por año, mes, semana o día.
7. El sistema presenta indicadores, gráficas y visualizaciones según los datos disponibles.
8. El usuario analiza las gráficas, compara periodos, revisa causas y explora cruces de variables.
9. El usuario puede consultar el historial de cargas para verificar archivos, fechas, registros y resúmenes de procesamiento.
10. El usuario puede consultar información adicional mediante narrativa IA y, a futuro, mediante chatbot conversacional.

## Funcionalidades

### Dashboard

El dashboard debe mostrar una vista clara del estado de la información materna cargada en el sistema. Debe priorizar indicadores de lectura rápida y visualizaciones útiles para análisis epidemiológico.

Debe mostrar:

- total de casos analizados;
- total de casos de mortalidad materna;
- total de casos de morbilidad materna extrema;
- tasa o indicador de letalidad, según la definición acordada por el equipo;
- comparación contra periodos anteriores cuando existan datos suficientes;
- última semana reportada;
- pestañas para generalidades, morbilidad y mortalidad;
- acceso a filtros de cohorte, periodo y exportación de reporte.

El dashboard no debe saturar al usuario con elementos decorativos. Cada bloque debe aportar información útil para comprender la situación materna.

### Gráficas

Las gráficas deben presentar información estadística de forma comprensible, consistente y filtrable.

Actualmente el sistema contempla o calcula visualizaciones sobre:

- evolución mensual de mortalidad y morbilidad;
- principales causas CIE-10;
- distribución por edad o grupos de edad;
- distribución por edad gestacional;
- distribución de edad por nivel de riesgo;
- variables sociodemográficas;
- variables clínicas;
- demoras relacionadas con mortalidad;
- fallas orgánicas y severidad en morbilidad, cuando existan datos;
- cruces entre variables sociodemográficas y clínicas.

Las gráficas deben responder correctamente a los filtros activos y mostrar nombres claros. No deben usar etiquetas genéricas si el sistema puede mostrar el nombre real de la variable.

### Grafos

Los grafos deben representar relaciones o flujos que sean difíciles de entender en tablas simples.

El backend incluye capacidad para construir un grafo tipo Sankey asociado a mortalidad, pensado para representar el flujo clínico entre etapas como tipo de parto, nivel de atención y momento de muerte. Esta visualización debe usarse solo si ayuda a entender trayectorias o relaciones relevantes dentro del proceso de atención.

Los grafos deben responder a preguntas como:

- ¿qué rutas o combinaciones aparecen con mayor frecuencia?
- ¿en qué etapa se concentran más casos?
- ¿qué relación existe entre variables clínicas o de atención?

No se deben agregar grafos únicamente por apariencia visual. Si una barra, tabla o cruce comunica mejor la información, se debe preferir la alternativa más clara.

### Filtros

Los filtros permiten delimitar el universo de análisis y deben afectar indicadores, gráficas y visualizaciones de forma consistente.

Filtros principales identificados en la aplicación:

- evento o cohorte de análisis: 549 + 550 integrados, solo mortalidad 550 o solo morbilidad 549;
- año de reporte;
- mes de reporte;
- semana de reporte;
- día de reporte;
- variables sociodemográficas en cruces: zona de residencia, población vulnerable, etnia y tipo de afiliación;
- variables clínicas en cruces, según el tipo de análisis.

Para mortalidad, los cruces clínicos pueden incluir variables como gestaciones, partos vaginales, cesáreas, tipo de parto y semana de gestación al momento del evento.

Para morbilidad, los cruces clínicos pueden incluir variables como número de gestaciones, partos vaginales, cesáreas, terminación de la gestación, edad gestacional y fallas orgánicas.

Los filtros deben ser visibles, comprensibles y reversibles. Si un filtro depende de otro, la interfaz debe dejar claro cuándo está habilitado o deshabilitado.

### Historial

El historial debe permitir revisar las cargas realizadas y entender qué información fue incorporada al sistema.

Debe contener:

- fecha y hora de carga;
- tipo de evento cargado: 549 morbilidad o 550 mortalidad;
- nombre del archivo;
- total de registros procesados;
- año, mes y semana (ISO, hora de Colombia) de la carga;
- buscador (archivo, tipo o evento 549/550) y filtros por evento, año, mes y semana;
- resumen del procesamiento, incluyendo pacientes nuevos, pacientes existentes, casos creados, casos actualizados o duplicados omitidos cuando aplique;
- paginación cuando existan muchas cargas.

El historial debe ayudar a auditar el proceso de carga y evitar confusión sobre qué archivos ya fueron incorporados.

### Chatbot

El chatbot es un módulo conversacional para consultar información del sistema en lenguaje natural.

Debe permitir preguntas como:

- ¿cuáles fueron las principales causas de mortalidad en un periodo?
- ¿qué grupo de edad presenta más casos?
- ¿cómo cambió la morbilidad respecto al periodo anterior?

El chatbot trabaja exclusivamente con información agregada y segura precalculada por el backend. No envía datos crudos de pacientes a servicios externos ni expone información sensible. Utiliza la arquitectura local de IA generativa (Ollama) como "lector" del contexto, asegurando total privacidad.

Estado actual: el chatbot conversacional se encuentra implementado e integrado en el dashboard como un panel flotante, con protección frente a fallos del servicio de IA local.

## Principios funcionales

La aplicación debe priorizar:

- claridad;
- facilidad de interpretación;
- consistencia;
- interacción útil;
- información relevante;
- protección de datos sensibles;
- trazabilidad de cargas y resultados;
- apoyo a decisiones de salud pública.

No agregar funcionalidades únicamente porque parezcan modernas o visualmente atractivas.

Cada nueva funcionalidad debe responder a una necesidad real del flujo de análisis: cargar, validar, filtrar, comparar, interpretar, consultar o reportar información.

## Alcance actual y pendientes relevantes

Funcionalidades existentes o parcialmente existentes:

- carga de archivos SIVIGILA 549/550;
- historial de cargas;
- dashboard con indicadores;
- gráficas de causas, distribuciones y cruces;
- filtros por evento y periodo;
- login y registro;
- narrativa IA basada en indicadores agregados;
- exportación de reporte desde el dashboard.

Pendientes o puntos a validar:

- validar completamente que todos los filtros actualicen correctamente indicadores y gráficas;
- revisar recomendaciones de diseño recibidas para las gráficas y el dashboard;
- revisar la integración visible de narrativa IA en el frontend;
- confirmar la definición estadística de indicadores sensibles como letalidad;
- fortalecer seguridad/autenticación en endpoints y acceso a archivos, según auditorías existentes;
- definir despliegue final con Docker u otra estrategia.

## Reglas de producto para futuras modificaciones

- Antes de crear una funcionalidad nueva, revisar si ya existe una implementación parcial.
- Antes de modificar gráficas o filtros, revisar los hooks, componentes y endpoints relacionados.
- No cambiar la lógica estadística sin validar la definición con el equipo.
- No introducir librerías visuales nuevas si ECharts o las librerías actuales resuelven el caso.
- No exponer datos sensibles de pacientes en servicios externos.
- Mantener la aplicación enfocada en análisis epidemiológico, no en decoración visual.
- Si se cambia el comportamiento principal del producto, actualizar este documento y `docs/CHANGELOG.md`.
