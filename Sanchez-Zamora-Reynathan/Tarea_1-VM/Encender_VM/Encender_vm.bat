@echo off
:: ============================================================
::  SSH AUTO-CONNECT - VMware Workstation
::  Enciende Ubuntu 64-bit y conecta via SSH con llave RSA
::  Passphrase se pide UNA sola vez por sesion de Windows
::  Sanchez Zamora Reynathan
:: ============================================================

title SSH VM - fak3me@192.168.106.128
color 0A

:: ─────────────────────────────────────────────────────────────
::  CONFIGURACION
:: ─────────────────────────────────────────────────────────────
set VM_USER=fak3me
set VM_IP=192.168.106.128
set VM_PORT=22
set KEY_PATH=C:\Users\Fakeme\.ssh\id_rsa
set VMRUN="C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
set VMX_PATH=C:\Users\Fakeme\OneDrive - Instituto Politecnico Nacional\Documents\Virtual Machines\Ubuntu 64-bit\Ubuntu 64-bit.vmx

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   SSH Auto-Connect - VMware Workstation          ║
echo  ║   VM   : Ubuntu 64-bit                          ║
echo  ║   Host : fak3me@192.168.106.128                 ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ─── PASO 1: Verificar llave privada ────────────────────────
echo  [1/5] Verificando llave RSA...
if not exist "%KEY_PATH%" (
    echo.
    echo  [ERROR] No se encontro la llave privada en:
    echo          %KEY_PATH%
    pause & exit /b 1
)
echo         OK - Llave encontrada

:: ─── PASO 2: Verificar vmrun.exe ────────────────────────────
echo  [2/5] Verificando VMware Workstation...
if not exist %VMRUN% (
    echo.
    echo  [ERROR] No se encontro vmrun.exe
    pause & exit /b 1
)
echo         OK - VMware Workstation detectado

:: ─── PASO 3: Encender la VM si esta apagada ─────────────────
echo  [3/5] Verificando estado de la VM...

%VMRUN% list 2>nul | findstr /i "Ubuntu 64-bit" >nul 2>&1
if %errorlevel% equ 0 (
    echo         OK - La VM ya esta encendida
    goto :wait_ssh
)

echo         Encendiendo VM: Ubuntu 64-bit...
%VMRUN% start "%VMX_PATH%" nogui >nul 2>&1
if %errorlevel% neq 0 (
    %VMRUN% start "%VMX_PATH%" >nul 2>&1
)
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] No se pudo encender la VM.
    echo          Verifica que el archivo exista en:
    echo          %VMX_PATH%
    pause & exit /b 1
)
echo         OK - VM encendida

:: ─── PASO 4: Esperar que SSH este disponible ────────────────
:wait_ssh
echo  [4/5] Esperando que SSH este disponible...
set /a INTENTOS=0
:loop_ssh
set /a INTENTOS+=1
if %INTENTOS% gtr 24 (
    echo.
    echo  [ERROR] La VM no respondio SSH en 2 minutos.
    echo          Verifica dentro de Ubuntu:
    echo            sudo systemctl enable ssh
    echo            sudo systemctl start ssh
    pause & exit /b 1
)
ssh -p %VM_PORT% -i "%KEY_PATH%" ^
    -o ConnectTimeout=5 ^
    -o StrictHostKeyChecking=no ^
    -o BatchMode=yes ^
    %VM_USER%@%VM_IP% exit >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 5 /nobreak >nul
    goto :loop_ssh
)
echo         OK - SSH disponible en %VM_IP%

:: ─── PASO 5: ssh-agent y cargar llave RSA ───────────────────
echo  [5/5] Iniciando agente SSH...

ssh-add -l 2>nul | findstr /i "id_rsa" >nul 2>&1
if %errorlevel% equ 0 (
    echo         OK - Llave RSA ya cargada en el agente
    goto :connect
)

sc query ssh-agent 2>nul | findstr "RUNNING" >nul 2>&1
if %errorlevel% neq 0 (
    net start ssh-agent >nul 2>&1
)

echo.
echo  ══════════════════════════════════════════════════════
echo   Ingresa la passphrase de tu llave RSA.
echo   Solo se pedira UNA VEZ - el agente la recordara
echo   durante toda tu sesion de Windows.
echo  ══════════════════════════════════════════════════════
echo.

ssh-add "%KEY_PATH%"

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Passphrase incorrecta o llave invalida.
    pause & exit /b 1
)
echo.
echo         OK - Llave RSA cargada. No se volvera a pedir.

:: ─── CONECTAR SSH ───────────────────────────────────────────
:connect
echo.
echo  ══════════════════════════════════════════════════════
echo   Conectando a fak3me@192.168.106.128 ...
echo  ══════════════════════════════════════════════════════
echo.

ssh -p %VM_PORT% ^
    -o StrictHostKeyChecking=no ^
    -o ServerAliveInterval=60 ^
    -o ServerAliveCountMax=3 ^
    %VM_USER%@%VM_IP%

echo.
echo  ══════════════════════════════════════════════════════
echo   Sesion SSH cerrada.
echo  ══════════════════════════════════════════════════════
echo.
pause