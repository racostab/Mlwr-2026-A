"""Snapshots de la VM Kali con VirtualBox (VBoxManage): estado LIMPIO reproducible.

Una sola responsabilidad: gestionar el *snapshot limpio* de la VM para que cada
detonación arranque desde un estado idéntico y no contaminado. Detonar un botnet
deja residuos (persistencia, cron, archivos, procesos); sin restaurar, la segunda
muestra correría sobre la basura de la primera y el strace/volcado mezclaría
comportamientos.

Flujo de uso (lo orquesta el runner `analizador_dinamico.py`):
  1. Tras provisionar la VM (una vez), se toma el snapshot `limpio`.
  2. Antes de CADA detonación se restaura `limpio` (con la VM apagada) → la VM
     vuelve al estado recién provisionado.

Las otras capas viven en sus módulos: la red en `red.py`, el firewall en
`firewall.py`, el gate en `verificacion.py`. La fachada que las une es
`aislamiento.py` (el runner importa de la fachada).

    python3 dinamico/analizador/snapshot.py crear   [nombre_vm]   # toma el snapshot 'limpio'
    python3 dinamico/analizador/snapshot.py restaurar [nombre_vm] # vuelve al 'limpio'
"""
import sys

from red import apagar_vm, vboxmanage, vm_existe

SNAPSHOT_LIMPIO = "limpio"   # nombre canónico del estado base recién provisionado


def existe(nombre: str, snap: str = SNAPSHOT_LIMPIO) -> bool:
    """True si la VM `nombre` tiene un snapshot llamado `snap`."""
    if not vm_existe(nombre):
        return False
    try:
        salida = vboxmanage("snapshot", nombre, "list", "--machinereadable")
    except RuntimeError:
        # `snapshot list` devuelve error si la VM no tiene ningún snapshot.
        return False
    return f'="{snap}"' in salida or f'SnapshotName="{snap}"' in salida


def crear(nombre: str, snap: str = SNAPSHOT_LIMPIO, recrear: bool = False) -> None:
    """Toma el snapshot `snap` de la VM (estado base limpio).

    Se hace con la VM apagada para capturar un estado en disco consistente. Si ya
    existe y no se pide `recrear`, no hace nada (idempotente). El llamador es
    responsable de que la VM esté realmente limpia (recién provisionada) en este
    momento: este módulo solo fija el punto de retorno.
    """
    if not vm_existe(nombre):
        raise RuntimeError(f"La VM '{nombre}' no existe; créala con vagrant antes.")
    if existe(nombre, snap):
        if not recrear:
            return
        vboxmanage("snapshot", nombre, "delete", snap)
    apagar_vm(nombre)  # estado en disco consistente
    vboxmanage("snapshot", nombre, "take", snap,
               "--description", "Estado base recien provisionado (sin malware)")


def restaurar(nombre: str, snap: str = SNAPSHOT_LIMPIO) -> None:
    """Restaura la VM al snapshot `snap` (la apaga primero; queda apagada).

    Tras esto el llamador debe arrancar la VM (`red.preparar_aislada`). Lanza si
    no existe el snapshot: NUNCA se debe detonar sobre un estado posiblemente sucio
    creyendo que se restauró.
    """
    if not existe(nombre, snap):
        raise RuntimeError(
            f"La VM '{nombre}' no tiene el snapshot '{snap}'. Créalo una vez con "
            f"'python3 dinamico/analizador/snapshot.py crear {nombre}' (con la VM "
            "recién provisionada y limpia)."
        )
    apagar_vm(nombre)  # no se puede restaurar en caliente
    vboxmanage("snapshot", nombre, "restore", snap)


def asegurar_limpio_y_restaurar(nombre: str, snap: str = SNAPSHOT_LIMPIO) -> bool:
    """Deja la VM en el estado base antes de detonar; devuelve si restauró.

    - Si el snapshot existe → lo restaura (True): cada muestra arranca limpia.
    - Si NO existe → lo crea desde el estado actual (asumido limpio en el primer
      uso) y devuelve False, avisando que esta corrida define la línea base.
    """
    if existe(nombre, snap):
        restaurar(nombre, snap)
        return True
    print(f"[!] La VM '{nombre}' no tenía snapshot '{snap}'. Tomo uno AHORA desde el "
          "estado actual y lo uso como línea base limpia.\n"
          "    Si la VM ya estaba sucia, recréalo: snapshot.py crear --recrear.")
    crear(nombre, snap)
    return False


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "crear"
    vm = sys.argv[2] if len(sys.argv) > 2 else "kali-malware-lab"
    if accion == "crear":
        crear(vm, recrear="--recrear" in sys.argv)
        print(f"[+] Snapshot '{SNAPSHOT_LIMPIO}' tomado de '{vm}'.")
    elif accion == "restaurar":
        restaurar(vm)
        print(f"[+] VM '{vm}' restaurada al snapshot '{SNAPSHOT_LIMPIO}' (apagada).")
    else:
        print("Uso: snapshot.py [crear|restaurar] [nombre_vm] [--recrear]")
        sys.exit(1)
