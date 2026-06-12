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

snapshot)
    # Toma el snapshot 'limpio' (estado base sin malware). Hazlo UNA vez tras
    # provisionar la VM y antes de detonar la primera muestra. Pasa --recrear
    # para reemplazar uno previo.
    echo "Tomando snapshot limpio de la maquina virtual..."
    python3 "$(dirname "$0")/../analizador/snapshot.py" crear "$VM_NAME" "${3:-}"
;;

restaurar)
    # Devuelve la VM al snapshot 'limpio' (deshace lo que dejo una muestra).
    echo "Restaurando la maquina virtual al estado limpio..."
    python3 "$(dirname "$0")/../analizador/snapshot.py" restaurar "$VM_NAME"
;;

*)
    echo "Uso:"
    echo "bash dinamico/scripts/control_maquina_virtual.sh start     kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh stop      kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh suspend   kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh resume    kali"
    echo "bash dinamico/scripts/control_maquina_virtual.sh snapshot  kali [--recrear]"
    echo "bash dinamico/scripts/control_maquina_virtual.sh restaurar kali"
;;
esac