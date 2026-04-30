#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/config.json"

# ── helpers ───────────────────────────────────────────────────────────────────

ok()   { echo "[+] $*"; }
info() { echo "[*] $*"; }
warn() { echo "[!] $*"; }

check_cmd() {
    if command -v "$1" &>/dev/null; then
        ok "$1 instalado"
    else
        warn "$1 no encontrado — $2"
        return 1
    fi
}

# ── dependencias ──────────────────────────────────────────────────────────────

echo "================================================="
echo "  Malware Lab — Setup"
echo "================================================="
echo ""
echo "-- Verificando dependencias --"
check_cmd python3  "instala Python 3"
check_cmd docker   "https://docs.docker.com/engine/install/"
check_cmd jq       "sudo apt install jq"
echo ""

# ── config.json ───────────────────────────────────────────────────────────────

echo "-- Configuración --"
if [ ! -f "$CONFIG" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG"
    ok "config.json creado desde config.example.json"
    warn "Edita config.json con tus valores antes de continuar (usuario, etc.)"
    echo ""
    read -rp "¿Abrir config.json ahora? [S/n]: " resp
    [[ "$resp" =~ ^[Ss]$|^$ ]] && "${EDITOR:-nano}" "$CONFIG"
else
    ok "config.json ya existe"
fi
echo ""

# ── llaves SSH ────────────────────────────────────────────────────────────────

echo "-- Llaves SSH --"
if [ ! -f "$HOME/.ssh/id_rsa" ]; then
    info "Generando par de llaves RSA..."
    mkdir -p "$HOME/.ssh"
    ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/id_rsa" -N ""
    ok "Llave generada en ~/.ssh/id_rsa"
else
    ok "Llave SSH ya existe en ~/.ssh/id_rsa"
fi
echo ""

# ── Python deps ───────────────────────────────────────────────────────────────

echo "-- Dependencias Python --"
if python3 -c "import paramiko" &>/dev/null; then
    ok "paramiko ya instalado"
else
    pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet --break-system-packages
    ok "Dependencias instaladas"
fi
echo ""

# ── Docker (análisis estático) ────────────────────────────────────────────────

echo "-- Docker / Debian (análisis estático) --"
CONTAINER=$(jq -r '.docker.container' "$CONFIG")
PORT=$(jq -r '.docker.port'           "$CONFIG")
USER=$(jq -r '.docker.user'           "$CONFIG")

info "Construyendo imagen Docker..."
docker build -t malware-debian "$SCRIPT_DIR/docker" -q
ok "Imagen malware-debian lista"

if ! docker inspect "$CONTAINER" &>/dev/null 2>&1; then
    docker run -d --name "$CONTAINER" -p "$PORT:22" --restart always malware-debian
    ok "Contenedor '$CONTAINER' creado"
    sleep 2

    # Crear usuario en el contenedor (solo si no es root)
    if [ "$USER" != "root" ]; then
        docker exec "$CONTAINER" useradd -m -s /bin/bash "$USER" 2>/dev/null || true
        SSH_HOME="/home/$USER"
    else
        SSH_HOME="/root"
    fi

    # Copiar llave pública
    docker exec -i "$CONTAINER" bash -c \
        "mkdir -p $SSH_HOME/.ssh && \
         cat >> $SSH_HOME/.ssh/authorized_keys && \
         chown -R $USER:$USER $SSH_HOME/.ssh && \
         chmod 700 $SSH_HOME/.ssh && \
         chmod 600 $SSH_HOME/.ssh/authorized_keys" \
        < "$HOME/.ssh/id_rsa.pub"
    ok "Llave SSH copiada al contenedor"
else
    ok "Contenedor '$CONTAINER' ya existe"
fi
echo ""

# ── Kali Linux (análisis dinámico) ────────────────────────────────────────────

echo "-- Kali Linux (análisis dinámico) --"
echo ""
echo "  Elige cómo configurar tu VM Kali:"
echo "  1) Vagrant (automático, recomendado para instalación nueva)"
echo "  2) VirtualBox manual — importar .ova"
echo "  3) VM ya existente — solo configurar SSH"
echo "  4) Saltar"
echo ""
read -rp "Opción [1-4]: " opcion

case "$opcion" in
1)
    if ! command -v vagrant &>/dev/null; then
        warn "Vagrant no instalado. Descárgalo en: https://www.vagrantup.com/downloads"
        exit 1
    fi
    info "Levantando VM Kali con Vagrant (puede tardar varios minutos)..."
    cd "$SCRIPT_DIR"
    vagrant up
    ok "VM Kali lista"
    ;;
2)
    echo ""
    echo "  Pasos para importar el .ova:"
    echo "  1. VirtualBox → Archivo → Importar servicio virtualizado → selecciona el .ova"
    echo "  2. Configuración → Red → Adaptador 1 → Reenvío de puertos:"
    echo "     Nombre: SSH | TCP | Puerto anfitrión: 2222 | Puerto invitado: 22"
    echo "  3. Inicia la VM"
    echo ""
    read -rp "¿Copiar llave SSH a la VM ahora? [S/n]: " resp
    if [[ "$resp" =~ ^[Ss]$|^$ ]]; then
        KALI_HOST=$(jq -r '.kali.host' "$CONFIG")
        KALI_PORT=$(jq -r '.kali.port' "$CONFIG")
        KALI_USER=$(jq -r '.kali.user' "$CONFIG")
        info "Copiando llave SSH a $KALI_USER@$KALI_HOST:$KALI_PORT..."
        sshpass -p kali ssh-copy-id -i "$HOME/.ssh/id_rsa.pub" \
            -p "$KALI_PORT" -o StrictHostKeyChecking=no "$KALI_USER@$KALI_HOST"
        ok "Llave copiada"
    fi
    ;;
3)
    KALI_HOST=$(jq -r '.kali.host' "$CONFIG")
    KALI_PORT=$(jq -r '.kali.port' "$CONFIG")
    KALI_USER=$(jq -r '.kali.user' "$CONFIG")
    info "Asegúrate de que la VM tenga reenvío de puertos: host $KALI_PORT → guest 22"
    info "Copiando llave SSH a $KALI_USER@$KALI_HOST:$KALI_PORT..."
    sshpass -p kali ssh-copy-id -i "$HOME/.ssh/id_rsa.pub" \
        -p "$KALI_PORT" -o StrictHostKeyChecking=no "$KALI_USER@$KALI_HOST" || \
        warn "No se pudo copiar la llave. Hazlo manualmente cuando la VM esté encendida."
    ;;
4)
    info "Setup de Kali omitido"
    ;;
esac

# ── resumen ───────────────────────────────────────────────────────────────────

echo ""
echo "================================================="
echo "  Setup completo"
echo "================================================="
echo ""
echo "Comandos disponibles:"
echo "  python3 lab.py docker status"
echo "  python3 lab.py docker start"
echo "  python3 lab.py kali start"
echo "  python3 lab.py static hash /ruta/muestra.exe"
echo ""
echo "Conectar manualmente:"
echo "  bash docker/debian.sh    # shell en contenedor Debian"
echo "  bash kali/kali.sh        # shell en Kali"
