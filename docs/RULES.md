# Reglas para agentes de IA

## 1. Regla principal

No modificar código sin comprender primero la estructura existente.

Antes de realizar cambios:

1. inspeccionar el código relacionado;
2. identificar componentes afectados;
3. identificar dependencias;
4. identificar estilos existentes;
5. identificar comportamiento actual;
6. determinar el cambio mínimo necesario.

---

## 2. No rediseñar sin autorización

No modificar la identidad visual existente salvo que la tarea lo solicite explícitamente.

No introducir:

* gradientes decorativos;
* glassmorphism;
* sombras excesivas;
* animaciones innecesarias;
* exceso de tarjetas;
* iconos decorativos;
* colores nuevos sin justificación;
* componentes que no aporten información o funcionalidad.

---

## 3. Principio de mínimo cambio

Modificar solamente lo necesario para cumplir la tarea.

No realizar refactorizaciones no relacionadas.

No cambiar nombres de componentes, estructuras o archivos sin necesidad.

---

## 4. Datos primero

No modificar la lógica de negocio para solucionar problemas exclusivamente visuales.

Separar:

* datos;
* lógica;
* presentación;
* estilos.

---

## 5. Componentes existentes

Antes de crear un componente nuevo, comprobar si ya existe uno que pueda reutilizarse.

Evitar duplicación.

---

## 6. Gráficas

Las gráficas deben:

* tener títulos claros;
* tener ejes coherentes con la variable representada;
* actualizar correctamente sus etiquetas cuando cambien las variables;
* mantener consistencia visual;
* responder correctamente a filtros.

Nunca utilizar etiquetas genéricas cuando el contexto permita mostrar el nombre específico de la variable.

---

## 7. Dashboard

El dashboard debe priorizar:

1. comprensión;
2. comparación;
3. exploración;
4. lectura rápida;
5. consistencia.

La apariencia moderna no debe convertirse en el objetivo principal.

---

## 8. Validación obligatoria

Después de modificar código:

* ejecutar la aplicación;
* comprobar errores;
* comprobar las funcionalidades afectadas;
* comprobar responsive;
* comprobar que no se rompieron funcionalidades existentes.

Informar:

* archivos modificados;
* cambios realizados;
* pruebas ejecutadas;
* problemas encontrados.
