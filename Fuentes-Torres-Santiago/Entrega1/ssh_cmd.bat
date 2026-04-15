@echo off
:: ============================================================
::  ssh_cmd.bat  —  Script [cmd]
::  Ejecuta un comando remoto en la VM via SSH
::
::  Uso:
::    ssh_cmd.bat [comando]
::    ssh_cmd.bat [host] [comando]
::
::  Ejemplos:
::    ssh_cmd.bat uname -a
::    ssh_cmd.bat ciber-vm df -h
::    ssh_cmd.bat ciber-vm whoami
:: ============================================================

:: ── Configuración ───────────────────────────────────────────
set DEFAULT_HOST=ciber-vm
:: ────────────────────────────────────────────────────────────

if "%~1"=="" goto :uso

:: Verificar si el primer argumento es un host conocido
if /i "%~1"=="ciber-vm" (
    set HOST=%~1
    shift
) else (
    set HOST=%DEFAULT_HOST%
)

:: Juntar todos los argumentos restantes como el comando
set CMD=%1
:loop
shift
if "%~1"=="" goto :ejecutar
set CMD=%CMD% %1
goto :loop

:ejecutar
if "%CMD%"=="" goto :uso

echo [SSH] Ejecutando en %HOST%: %CMD%
echo.

ssh %HOST% %CMD%

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Comando ejecutado correctamente.
) else (
    echo.
    echo [ERROR] Fallo al ejecutar el comando.
)
goto :fin

:uso
echo.
echo  Uso: ssh_cmd.bat [host] [comando]
echo.
echo  Ejemplos:
echo    ssh_cmd.bat uname -a
echo    ssh_cmd.bat ciber-vm df -h
echo    ssh_cmd.bat ciber-vm whoami
echo.

:fin