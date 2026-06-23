@echo off
title SolarSite Analytics
echo.
echo  =====================================================
echo   ☀️   SolarSite Analytics — Instalador / Launcher
echo  =====================================================
echo.

cd /d "%~dp0"

:: ── Verificar que Python esté instalado ───────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no está instalado o no está en el PATH.
    echo  Descárgalo desde https://www.python.org/downloads/
    echo     Asegúrate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b
)

echo  Python detectado
echo.

:: ── Crear entorno virtual solo si no existe ───────────────────────────────
if not exist "venv\" (
    echo  Creando entorno virtual por primera vez...
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b
    )
    echo  Entorno virtual creado
    echo.
) else (
    echo  Entorno virtual ya existe, omitiendo creación
    echo.
)

:: ── Activar entorno virtual ───────────────────────────────────────────────
call venv\Scripts\activate
if errorlevel 1 (
    echo  ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b
)

:: ── Instalar dependencias solo si falta streamlit ─────────────────────────
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo  Instalando dependencias desde requirements.txt...
    echo     Esto puede tardar unos minutos la primera vez.
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  ERROR: Falló la instalación de dependencias.
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
echo  🌐 Iniciando SolarSite Analytics...
echo  👉 Se abrirá en: http://localhost:8501
echo.
echo  Para cerrar la aplicación presiona CTRL + C
echo  ─────────────────────────────────────────────
echo.

streamlit run app.py

pause