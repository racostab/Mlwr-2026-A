#!/bin/bash
# Captura el tráfico de la VM en su interfaz host-only para COMPROBAR que nada
# sale hacia internet mientras detonas una muestra. Detecta solo la interfaz, la
# MAC y la subred de la VM (no hay nada hardcodeado), así que el filtro siempre
# encaja aunque cambie la red.
#
# Modos:
#   fugas (por defecto)  Solo lo que la VM intenta mandar FUERA de la red del lab
#                        (IPv4 a otra subred o IPv6 global). En una jaula bien
#                        cerrada esto queda EN BLANCO: esa es la prueba.
#   todo                 TODO el tráfico de la VM, con MAC origen/destino (-e).
#                        Verás el SFTP del runner (interno, 192.168.56.x) e IPv6
#                        link-local; es ruidoso a propósito.
#
# Uso:
#   bash dinamico/scripts/capturar_red_vm.sh                 # fugas, a pantalla
#   bash dinamico/scripts/capturar_red_vm.sh todo            # todo el tráfico
#   bash dinamico/scripts/capturar_red_vm.sh fugas vm.pcap   # fugas + guardar pcap
#   VM=otra-vm bash dinamico/scripts/capturar_red_vm.sh      # otra VM
#
# Lánzalo en una terminal ANTES de detonar la muestra y córtalo con Ctrl-C al
# terminar. Necesita sudo (tcpdump abre la interfaz en modo promiscuo).
set -e

MODO="${1:-fugas}"
PCAP="${2:-}"
VM="${VM:-kali-malware-lab}"

command -v VBoxManage >/dev/null || { echo "[!] VBoxManage no está en el PATH."; exit 1; }
command -v tcpdump    >/dev/null || { echo "[!] tcpdump no instalado: sudo apt install tcpdump"; exit 1; }

# --- Descubrir la NIC host-only de la VM: índice, interfaz y MAC -------------
INFO="$(VBoxManage showvminfo "$VM" --machinereadable 2>/dev/null)" \
    || { echo "[!] No encuentro la VM '$VM'. Pásala con VM=<nombre> o como ya está creada."; exit 1; }

# Índice N donde nic<N>="hostonly".
N="$(printf '%s\n' "$INFO" | sed -n 's/^nic\([0-9]\)="hostonly"$/\1/p' | head -1)"
[ -n "$N" ] || { echo "[!] La VM '$VM' no tiene ninguna NIC en modo host-only."; exit 1; }

IFACE="$(printf '%s\n' "$INFO" | sed -n "s/^hostonlyadapter${N}=\"\(.*\)\"$/\1/p" | head -1)"
RAW_MAC="$(printf '%s\n' "$INFO" | sed -n "s/^macaddress${N}=\"\(.*\)\"$/\1/p" | head -1)"
# 0800270F85E6 -> 08:00:27:0f:85:e6
MAC="$(printf '%s' "$RAW_MAC" | sed 's/../&:/g; s/:$//' | tr 'A-Z' 'a-z')"

[ -n "$IFACE" ] && [ -n "$MAC" ] || { echo "[!] No pude leer la interfaz/MAC host-only de la VM."; exit 1; }

# --- Subred de la interfaz host-only (para excluir el tráfico interno) --------
CIDR="$(ip -o -f inet addr show "$IFACE" 2>/dev/null | awk '{print $4}' | head -1)"
if [ -z "$CIDR" ]; then
    echo "[!] La interfaz $IFACE no tiene IPv4 (¿la VM está apagada?)."
    echo "    Arranca la VM (o lanza el runner) y reintenta; la interfaz se activa al bootear."
    exit 1
fi
SUBNET="$(python3 -c 'import ipaddress,sys; print(ipaddress.ip_interface(sys.argv[1]).network)' "$CIDR")"

# --- Construir filtro y lanzar tcpdump ---------------------------------------
echo "VM=$VM  interfaz=$IFACE  mac=$MAC  subred=$SUBNET  modo=$MODO"
[ -n "$PCAP" ] && echo "guardando pcap en: $PCAP"

case "$MODO" in
  fugas)
    # Solo lo que la VM ORIGINA hacia fuera de la subred del lab; se excluye IPv6
    # link-local (fe80::/10) y multicast (ff00::/8), que nunca salen del enlace.
    FILTRO="ether src $MAC and not net $SUBNET and not net fe80::/10 and not net ff00::/8"
    echo "=> Debe quedar EN BLANCO. Cualquier línea = intento de salida a internet."
    set -x
    sudo tcpdump -ni "$IFACE" ${PCAP:+-w "$PCAP"} "$FILTRO"
    ;;
  todo)
    FILTRO="ether host $MAC"
    echo "=> Todo el tráfico de la VM (incluye SFTP del runner e IPv6 link-local)."
    set -x
    sudo tcpdump -eni "$IFACE" ${PCAP:+-w "$PCAP"} "$FILTRO"
    ;;
  *)
    echo "[!] Modo desconocido: '$MODO'. Usa 'fugas' o 'todo'."; exit 1 ;;
esac
