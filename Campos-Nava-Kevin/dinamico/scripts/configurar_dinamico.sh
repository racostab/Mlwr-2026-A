#!/bin/bash
# Configura y AÍSLA todo el análisis dinámico (VM Kali) en un solo paso.
#
# Es el módulo que reúne el ciclo completo del dinámico, para que `setup.sh` no
# tenga que conocer los detalles: solo lo invoca. También sirve para (re)preparar
# el lab dinámico por separado, sin volver a correr todo el setup:
#
#     bash dinamico/scripts/configurar_dinamico.sh
#
# Hace, en orden:
#   1. Comprueba sus condiciones: VirtualBox, Vagrant y config.json (los instala
#      / crea setup.sh; aquí solo se verifican y se avisa con claridad si faltan).
#   2. vagrant up   → crea/provisiona la VM (con NAT, para clonar la box e
#      instalar herramientas; TODAVÍA sin malware).
#   3. vagrant halt → la apaga (el NAT no se puede quitar en caliente).
#   4. aislamiento.py (fachada) → quita el NAT (host-only, sin internet), arranca
#      la VM headless y aplica el firewall del host (firewall local).
#   5. verificacion.py → GATE DURO: prueba que la jaula esté cerrada (NAT off,
#      host-only, firewall confirmado, internet inalcanzable). Si algo falla, sale
#      con error y NO deja el lab marcado como listo.
set -euo pipefail

# Raíz del repo (este script vive en dinamico/scripts/).
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
VM_DIR="$RAIZ/dinamico/maquina_virtual"
CONFIG="$RAIZ/config.json"

ok()   { echo "[+] $*"; }
info() { echo "[*] $*"; }
err()  { echo "[!] $*" >&2; }

# ── 1. Condiciones para que el dinámico esté listo ───────────────────────────
command -v VBoxManage >/dev/null 2>&1 || { err "VirtualBox no instalado (corre setup.sh o instala VirtualBox)."; exit 1; }
command -v vagrant    >/dev/null 2>&1 || { err "Vagrant no instalado (corre setup.sh o instala Vagrant)."; exit 1; }
[ -f "$CONFIG" ] || { err "Falta config.json (copia config.example.json y edítalo, o corre setup.sh)."; exit 1; }

VM_NAME="$(python3 -c "import json;print(json.load(open('$CONFIG'))['kali']['vm_name'])" 2>/dev/null || echo kali-malware-lab)"

# ── 2. Crear/provisionar la VM (con NAT, sin malware aún) ─────────────────────
info "Creando/provisionando la VM '$VM_NAME' (vagrant up; la 1ª vez tarda)..."
(cd "$VM_DIR" && vagrant up)

# ── 3. Apagar para poder quitar el NAT (no se puede en caliente) ─────────────
info "Apagando la VM para reconfigurar la red..."
(cd "$VM_DIR" && vagrant halt) || true

# ── 4. Aislar: host-only sin NAT + arranque headless + firewall del host ─────
# La fachada imprime SOLO la IP por stdout (su log va a stderr).
info "Aislando la VM (host-only, sin internet) y aplicando el firewall del host..."
IP_VM="$(python3 "$RAIZ/dinamico/analizador/aislamiento.py" "$VM_NAME")"
ok "VM aislada y encendida en $IP_VM (sin NAT)"

# ── 5. Gate duro: PROBAR la jaula antes de declarar el lab listo ─────────────
info "Verificando el aislamiento (gate de seguridad)..."
if python3 "$RAIZ/dinamico/analizador/verificacion.py" "$VM_NAME"; then
    ok  "Jaula cerrada y verificada: el lab dinámico está LISTO."
    info "SSH a la VM:  bash dinamico/scripts/ssh_maquina_virtual.sh"
    info "Detonar:      python3 dinamico/analizador/analizador_dinamico.py <muestra> 20"
else
    err "El aislamiento NO se pudo confirmar; el lab dinámico NO está listo."
    err "Revisa la salida de arriba; NO detones muestras hasta resolverlo."
    exit 1
fi
