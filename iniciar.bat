@echo off
title SolarSite Analytics
echo.
echo  =====================================================
echo      SolarSite Analytics - Instalador / Launcher
echo  =====================================================
echo.

cd /d "%~dp0"

:: ── Verificar que Python esté instalado ───────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no esta instalado o no esta en el PATH.
    echo  Descargalo desde https://www.python.org/downloads/
    echo     Asegurate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b
)

echo  Python detectado
echo.

:: ── Crear entorno virtual solo si no existe ───────────────────────────────
if not exist ".venv\" (
    echo  Creando entorno virtual por primera vez...
    python -m venv .venv
    if errorlevel 1 (
        echo  ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b
    )
    echo  Entorno virtual creado
    echo.
) else (
    echo  Entorno virtual ya existe, omitiendo creacion
    echo.
)

:: ── Activar entorno virtual ───────────────────────────────────────────────
call .venv\Scripts\activate
if errorlevel 1 (
    echo  ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b
)

:: ── Instalar dependencias solo si falta streamlit ─────────────────────────
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo  Instalando dependencias desde requirements.txt...
    echo       Esto puede tardar unos minutos la primera vez.
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt --progress-bar on
    if errorlevel 1 (
        echo  ERROR: Fallo la instalacion de dependencias.
        pause
        exit /b
    )
    echo.
    echo  Dependencias instaladas correctamente
    echo.
) else (
    echo  Dependencias ya instaladas, omitiendo
    echo.
)

:: ── Lanzar la aplicación ──────────────────────────────────────────────────
echo  Iniciando SolarSite Analytics...
echo.
echo  Para cerrar la aplicacion presiona CTRL + C
echo  ____________________________________________________________
echo.

streamlit run app.py

pause