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
    echo "bash dinamico/scripts/control_maquina_virtual.sh start   kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh stop    kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh suspend kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh resume  kali"
;;
esac