# Sistema de diseño: MaternAnalytics

Este documento define las reglas visuales y de experiencia de usuario para mantener la interfaz consistente. El diseño de la aplicación ya está construido; cualquier cambio debe respetar lo existente y modificar solamente lo necesario para la tarea solicitada.

La aplicación es una herramienta de trabajo para análisis de salud pública materna. Debe sentirse profesional, clara y específica para el problema que resuelve, no como una plantilla genérica de dashboard generada automáticamente.

## Objetivo visual

La aplicación debe tener una apariencia profesional, sobria y orientada al análisis epidemiológico.

El diseño debe ayudar a que la Secretaría de Salud o el usuario responsable pueda cargar información, filtrar datos, leer indicadores, interpretar gráficas y revisar hallazgos sin distracciones visuales.

No debe parecer una plantilla genérica de dashboard. Debe comunicar que está hecha para vigilancia y análisis de mortalidad materna y morbilidad materna extrema.

## Principios

### 1. Información antes que decoración

Los elementos visuales deben ayudar a comprender o utilizar la información.

No agregar elementos únicamente para decorar.

Cada bloque debe responder a una función clara:

- orientar al usuario;
- mostrar un indicador;
- permitir una acción;
- filtrar información;
- explicar una gráfica;
- presentar un estado de carga, vacío o error.

### 2. Jerarquía

La interfaz debe permitir identificar rápidamente:

1. contexto;
2. filtros;
3. indicadores;
4. visualizaciones;
5. detalles.

El usuario debe poder entender primero qué está viendo, luego qué filtros están activos, después cuáles son los indicadores principales y finalmente explorar visualizaciones o detalles.

### 3. Densidad

Evitar que cada componente ocupe innecesariamente toda la pantalla.

Cuando existan visualizaciones relacionadas, aprovechar el espacio horizontal. En escritorio, las gráficas comparables deben usar rejillas o columnas cuando sea razonable; en móvil deben apilarse sin romper lectura ni controles.

La interfaz debe ser densa en información útil, pero no saturada. El espacio vacío debe ayudar a leer, no inflar artificialmente la pantalla.

### 4. Consistencia

Mantener consistencia en:

- tipografías;
- colores;
- tamaños;
- espaciados;
- botones;
- controles;
- estados;
- estilos de gráficas;
- lenguaje visual entre módulos.

No crear un estilo diferente para cada componente. Antes de agregar una clase, patrón o variante nueva, revisar si ya existe una solución equivalente en `frontend/maternanalytics/src/components/` o en los CSS actuales.

### 5. Evitar apariencia genérica de IA

No introducir automáticamente:

- glassmorphism;
- gradientes decorativos;
- sombras excesivas;
- exceso de tarjetas;
- animaciones innecesarias;
- iconos decorativos;
- elementos flotantes sin función;
- colores aleatorios;
- efectos visuales solamente porque sean modernos.

La aplicación debe verse moderna por su claridad, orden y utilidad, no por efectos visuales.

### 6. Responsive

La interfaz debe funcionar correctamente en:

- escritorio;
- tablet;
- móvil.

Como mínimo, revisar anchos aproximados de 1280 px, 768 px y 375 px cuando se modifiquen pantallas o componentes visuales.

### 7. Visualizaciones

Las gráficas deben tener:

- título claro;
- variables identificables;
- ejes coherentes;
- etiquetas comprensibles;
- leyendas cuando sean necesarias;
- colores consistentes con el tipo de dato;
- estados claros cuando no haya datos suficientes.

Cuando una variable cambie dinámicamente, los textos asociados a la gráfica también deben actualizarse. No usar títulos genéricos si el contexto permite mostrar el nombre real de la variable.

Una gráfica debe responder una pregunta concreta. Si una tabla, indicador o texto explica mejor la información, no forzar una visualización compleja.

## Identidad visual actual

### Tipografía

La aplicación usa principalmente **Plus Jakarta Sans**.

Reglas:

- mantener la misma familia tipográfica en dashboard, formularios y navegación;
- evitar mezclar muchas fuentes;
- usar pesos tipográficos con intención: regular para lectura, semibold/bold para jerarquía;
- no aumentar tamaños de texto para compensar falta de estructura.

### Color

Tokens globales principales definidos en `frontend/maternanalytics/src/index.css`:

- escala principal (basada en morado #662d90) `--blue-100` a `--blue-900` (usada en login);
- acento `--pink-500`;
- escala de marca (basada en morado #662d90) `--brand-500`, `--brand-700`, `--brand-900` (usada en dashboard).

Reglas:

- usar tokens existentes antes de crear nuevos colores;
- no agregar colores aleatorios en componentes;
- mantener colores de datos separados de colores decorativos;
- no transmitir significado únicamente por color.

Colores semánticos de datos identificados:

- mortalidad: rojo;
- morbilidad: verde;
- riesgo: rojo o color de alerta;
- valores neutros: grises o tonos de baja jerarquía.

### Componentes y contenedores

Los contenedores deben tener bordes, radios, sombras y espaciados consistentes.

Reglas:

- evitar tarjetas dentro de tarjetas;
- no usar una tarjeta para cada texto si no aporta estructura;
- preferir secciones claras y compactas;
- mantener radios moderados;
- usar sombras con mucha moderación;
- evitar animaciones decorativas.

## Layout

La estructura principal del dashboard combina navegación lateral, área de contenido y panel de filtros.

Reglas:

- el contexto de análisis debe estar visible antes de las gráficas;
- los filtros deben estar cerca del contenido que afectan;
- los indicadores principales deben aparecer antes de visualizaciones detalladas;
- las vistas relacionadas deben agruparse por pestañas o secciones claras;
- las visualizaciones comparables deben aprovechar columnas en escritorio;
- el layout debe apilarse correctamente en tablet y móvil.

No convertir una tarea puntual de ajuste visual en un rediseño general de la pantalla.

## Componentes

Antes de crear un componente visual nuevo, comprobar si puede reutilizarse uno existente.

Componentes o patrones que deben reutilizarse cuando aplique:

- estados de carga;
- estados vacíos;
- estados de error;
- botones existentes;
- controles de filtro;
- pestañas;
- tarjetas de KPI;
- componentes de gráficas;
- tabla de historial;
- modales existentes.

Cada vista con datos debe contemplar:

- cargando;
- vacío;
- error;
- éxito.

Los mensajes deben mostrarse en la interfaz, no mediante `alert()`.

## Gráficas y visualizaciones

Las visualizaciones deben priorizar interpretación.

Reglas:

- título específico por variable o pregunta analítica;
- ejes con unidades o etiquetas entendibles;
- leyendas cuando haya más de una serie;
- colores consistentes entre mortalidad y morbilidad;
- etiquetas legibles en desktop y móvil;
- evitar saturación de texto;
- evitar visualizaciones complejas si no agregan comprensión;
- validar que filtros y textos cambien juntos.

Para cruces de variables, el usuario debe entender:

- variable sociodemográfica seleccionada;
- variable clínica seleccionada;
- total o universo analizado;
- categorías comparadas;
- ausencia de datos, si aplica.

Para grafos o Sankey, usarlos solamente si representan relaciones o flujos reales que no se entienden bien con una gráfica simple.

## Filtros y controles

Los filtros deben ser claros, visibles y reversibles.

Reglas:

- mostrar qué filtros están activos;
- permitir limpiar filtros;
- deshabilitar controles dependientes cuando falte el filtro padre;
- explicar dependencias cuando sea necesario;
- no ocultar filtros críticos;
- evitar controles duplicados que modifiquen el mismo dato desde lugares distintos.

Los filtros deben actualizar indicadores, gráficas y textos asociados de forma coherente.

## Accesibilidad

Mínimos obligatorios:

- contraste suficiente en texto e interfaz;
- foco visible en elementos interactivos;
- botones reales para acciones;
- campos con `label`;
- tablas semánticas cuando se presenten datos tabulares;
- nombres accesibles para botones con iconos;
- navegación usable con teclado;
- no depender solo del color para comunicar estados.

## CSS y mantenimiento visual

Reglas de mantenimiento:

- usar CSS plano por componente, como ya existe en el proyecto;
- preferir clases CSS sobre estilos inline, salvo valores realmente dinámicos;
- usar tokens existentes para color y espaciado cuando sea posible;
- no introducir otra metodología de estilos sin necesidad;
- no agregar `!important` salvo caso excepcional y justificado;
- si un archivo CSS crece demasiado, dividir por sección cuando se toque por una tarea relacionada.

## Regla para modificaciones visuales

No rediseñar toda la aplicación cuando la tarea solicite modificar solamente un componente.

Realizar el cambio mínimo necesario.

Antes de agregar un nuevo componente visual, comprobar si puede reutilizarse uno existente.

Antes de cambiar estilos globales, revisar qué pantallas dependen de ellos.

Antes de modificar gráficas, revisar datos, filtros, textos, estados y responsive.

## Checklist antes de dar por terminado un cambio visual

- El cambio respeta el diseño existente.
- No introduce decoración innecesaria.
- Mantiene jerarquía clara.
- Usa colores y tipografías consistentes.
- Funciona con datos reales, vacío, carga y error.
- No rompe filtros ni navegación.
- Las gráficas tienen títulos, ejes y etiquetas comprensibles.
- El componente responde bien en escritorio, tablet y móvil.
- El texto no se desborda ni se superpone.
- Las acciones son claras y accesibles.
