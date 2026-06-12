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

# --- IPv6: misma política (defensa en profundidad) ---------------------------
# La VM emite IPv6 link-local; aunque no hay ruta IPv6 a internet (ningún router
# le contesta), cerramos VM→host por IPv6 igual que en IPv4 para no dejar un canal
# sin filtrar. Best-effort: si el host no tiene ip6tables, se avisa y se sigue.
if command -v ip6tables >/dev/null 2>&1; then
    _del6() { while sudo ip6tables -C "$@" 2>/dev/null; do sudo ip6tables -D "$@"; done; }
    INPUT6_EST=(INPUT  -i "$IFACE" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT)
    INPUT6_DROP=(INPUT -i "$IFACE" -j DROP)
    FWD6_DROP=(FORWARD -i "$IFACE" -j DROP)
    for rule in INPUT6_EST INPUT6_DROP FWD6_DROP; do
        eval "_del6 \"\${$rule[@]}\""
    done
    sudo ip6tables -A "${INPUT6_EST[@]}"   # respuestas a sesiones del host (si las hubiera)
    sudo ip6tables -A "${INPUT6_DROP[@]}"  # descartar lo que la VM inicie hacia el host
    sudo ip6tables -A "${FWD6_DROP[@]}"    # no enrutar tráfico IPv6 de la VM
    echo "[+] IPv6 también aislado en $IFACE:"
    sudo ip6tables -S INPUT   | grep -- "-i $IFACE" || true
    sudo ip6tables -S FORWARD | grep -- "-i $IFACE" || true
else
    echo "[!] ip6tables no disponible; IPv6 sin reglas (de todos modos no hay ruta IPv6 a internet)."
fi
