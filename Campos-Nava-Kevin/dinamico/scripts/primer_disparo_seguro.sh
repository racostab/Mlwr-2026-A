#!/usr/bin/env bash
# primer_disparo_seguro.sh — Lanza UNA detonación con un "tripwire" de fuga en vivo.
#
# Qué hace (en el HOST):
#   1. Levanta un tcpdump en el uplink real, filtrado a la IP de la VM: si ahí
#      aparece UN solo paquete durante la corrida => posible FUGA.
#   2. Encola la muestra en el servicio dinámico (:8002), que ya restaura el
#      snapshot limpio, aísla, verifica y detona.
#   3. Al terminar, para el tripwire y dice cuántos paquetes capturó:
#        0  => no escapó nada (OK)
#       >0  => REVISA: algo de la VM salió por el uplink.
#
# IMPORTANTE: este script NO sabe si la muestra es benigna o malware real;
# ejecuta EL ARCHIVO QUE LE PASES. Haz primero el ensayo en seco con un señuelo.
#
# Uso:
#   bash dinamico/scripts/primer_disparo_seguro.sh [ruta_muestra] [segundos]
#   # sin args  -> ENSAYO BENIGNO con dataset/muestras_prueba/senuelo_red 20s
#   # con args  -> lo que tú indiques (aquí es donde pondrías el malware real)
set -euo pipefail
cd "$(dirname "$0")/../.."   # raíz del repo

MUESTRA="${1:-dataset/muestras_prueba/senuelo_red}"
SEGUNDOS="${2:-20}"
SERVICIO="${DYNAMIC_URL:-http://localhost:8002}"

[ -f "$MUESTRA" ] || { echo "[!] No existe la muestra: $MUESTRA"; exit 1; }

# Datos de red (auto-detectados; sobreescribibles por entorno).
UPLINK="${UPLINK:-$(ip route get 8.8.8.8 2>/dev/null | sed -n 's/.* dev \([^ ]*\).*/\1/p' | head -1)}"
VM_IP="${VM_IP:-$(python3 -c 'from compartido.configuracion import kali; print(kali()["host"])' 2>/dev/null || echo 192.168.56.10)}"

# Aviso si la muestra NO es un señuelo conocido (probable malware real).
case "$MUESTRA" in
  *muestras_prueba/senuelo_*) TIPO="ENSAYO BENIGNO (señuelo)";;
  *) TIPO="*** NO es un señuelo conocido: trátalo como MALWARE REAL ***";;
esac

cat <<EOF
──────────────────────────────────────────────
 Muestra : $MUESTRA
 Tipo    : $TIPO
 Tiempo  : ${SEGUNDOS}s
 Tripwire: uplink=$UPLINK  vigilando IP VM=$VM_IP
 Servicio: $SERVICIO
──────────────────────────────────────────────
EOF
read -r -p "¿Continuar? [y/N] " ok; [ "$ok" = "y" ] || { echo "Cancelado."; exit 0; }

# 1) Tripwire: captura en el uplink cualquier paquete de/para la VM.
PCAP="$(mktemp /tmp/tripwire_XXXX.pcap)"
echo "[*] Tripwire ON (sudo tcpdump en $UPLINK)…"
sudo tcpdump -ni "$UPLINK" -w "$PCAP" "host $VM_IP" >/dev/null 2>&1 &
TCPDUMP_PID=$!
sleep 1

# 2) Encolar la detonación y seguir el job hasta que termine.
echo "[*] Encolando en $SERVICIO …"
JID=$(curl -s -F "file=@${MUESTRA}" -F "segundos=${SEGUNDOS}" "$SERVICIO/analisis" \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "[*] job=$JID — esperando (estado: en_cola→ejecutando→…→listo)…"
while :; do
  EST=$(curl -s "$SERVICIO/analisis/$JID" | python3 -c 'import sys,json;print(json.load(sys.stdin)["estado"])')
  echo "    estado=$EST"
  [ "$EST" = "listo" ] || [ "$EST" = "error" ] && break
  sleep 3
done

# 3) Parar el tripwire y contar.
sudo kill "$TCPDUMP_PID" 2>/dev/null || true
sleep 1
FUGAS=$(sudo tcpdump -nr "$PCAP" 2>/dev/null | wc -l)
sudo rm -f "$PCAP"

echo "──────────────────────────────────────────────"
echo " job=$JID  estado=$EST"
if [ "$FUGAS" -eq 0 ]; then
  echo " TRIPWIRE: 0 paquetes en el uplink  ✅  (nada escapó)"
else
  echo " TRIPWIRE: $FUGAS paquete(s) en el uplink  ❌  POSIBLE FUGA — REVISA antes de seguir"
fi
echo " Resultados del job: $SERVICIO/analisis/$JID"
echo "──────────────────────────────────────────────"
[ "$EST" = "listo" ] && [ "$FUGAS" -eq 0 ]
