#!/bin/bash
# Aísla el host de la VM en la red host-only.
#
# Uso:  bash dinamico/reglas_firewall/aislar_host.sh [interfaz] [subred]
#       (por defecto: vboxnet0  192.168.56.0/24)
set -e

IFACE="${1:-vboxnet0}"

# Borra una regla repetida hasta que no quede ninguna (idempotencia).
_del() { while sudo iptables -C "$@" 2>/dev/null; do sudo iptables -D "$@"; done; }

INPUT_EST=(INPUT  -i "$IFACE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT)
INPUT_DHCP=(INPUT -i "$IFACE" -p udp --dport 67 -j ACCEPT)
INPUT_DROP=(INPUT -i "$IFACE" -j DROP)
FWD_DROP=(FORWARD -i "$IFACE" -j DROP)

# Limpia versiones previas y reinserta en el orden correcto.
for rule in INPUT_EST INPUT_DHCP INPUT_DROP FWD_DROP; do
    eval "_del \"\${$rule[@]}\""
done
sudo iptables -A "${INPUT_EST[@]}"     # 1. dejar pasar respuestas a sesiones del host
sudo iptables -A "${INPUT_DHCP[@]}"    # 2. permitir DHCP (renovación de lease de la VM)
sudo iptables -A "${INPUT_DROP[@]}"    # 3. descartar lo demás que inicie la VM hacia el host
sudo iptables -A "${FWD_DROP[@]}"      # 4. no enrutar tráfico de la VM

echo "[+] Host aislado de la VM en $IFACE. Reglas activas:"
sudo iptables -S INPUT   | grep -- "-i $IFACE" || true
sudo iptables -S FORWARD | grep -- "-i $IFACE" || true
