x@echo off
REM ============================================
REM  Script-VB: Control de VMs con VBoxManage
REM  Uso: control_vm.bat [accion] [nombre_vm]
REM  Acciones de este SCRIPT: start | stop | pause | resume | status | snapshot
REM ============================================

SET VM_NAME=%2
IF "%VM_NAME%"=="" SET VM_NAME=AlpineVM

IF "%1"=="start"    GOTO START
IF "%1"=="stop"     GOTO STOP
IF "%1"=="pause"    GOTO PAUSE
IF "%1"=="resume"   GOTO RESUME
IF "%1"=="status"   GOTO STATUS
IF "%1"=="snapshot" GOTO SNAPSHOT
GOTO USAGE

:START
  echo [-------------------->] Iniciando VM: %VM_NAME%
  VBoxManage startvm "%VM_NAME%" --type headless
  GOTO END


:STOP
  echo [-------------------->] Apagando VM: %VM_NAME%
  VBoxManage controlvm "%VM_NAME%" acpipowerbutton
  GOTO END

:PAUSE
  echo [-------------------->] Pausando VM: %VM_NAME%
  VBoxManage controlvm "%VM_NAME%" pause
  GOTO END

:RESUME
  echo [-------------------->] Reanudando VM: %VM_NAME%
  VBoxManage controlvm "%VM_NAME%" resume
  GOTO END

:STATUS
  echo [-------------------->] Estado de VMs:
  VBoxManage list runningvms
  VBoxManage showvminfo "%VM_NAME%" --machinereadable | findstr VMState
  GOTO END

:SNAPSHOT
  echo [-------------------->] Creando snapshot de: %VM_NAME%
  VBoxManage snapshot "%VM_NAME%" take "snap-%DATE%"
  GOTO END

:USAGE
  echo Uso: control_vm.bat [start^|stop^|pause^|resume^|status^|snapshot] [nombre_vm]

:END
  echo [-------------------->] Operacion completada