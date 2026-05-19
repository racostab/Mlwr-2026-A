@echo off
:: ============================================================
::  docker_cmd.bat  —  Script [cmd]
::  Ejecuta un comando dentro de un contenedor Debian
::
::  Uso:
::    docker_cmd.bat [comando]
::    docker_cmd.bat [contenedor] [comando]
::
::  Ejemplos:
::    docker_cmd.bat whoami
::    docker_cmd.bat ciber-docker ls -la
::    docker_cmd.bat ciber-docker uname -a
:: ============================================================

:: ── Configuración ───────────────────────────────────────────
set DEFAULT_NAME=ciber-docker
set DEFAULT_IMAGE=debian:bookworm-slim
:: ────────────────────────────────────────────────────────────

if "%~1"=="" goto :uso

:: Detectar si el primer argumento es el contenedor
if "%~2"=="" (
    set CONTENEDOR=%DEFAULT_NAME%
    set CMD=%~1
) else (
    set CONTENEDOR=%~1
    set CMD=%~2
)

:: Juntar argumentos restantes
:loop
shift /2
if "%~2"=="" goto :verificar
set CMD=%CMD% %~2
goto :loop

:verificar
if "%CMD%"=="" goto :uso

echo [DOCKER] Ejecutando en %CONTENEDOR%: %CMD%
echo.

:: Verificar si el contenedor existe
docker inspect %CONTENEDOR% >NUL 2>&1
if %ERRORLEVEL%==0 (
    :: Contenedor existe — verificar si esta corriendo
    for /f "tokens=*" %%i in ('docker inspect --format="{{.State.Running}}" %CONTENEDOR%') do set RUNNING=%%i
    if "%RUNNING%"=="true" (
        :: Esta corriendo — ejecutar directo
        docker exec %CONTENEDOR% /bin/bash -c "%CMD%"
    ) else (
        :: Esta detenido — iniciarlo primero
        echo [DOCKER] Contenedor detenido. Iniciando...
        docker start %CONTENEDOR% >NUL 2>&1
        timeout /t 2 /nobreak >NUL
        docker exec %CONTENEDOR% /bin/bash -c "%CMD%"
    )
) else (
    :: No existe — crear contenedor temporal
    echo [DOCKER] Contenedor no encontrado. Ejecutando en contenedor temporal...
    docker run --rm %DEFAULT_IMAGE% /bin/bash -c "%CMD%"
)

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Comando ejecutado correctamente.
) else (
    echo.
    echo [ERROR] Fallo al ejecutar el comando.
    echo [INFO]  Verifica que Docker Desktop este corriendo.
)
goto :fin

:uso
echo.
echo  Uso: docker_cmd.bat [contenedor] [comando]
echo.
echo  Ejemplos:
echo    docker_cmd.bat whoami
echo    docker_cmd.bat ciber-docker ls -la
echo    docker_cmd.bat ciber-docker uname -a
echo.

:fin