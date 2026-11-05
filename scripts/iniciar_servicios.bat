@echo off
set "BASE_DIR=%~dp0..\"

echo Iniciando las 4 terminales para el proyecto...

:: Terminal 1: IA-SERVICE
start "1. IA-SERVICE (Puerto 8001)" cmd /k "cd /d %BASE_DIR%ia-service && call venv\Scripts\activate && uvicorn main:app --reload --port 8001"

:: Terminal 2: BACKEND
start "2. BACKEND (Puerto 8000)" cmd /k "cd /d %BASE_DIR%backend && call venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: Terminal 3: FRONTEND
start "3. FRONTEND (Puerto 5173)" cmd /k "cd /d %BASE_DIR%frontend\maternanalytics && pnpm dev"

:: Terminal 4: NGROK (acceso publico)
start "4. NGROK (acceso publico)" cmd /k ""%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" start --all"

echo ¡Las 4 terminales han sido lanzadas correctamente!
echo Espera unos segundos y revisa la terminal de NGROK para ver la URL publica.
