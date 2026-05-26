#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY_DIR="$SCRIPT_DIR/lab_keys"
ENV_FILE="$SCRIPT_DIR/.env"
LAB_STARTED=false
KALI_STARTED=false

ok()   { echo "[+] $*"; }
info() { echo "[*] $*"; }
warn() { echo "[!] $*"; }

cleanup() {
    echo ""
    info "Apagando el lab..."
    cd "$SCRIPT_DIR"
    $KALI_STARTED && vagrant halt 2>/dev/null || true
    docker compose down
    exit 0
}
trap cleanup INT TERM


echo "  Malware Lab — Setup"

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

# ── Kali (opcional) ──────────────────────────────────────────────────────────

echo "-- Kali Linux (análisis dinámico, opcional) --"
echo "  La VM Kali queda fuera de Docker (necesita kernel propio)."
echo ""
read -rp "¿Configurar Kali ahora con Vagrant? [s/N]: " resp
if [[ "$resp" =~ ^[Ss]$ ]]; then
    if command -v vagrant &>/dev/null; then
        vagrant up
        KALI_STARTED=true
        info "Copia la llave del lab: ssh-copy-id -i lab_keys/id_rsa.pub -p 2222 kali@127.0.0.1"
    else
        warn "Vagrant no instalado: https://www.vagrantup.com/downloads"
    fi
else
    info "Saltado. Para configurar luego: vagrant up"
fi
echo ""

# ── resumen ───────────────────────────────────────────────────────────────────

WEB_PORT=$(grep ^WEB_PORT "$ENV_FILE" | cut -d= -f2)
echo "================================================="
echo "  Setup completo"
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
echo "  Ctrl+C para apagar y destruir los contenedores."
echo "================================================="
echo ""

# Mantiene el script vivo; el trap de arriba hace el cleanup al salir.
while true; do sleep 60; done
