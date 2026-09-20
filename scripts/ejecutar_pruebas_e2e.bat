@echo off
color 0B
echo ===================================================================
echo.
echo       Iniciando Pruebas End-to-End (E2E) de VidaMaterna
echo.
echo ===================================================================
echo.

:: Navegar a la carpeta del frontend (funciona lance desde donde se lance)
cd /d "%~dp0..\frontend\maternanalytics"

echo [!] Verificando e instalando dependencias de Playwright...
call pnpm install
:: (@playwright/test ya está en devDependencies de package.json)
:: Esto descarga los navegadores necesarios
call pnpm exec playwright install chromium --with-deps

echo.
echo [!] Lanzando la interfaz de Playwright...
echo     En la nueva ventana que se abra, presiona el boton "Play" 
echo     (triangulo verde) para ver como se ejecutan las pruebas.
echo.
echo     Para salir, simplemente cierra la ventana de pruebas.
echo.

:: Ejecutamos las pruebas con la interfaz gráfica (--ui) 
call pnpm exec playwright test --ui

echo.
echo ===================================================================
echo Pruebas finalizadas. 
echo Puedes encontrar el reporte en formato Markdown en:
echo frontend\maternanalytics\playwright-report.md
echo ===================================================================
pause
