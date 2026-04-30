#!/usr/bin/env python3
"""
vm.py --> API Python para control de VirtualBox
Uso: python vm.py [accion] [nombre_vm]
     python vm.py list
     python vm.py start nombre_vm
     python vm.py stop  nombre_vm
     
"""
import subprocess
import sys
import json
import re

VBOXMANAGE = r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'

def vbox(args: list) -> tuple:
    result = subprocess.run(
        [VBOXMANAGE] + args,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def listar_vms() -> list:
    _, out, _ = vbox(['list', 'vms'])
    return re.findall(r'"(.+?)"', out)


def estado_vm(nombre: str) -> str:
    _, out, _ = vbox(['showvminfo', nombre, '--machinereadable'])
    for line in out.splitlines():
        if line.startswith('VMState='):
            return line.split('=')[1].strip('"')
    return 'desconocido'

def iniciar_vm(nombre: str, modo: str = 'headless') -> bool:
    rc, out, err = vbox(['startvm', nombre, '--type', modo])
    if rc == 0:
        print(f'[-------------------->] VM "{nombre}" iniciada en modo {modo}')
        return True
    print(f'[-------------------->] Error: {err}')
    return False

def apagar_vm(nombre: str, forzar: bool = False) -> bool:
    cmd = 'poweroff' if forzar else 'acpipowerbutton'
    rc, _, err = vbox(['controlvm', nombre, cmd])
    if rc == 0:
        print(f'[-------------------->] VM "{nombre}" apagada')
        return True
    print(f'[-------------------->] Error: {err}')
    return False

def pausar_vm(nombre: str) -> bool:
    rc, _, _ = vbox(['controlvm', nombre, 'pause'])
    return rc == 0

def reanudar_vm(nombre: str) -> bool:
    rc, _, _ = vbox(['controlvm', nombre, 'resume'])
    return rc == 0

def crear_snapshot(nombre: str, snap_nombre: str) -> bool:
    rc, _, err = vbox(['snapshot', nombre, 'take', snap_nombre])
    if rc == 0:
        print(f'[-------------------->] Snapshot "{snap_nombre}" creado')
        return True
    print(f'[-------------------->] Error: {err}')
    return False

"Glosario de Acciones y su respectiva funcion "
if __name__ == '__main__':
    ACCIONES = {
        'list':     lambda: print(json.dumps(listar_vms(), indent=2)),
        'status':   lambda: print(f'Estado: {estado_vm(sys.argv[2])}'),
        'start':    lambda: iniciar_vm(sys.argv[2]),
        'stop':     lambda: apagar_vm(sys.argv[2]),
        'pause':    lambda: pausar_vm(sys.argv[2]),
        'resume':   lambda: reanudar_vm(sys.argv[2]),
        'snapshot': lambda: crear_snapshot(sys.argv[2], sys.argv[3]),
    }
    if len(sys.argv) < 2 or sys.argv[1] not in ACCIONES:
        print('Uso: python programa_vm.py [list|status|start|stop|pause|resume|snapshot] [vm] [snap]')
        sys.exit(1)
    ACCIONES[sys.argv[1]]()