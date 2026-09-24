# Auditoría TAREA 1 — Aseguramiento de la API

Fecha: 2026-09-19
Alcance: Revisión de la implementación de la TAREA 1 (Aseguramiento de la API).

## Resumen de la revisión

Tras revisar la implementación sin modificar los archivos, se confirma que se ha cumplido satisfactoriamente con:
- La inyección de la dependencia de autenticación (`Depends(get_current_user)`) en las rutas de datos (`analisis.py` y `sivigila.py`).
- La conservación de rutas públicas (`auth.py`, `/health`, login y registro).
- La deshabilitación del servicio estático de `/media` para no exponer archivos sensibles.
- El manejo de JWT en backend.
- La correcta gestión e inyección del `token` en el frontend usando `fetchWithTimeout`.
- La redirección y limpieza de sesión (`clearSession`) ante un error `401 Unauthorized`.
- La funcionalidad del dashboard, historial y carga de archivos con el flujo de autenticación implementado.

## Hallazgos detectados

A continuación se detalla el único hallazgo detectado durante la auditoría:

### Hallazgo 1
- **Severidad:** Baja (Inconsistencia de tipado estático)
- **Archivo:** `BACKEND/api/dependencies.py`
- **Componente o endpoint:** Función `get_current_user`
- **Problema:** La anotación de tipos declara que la función retorna la clase modelo (`type[Usuario]`), pero la lógica en realidad retorna una instancia autenticada de esa clase. Además, asume que el token decodificará el `"sub"` directamente como un entero, cuando en `core/security.py` se inyecta y codifica como string.
- **Evidencia:** 
  - Firma actual: `def get_current_user(...) -> type[Usuario]:` frente al retorno real que es `return user` (donde `user` viene de `db.get(Usuario, ...)`).
  - Asignación actual: `user_id: int | None = payload.get("sub")`. Al decodificarse en tiempo de ejecución, el diccionario de JWT devolverá un valor de tipo `str`.
- **Recomendación:** Cambiar la firma de la función para que retorne la instancia (es decir, `-> Usuario:` en lugar de `-> type[Usuario]:`) y corregir el tipado de la variable a `user_id: str | None = payload.get("sub")`.
