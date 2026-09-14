@echo off
set "BASE_DIR=%~dp0"

echo Iniciando las 4 terminales para el proyecto...

:: Terminal 1: Ollama
start "1. Ollama" cmd /k "ollama serve"

:: Terminal 2: IA-SERVICE
start "2. IA-SERVICE (Puerto 8001)" cmd /k "cd /d %BASE_DIR%IA-SERVICE && call venv\Scripts\activate && uvicorn main:app --reload --port 8001"

:: Terminal 3: BACKEND
start "3. BACKEND (Puerto 8000)" cmd /k "cd /d %BASE_DIR%BACKEND && call venv\Scripts\activate && uvicorn main:app --reload --port 8000"

:: Terminal 4: FRONTEND
start "4. FRONTEND (Puerto 5173)" cmd /k "cd /d %BASE_DIR%FRONTED\maternanalytics && pnpm dev"

echo ¡Las 4 terminales han sido lanzadas correctamente!
