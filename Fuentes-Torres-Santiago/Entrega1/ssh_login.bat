@echo off
:: ============================================================
::  ssh_login.bat  —  Script [login]
::  Abre sesión SSH interactiva hacia la VM
::
::  Uso:
::    ssh_login.bat              <- usa alias ciber-vm por defecto
::    ssh_login.bat [host]       <- host o alias personalizado
::
::  Ejemplo:
::    ssh_login.bat
::    ssh_login.bat ciber-vm
:: ============================================================

:: ── Configuración ───────────────────────────────────────────
set DEFAULT_HOST=ciber-vm
:: ────────────────────────────────────────────────────────────

if "%~1"=="" (
    set HOST=%DEFAULT_HOST%
) else (
    set HOST=%~1
)

echo [----------->] Conectando a %HOST%...
echo [----------->] Escribe 'exit' para cerrar la sesion.
echo.

ssh %HOST%

if %ERRORLEVEL%==0 (
    echo.
    echo [----------->] Sesion cerrada correctamente.
) else (
    echo.
    echo [ERROR] No se pudo conectar a %HOST%.
    echo [----------->]  Verifica que la VM este encendida.
    echo [----------->]  Alias configurado: ciber-vm ^| Usuario: debian ^| Puerto: 2222
)