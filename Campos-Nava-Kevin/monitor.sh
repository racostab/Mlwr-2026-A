#!/usr/bin/env bash
# monitor.sh — Abre TODOS los monitores del host en una sesión tmux (paneles).
#
# Vigila, durante una detonación de malware real, que NO se escape nada:
#   - FUGA uplink  (debe quedar VACÍO)        - lo que la VM EMITE (intentos ok)
#   - firewall DROP (contadores suben)        - procesos del host (nada nuevo)
#   - conexiones salientes del host (limpio)
#
# Pide sudo UNA vez (tcpdump corre en background y los paneles hacen `tail`).
# Al salir de tmux (Ctrl-b luego :kill-session, o cierra los paneles) limpia todo.
#
# Uso:  bash monitor.sh        (lánzalo ANTES de detonar; déjalo abierto)
set -u

VM_IP="${VM_IP:-192.168.56.10}"
HOSTONLY="${HOSTONLY:-vboxnet0}"
UPLINK="${UPLINK:-$(ip route get 8.8.8.8 2>/dev/null | sed -n 's/.* dev \([^ ]*\).*/\1/p' | head -1)}"
# Respaldo: si la ruta a 8.8.8.8 falla (Wi-Fi caído un instante), usa la ruta por defecto.
[ -n "$UPLINK" ] || UPLINK="$(ip route show default 2>/dev/null | sed -n 's/.* dev \([^ ]*\).*/\1/p' | head -1)"
SESSION="monitor_lab"
LOGDIR="$(mktemp -d /tmp/mon_lab.XXXX)"

command -v tmux    >/dev/null || { echo "[!] Falta tmux:    sudo apt install tmux";          exit 1; }
command -v tcpdump >/dev/null || { echo "[!] Falta tcpdump: sudo apt install tcpdump";        exit 1; }
[ -n "$UPLINK" ] || { echo "[!] No detecté el uplink; exporta UPLINK=<iface> y reintenta."; exit 1; }

echo "[*] uplink=$UPLINK  VM=$VM_IP  host-only=$HOSTONLY"
echo "[*] Pide sudo una vez (para tcpdump)..."
sudo -v || exit 1
# mantener vivo el timestamp de sudo mientras dure el script
( while true; do sudo -n true 2>/dev/null; sleep 50; done ) &
SUDO_KEEP=$!

# --- capturas en background (sudo, -l = línea a línea para que tail las vea) ---
sudo tcpdump -ni "$UPLINK" -l "host $VM_IP"  > "$LOGDIR/uplink.log" 2>&1 &
sudo tcpdump -ni "$HOSTONLY" -l 'not arp and not (udp port 67 or udp port 68) and not port 22' \
                                              > "$LOGDIR/vbox.log"   2>&1 &

cleanup() {
    tmux kill-session -t "$SESSION" 2>/dev/null
    kill "$SUDO_KEEP" 2>/dev/null
    sudo pkill -f "tcpdump -ni $UPLINK"   2>/dev/null
    sudo pkill -f "tcpdump -ni $HOSTONLY" 2>/dev/null
    rm -rf "$LOGDIR"
    echo "[+] Monitores cerrados y limpiados."
}
trap cleanup EXIT

# --- panel = comando con cabecera ---
P_UPLINK="echo '== FUGA UPLINK ($UPLINK -> debe quedar VACIO) =='; tail -f '$LOGDIR/uplink.log'"
P_VBOX="echo '== VM EMITE ($HOSTONLY -> intentos sin respuesta = OK) =='; tail -f '$LOGDIR/vbox.log'"
P_FW="watch -n1 \"echo '== FIREWALL (DROP -i $HOSTONLY debe SUBIR) =='; sudo iptables -L -vn | grep -iE 'chain (INPUT|FORWARD)|$HOSTONLY'\""
P_PS="watch -n2 \"echo '== PROCESOS HOST (solo VBoxHeadless/ssh; NADA nuevo) =='; ps -eo pid,ppid,user,%cpu,%mem,comm --sort=-%cpu | head -15\""
P_SS="watch -n2 \"echo '== CONEXIONES SALIENTES HOST (sin nada externo nuevo) =='; ss -tunp state established | grep -vE '127.0.0.1|::1|:22 '\""

# --- montar la sesión tmux (5 paneles en mosaico) ---
tmux new-session  -d -s "$SESSION" -n monitores "$P_UPLINK"
tmux split-window -t "$SESSION" "$P_VBOX"
tmux split-window -t "$SESSION" "$P_FW"
tmux split-window -t "$SESSION" "$P_PS"
tmux split-window -t "$SESSION" "$P_SS"
tmux select-layout -t "$SESSION" tiled
tmux set-option -t "$SESSION" mouse on

echo "[*] Abriendo tmux. Para SALIR y limpiar: Ctrl-b y luego :kill-session  (o cierra la ventana)."
tmux attach -t "$SESSION"
