#!/bin/bash

VM_NAME="$2"

case "$1" in
start)
    echo "Encendiendo la maquina virtual..."
    VBoxManage startvm "$VM_NAME" --type headless
;;

stop)
    echo "Apagando la maquina virtual..."
    VBoxManage controlvm "$VM_NAME" poweroff
;;

suspend)
    echo "Suspendiendo la maquina virtual..."
    VBoxManage controlvm "$VM_NAME" savestate
;;

resume)
    echo "Reanudando la maquina virtual..."
    VBoxManage startvm "$VM_NAME"
;;

*)
    echo "Uso:"
    echo "./vmcontrol.sh start  NOMBRE_VM"
    echo "./vmcontrol.sh stop   NOMBRE_VM"
    echo "./vmcontrol.sh pause NOMBRE_VM"
    echo "./vmcontrol.sh resume NOMBRE_VM"
;;
esac