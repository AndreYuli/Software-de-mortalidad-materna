# Validación de narrativas generadas por IA (tercer lote)

Verificación numérica de las narrativas del ia-service con el modelo del servidor (Groq, `openai/gpt-oss-20b`).
Mismo procedimiento que el segundo lote del manuscrito (3-nov-2026). Criterio completo: `criterio.md`.

No es parte de la suite de pruebas automáticas: llama a un servicio externo, el resultado varía entre ejecuciones y necesita una clave.

## Uso (PowerShell, desde esta carpeta)
Debe ser **PowerShell** (el prompt empieza con `PS`). En el Símbolo del sistema (cmd) los comandos con `$` no funcionan: escribe `powershell` para cambiar.
La clave de Groq (empieza con `gsk_`) se crea en https://console.groq.com → API Keys. No se pega en chats ni en archivos; este script no lee ningún `.env`.

    $s = Read-Host "Clave Groq" -AsSecureString
    $env:LLM_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
    python .\validacion3_gpt-oss.py              # indicadores -> 18 solicitudes -> análisis
    Remove-Item Env:LLM_API_KEY
    python .\validacion3_gpt-oss.py --simulado   # sin red ni clave: comprueba el flujo (salida en simulado/)

Si se corta (error 429, red), se vuelve a ejecutar y retoma las solicitudes ya guardadas.
Requiere el venv del backend (`backend/venv`) y los Excel de `frontend/maternanalytics/e2e/fixtures`.

## Archivos
- `validacion3_gpt-oss.py`: ejecuta el lote y analiza las cifras.
- `narrativa_verificacion_a520cdbf.py`: copia del verificador de la rama `correccion/aval-condicionado` (commit a520cdbf), el que se usó en el segundo lote. No está en `main`.
- `criterio.md`: criterio escrito antes de ejecutar.
- Salidas (se crean al ejecutar): `val3_indicadores.json`, `val3_narrativas.json`, `resultado_validacion3.json` y `.txt`.
