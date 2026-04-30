@echo off
:: ============================================================
::  docker_login.bat  —  Script [login]
::  Abre sesion interactiva dentro de un contenedor Debian
::
::  Uso:
::    docker_login.bat                <- usa contenedor default
::    docker_login.bat [contenedor]   <- contenedor especifico
::
::  Ejemplos:
::    docker_login.bat
::    docker_login.bat mi-contenedor
:: ============================================================

:: ── Configuración ───────────────────────────────────────────
set DEFAULT_IMAGE=debian:bookworm-slim
set DEFAULT_NAME=ciber-docker
:: ────────────────────────────────────────────────────────────

if "%~1"=="" (
    set CONTENEDOR=%DEFAULT_NAME%
) else (
    set CONTENEDOR=%~1
)

echo [DOCKER] Abriendo sesion interactiva en %CONTENEDOR%...
echo [DOCKER] Escribe 'exit' para cerrar la sesion.
echo.

:: Verificar si el contenedor ya existe y esta corriendo
docker inspect --format="{{.State.Running}}" %CONTENEDOR% >NUL 2>&1
if %ERRORLEVEL%==0 (
    :: Contenedor existe, entrar a el
    docker exec -it %CONTENEDOR% /bin/bash
) else (
    :: Contenedor no existe, crear uno nuevo
    echo [DOCKER] Contenedor no encontrado. Creando uno nuevo...
    docker run -it --name %CONTENEDOR% %DEFAULT_IMAGE% /bin/bash
)

if %ERRORLEVEL%==0 (
    echo.
    echo [OK] Sesion cerrada correctamente.
) else (
    echo.
    echo [ERROR] No se pudo abrir la sesion.
    echo [INFO]  Verifica que Docker Desktop este corriendo.
)