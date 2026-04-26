@echo off
echo ========================================
echo   SHADOW_DEV Portfolio - Servidor Local
echo ========================================
echo.
echo Iniciando servidor en http://localhost:8000
echo Abre ESE link en tu navegador (NO el archivo directo)
echo.
echo Presiona Ctrl+C para detener el servidor.
echo.

:: Try Python 3
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Usando Python...
    python -m http.server 8000
    goto end
)

:: Try Python launcher
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo Usando Python (py)...
    py -m http.server 8000
    goto end
)

:: Try Node.js with npx
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo Usando Node.js / npx serve...
    npx serve -l 8000 .
    goto end
)

echo ERROR: No se encontro Python ni Node.js instalado.
echo Instala Python desde https://python.org y vuelve a intentar.
pause

:end
