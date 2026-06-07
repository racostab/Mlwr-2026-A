"""API de Oracle VirtualBox (VBoxManage) para dejar la VM Kali AISLADA.

`VBoxManage` es la CLI oficial de gestión de VirtualBox (la misma API que la GUI).

Idea del aislamiento (dos capas):
  1. Red **host-only** `vboxnet0` (host = 192.168.56.1): la VM tiene IP fija
     192.168.56.10 (la fija el Vagrantfile como `private_network`) y solo ve al
     host por esa red privada.
  2. Se **desconecta el NAT** de la VM (adaptador 1, modo `null`) tras provisionar,
     así la VM se queda sin salida a internet pero conserva su IP host-only fija.
     El firewall del host
     (`dinamico/reglas_firewall/aislar_host.sh`) corta además lo que la VM
     intente INICIAR hacia el host; solo deja pasar las respuestas a las sesiones
     que abre el host (SSH/SFTP).

Flujo completo:  vagrant up (provisiona por NAT)  →  preparar_aislada()  →  la VM
queda solo en host-only, sin internet, lista para el análisis dinámico.

    python3 dinamico/scripts/red_aislada.py [nombre_vm]   # aísla y arranca; imprime la IP
"""
import subprocess
import sys
from pathlib import Path
from shutil import which

IFACE_HOSTONLY = "vboxnet0"
HOST_IP        = "192.168.56.1"      # el host en la red host-only
GUEST_IP       = "192.168.56.10"     # la VM (fijada por el Vagrantfile)
NETMASK        = "255.255.255.0"


class VBoxNoDisponible(RuntimeError):
    """VBoxManage no está instalado en este host."""


def disponible() -> bool:
    return which("VBoxManage") is not None


def vboxmanage(*args: str) -> str:
    """Ejecuta `VBoxManage <args>` y devuelve stdout (lanza si falla)."""
    if not disponible():
        raise VBoxNoDisponible("VBoxManage no está instalado (instala VirtualBox)")
    r = subprocess.run(["VBoxManage", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"VBoxManage {' '.join(args)} → {r.stderr.strip()}")
    return r.stdout


def vm_existe(nombre: str) -> bool:
    return f'"{nombre}"' in vboxmanage("list", "vms")


def vm_corriendo(nombre: str) -> bool:
    return f'"{nombre}"' in vboxmanage("list", "runningvms")


def asegurar_interfaz_hostonly() -> str:
    """Garantiza la interfaz host-only `vboxnet0` con IP fija; devuelve la IP del host."""
    if IFACE_HOSTONLY not in vboxmanage("list", "hostonlyifs"):
        # En un sistema limpio, `create` da de alta vboxnet0 (el primero libre).
        vboxmanage("hostonlyif", "create")
    vboxmanage("hostonlyif", "ipconfig", IFACE_HOSTONLY,
               "--ip", HOST_IP, "--netmask", NETMASK)
    return HOST_IP


def aislar(nombre: str) -> None:
    """Desconecta el NAT (adaptador 1) dejando la VM sin internet.

    Usa `null` (adaptador presente pero SIN conexión), no `none` (lo quitaría):
    con `null` se conserva el orden de adaptadores, así la red host-only sigue
    siendo `eth1` con su IP fija 192.168.56.10. Con `none` la interfaz se
    renombraba a `eth0`, perdía la IP estática y caía a DHCP (.101).

    Solo puede hacerse con la VM apagada.
    """
    if vm_corriendo(nombre):
        return  # no se puede reconfigurar en caliente; se asume ya aislada
    vboxmanage("modifyvm", nombre, "--nic1", "null")  # NAT desconectado → sin internet


def iniciar_vm(nombre: str) -> None:
    if not vm_corriendo(nombre):
        vboxmanage("startvm", nombre, "--type", "headless")


def apagar_vm(nombre: str) -> None:
    if vm_corriendo(nombre):
        vboxmanage("controlvm", nombre, "poweroff")


def preparar_aislada(nombre: str) -> str:
    """Deja la VM corriendo en la red aislada y devuelve su IP (192.168.56.10).

    Si está apagada: asegura la interfaz host-only, le quita el NAT y la arranca.
    Si ya corre, se asume que está aislada (no se reconfigura en caliente).
    """
    if not vm_existe(nombre):
        raise RuntimeError(
            f"La VM '{nombre}' no existe. Créala primero con vagrant "
            "(setup.sh la provisiona si dices que sí, o `vagrant up` en "
            "dinamico/maquina_virtual)."
        )
    asegurar_interfaz_hostonly()
    if not vm_corriendo(nombre):
        aislar(nombre)
        iniciar_vm(nombre)
    return GUEST_IP


def aplicar_firewall() -> bool:
    """Aplica el firewall de aislamiento (reglas_firewall/aislar_host.sh). Pide sudo.

    La salida del script va a stderr para que el stdout solo lleve la IP (lo que
    captura setup.sh).
    """
    script = Path(__file__).resolve().parent.parent / "reglas_firewall" / "aislar_host.sh"
    if not script.exists():
        return False
    return subprocess.run(["bash", str(script)], stdout=sys.stderr).returncode == 0


if __name__ == "__main__":
    vm = sys.argv[1] if len(sys.argv) > 1 else "kali-malware-lab"
    ip = preparar_aislada(vm)        # red host-only + sin NAT + arranque
    aplicar_firewall()               # capa 2: corta lo que la VM inicie hacia el host
    print(ip)                        # única línea en stdout (la IP)
