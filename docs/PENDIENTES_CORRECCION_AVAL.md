# Pendientes tras la corrección al aval condicionado (al 4-nov-2026)

Lo ya hecho está en `CAMBIOS_CORRECCION_AVAL.md`. Los pendientes de fase 1 anteriores siguen en `PENDIENTES_FASE1.md`.

## Servidor / despliegue
- [ ] Llevar la rama `correccion/aval-condicionado` al servidor (hoy solo está en local, sin push).
- [ ] Cambiar `OLLAMA_MODEL` en el `.env` del ia-service (NVIDIA retiró `meta/llama-3.2-11b-vision-instruct`: da 404 aunque `/v1/models` lo liste). Candidatos que responden: `meta/llama-3.2-90b-vision-instruct`, `google/gemma-4-31b-it`. Probar con una petición real. Si cambia el modelo, actualizar el artículo y la Figura 7.
- [ ] Rotar `jwt_secret` (valor por defecto en `backend/core/config.py`) y la clave de NVIDIA.
- [ ] El script SQL trae `DROP DATABASE sivigila_maternidad` (preexistente): no ejecutarlo contra el servidor real.
- [ ] El contador de intentos de login vive en memoria de cada proceso: con varios procesos cada uno cuenta aparte.

## Funcionalidad
- [ ] Ítems 1 y 2 de la matriz: no hay modelo de asociación, solo frecuencia.
- [ ] Ítem 7 (campos compartidos entre mortalidad y morbilidad): se reevaluó y no se unificó. Si la asesora exige corregirlo, hay que diseñar tabla común + extensiones por evento (toca ~10 archivos).
- [ ] Ítem 9: falta la revisión clínica de las narrativas por profesionales (el lote solo mide cifras y reglas de texto).
- [ ] Registro abierto: decidir verificación de correo institucional y aprobación de un administrador.
- [ ] Sin autenticación multifactor. Mínimo de contraseña de 8: por debajo de los 15 de NIST SP 800-63B-4 para un solo factor (declarado en el artículo (5)). Subirlo a 15 o agregar MFA lo resolvería.
- [ ] Los commits no incluyen aún el cambio a 8 (hay que confirmarlo).
- [ ] La lista de contraseñas comunes es corta, de ejemplo.
- [ ] La validación CIE-10 está en la aplicación, no en la base (sin llave foránea a un catálogo).
- [ ] Los hallazgos menores de la revisión de uso están en `respuesta_a_la_matriz_de_la_asesora_3-nov_v2.txt`.

## Calidad
- [ ] ESLint del front: 10 errores en archivos no tocados (deuda anterior).
- [ ] Los `.xlsx` de `e2e/fixtures` están ignorados por `.gitignore`: copiarlos del repo original para correr Playwright en otro lugar.
- [ ] Los CSV de relevancia se versionaron con `git add -f` (el `.gitignore` ignora `*.csv`).

## Rama
- [ ] Decidir cómo integrar: merge o PR hacia `develop`/`main`. La rama `test/e2e-historias-usuario` tiene cambios sin confirmar: no tocarla.
