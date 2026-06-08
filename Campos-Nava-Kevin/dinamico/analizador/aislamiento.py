"""
Une las tres capas, cada una en su módulo de una sola responsabilidad:
  - `red.py`          → red host-only sin NAT (VBoxManage)
  - `firewall.py`     → firewall del host / firewall local (iptables)
  - `verificacion.py` → gate de pre-vuelo que PRUEBA el aislamiento (nmap desde la VM a la IP del host)

Igual que en el lado estático el motor importa desde `catalogo.analizador_estatico`,
aquí el runner dinámico importa desde `aislamiento`:

    import aislamiento
    ip = aislamiento.preparar_aislada(vm)       # 1. red host-only, sin NAT
    aislamiento.aplicar_firewall()              # 2. firewall del host
    aislamiento.verificar(vm, client=cliente)   # 3. gate: lanza NoAislada si hay fuga
"""
import sys

from red import (GUEST_IP, HOST_IP, IFACE_HOSTONLY, apagar_vm, disponible,
                 preparar_aislada, vboxmanage, vm_corriendo, vm_existe)
from firewall import aplicar as aplicar_firewall
from firewall import esta_aplicado as firewall_aplicado
from verificacion import NoAislada, verificar

__all__ = [
    # capa 1 — red
    "preparar_aislada", "apagar_vm", "disponible", "vm_existe", "vm_corriendo",
    "vboxmanage", "GUEST_IP", "HOST_IP", "IFACE_HOSTONLY",
    # capa 2 — firewall del host
    "aplicar_firewall", "firewall_aplicado",
    # capa 3 — verificación
    "verificar", "NoAislada",
]


if __name__ == "__main__":
    vm = sys.argv[1] if len(sys.argv) > 1 else "kali-malware-lab"
    ip = preparar_aislada(vm)   # capa 1: red host-only + sin NAT + arranque
    aplicar_firewall()          # capa 2: corta lo que la VM inicie hacia el host
    print(ip)                   # única línea en stdout (la IP)
