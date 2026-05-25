#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_DIR="$SCRIPT_DIR/lab_keys"
ENV_FILE="$SCRIPT_DIR/.env"
LAB_STARTED=false
VM_STARTED=false

# Nombre de la VM Debian (lo lee de config.json si jq está disponible)
VM_NAME="debian"
if command -v jq >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/config.json" ]; then
    VM_NAME=$(jq -r '.vbox.vm_name // "debian"' "$SCRIPT_DIR/config.json")
fi

ok()   { echo "[+] $*"; }
info() { echo "[*] $*"; }
warn() { echo "[!] $*"; }

cleanup() {
    echo ""
    info "Apagando el lab..."
    cd "$SCRIPT_DIR"
    $VM_STARTED && bash "$SCRIPT_DIR/vbox/cli.sh" stop "$VM_NAME" >/dev/null 2>&1 || true
    docker compose down
    exit 0
}
trap cleanup INT TERM

echo "================================================="
echo "  Malware Lab — Setup"
echo "================================================="
echo ""

# ── dependencias ──────────────────────────────────────────────────────────────

echo "-- Verificando dependencias --"
command -v docker  >/dev/null || { warn "Docker no instalado: https://docs.docker.com/engine/install/"; exit 1; }
docker compose version >/dev/null 2>&1 || { warn "Docker Compose v2 requerido"; exit 1; }
command -v ssh-keygen >/dev/null || { warn "ssh-keygen no encontrado"; exit 1; }
ok "docker / docker compose / ssh-keygen"
echo ""

# ── llaves SSH del lab (NO las del usuario) ──────────────────────────────────

echo "-- Llaves SSH del lab --"
mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"
if [ ! -f "$KEY_DIR/id_rsa" ]; then
    ssh-keygen -t rsa -b 4096 -f "$KEY_DIR/id_rsa" -N "" -C "malware-lab" -q
    ok "Llaves generadas en lab_keys/"
else
    ok "Llaves ya existen en lab_keys/"
fi
chmod 600 "$KEY_DIR/id_rsa"
chmod 644 "$KEY_DIR/id_rsa.pub"
echo ""

# ── .env ──────────────────────────────────────────────────────────────────────

if [ ! -f "$ENV_FILE" ]; then
    cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
    ok ".env creado desde .env.example"
else
    ok ".env ya existe"
fi
echo ""

# ── compose ───────────────────────────────────────────────────────────────────

echo "-- Levantando contenedores (build + up) --"
cd "$SCRIPT_DIR"
docker compose up -d --build
echo ""
docker compose ps
echo ""
LAB_STARTED=true

# ── VM Debian (opcional) ──────────────────────────────────────────────────────────

echo "-- VM Debian (análisis dinámico, opcional) --"
echo "  La VM Debian queda fuera de Docker (necesita kernel propio)."
echo ""
read -rp "¿Encender ahora tu VM Debian de VirtualBox ('$VM_NAME')? [s/N]: " resp
if [[ "$resp" =~ ^[Ss]$ ]]; then
    if command -v VBoxManage &>/dev/null; then
        if bash "$SCRIPT_DIR/vbox/cli.sh" start "$VM_NAME"; then
            VM_STARTED=true
            info "Shell de la VM:  bash vbox/vbox.sh"
        else
            warn "No se pudo iniciar '$VM_NAME' (¿ya encendida? ¿nombre correcto en config.json?)"
        fi
    else
        warn "VirtualBox (VBoxManage) no encontrado: https://www.virtualbox.org/"
    fi
else
    info "Saltado. Para encenderla luego: bash vbox/cli.sh start $VM_NAME"
fi
echo ""

# ── resumen ───────────────────────────────────────────────────────────────────

WEB_PORT=$(grep ^WEB_PORT "$ENV_FILE" | cut -d= -f2)
echo "================================================="
echo "  Setup completo"
echo "================================================="
echo ""
echo "  Web    → http://localhost:${WEB_PORT:-8000}"
echo "  Engine → http://localhost:8001 (API)"
echo ""
echo "CLI:"
echo "  python3 lab.py analyze /ruta/muestra"
echo "  python3 lab.py list"
echo ""
echo "Útil:"
echo "  docker compose logs -f engine"
echo ""
echo "  Ctrl+C para apagar el lab (contenedores y, si la encendiste, la VM Debian)."
echo "================================================="
echo ""

# Mantiene el script vivo; el trap de arriba hace el cleanup al salir.
while true; do sleep 60; done
