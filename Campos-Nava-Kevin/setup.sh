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
    $KALI_STARTED && (cd "$SCRIPT_DIR/dinamico/maquina_virtual" && vagrant halt) 2>/dev/null || true
    docker compose down
    exit 0
}
trap cleanup INT TERM


echo "  Malware Lab — Setup"

echo ""

# ── dependencias ──────────────────────────────────────────────────────────────

echo "-- Verificando dependencias --"

# Ejecuta un comando como root (sudo si hace falta).
as_root() {
    if command -v sudo >/dev/null; then sudo "$@"; else "$@"; fi
}

# Instala un paquete apt usando sudo si hace falta.
apt_install() {
    local pkg="$1"
    info "Instalando '$pkg'..."
    as_root apt-get update -qq && as_root apt-get install -y "$pkg"
}

# Vagrant no está en los repos de Ubuntu: se instala desde el repo APT oficial
# de HashiCorp y, si ese codename no estuviera, desde el .deb directo.
install_vagrant() {
    command -v vagrant >/dev/null && { ok "Vagrant ya instalado"; return 0; }
    warn "Vagrant no instalado, instalando desde el repo de HashiCorp..."
    local cn; cn="$(. /etc/os-release; echo "${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null)}")"

    apt_install ca-certificates >/dev/null 2>&1 || true
    as_root install -m 0755 -d /etc/apt/keyrings
    if curl -fsSL https://apt.releases.hashicorp.com/gpg \
         | as_root gpg --dearmor -o /etc/apt/keyrings/hashicorp.gpg 2>/dev/null; then
        as_root chmod a+r /etc/apt/keyrings/hashicorp.gpg
        echo "deb [signed-by=/etc/apt/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $cn main" \
            | as_root tee /etc/apt/sources.list.d/hashicorp.list >/dev/null
        as_root apt-get update -qq && as_root apt-get install -y vagrant && { ok "Vagrant instalado (repo HashiCorp)"; return 0; }
    fi

    # Fallback: .deb directo desde releases.hashicorp.com.
    warn "Repo APT no disponible para '$cn'; probando el .deb directo..."
    local ver="2.4.3" arch deb
    arch="$(dpkg --print-architecture)"
    deb="$(mktemp --suffix=.deb)"
    if curl -fsSL -o "$deb" "https://releases.hashicorp.com/vagrant/${ver}/vagrant_${ver}-1_${arch}.deb"; then
        as_root apt-get install -y "$deb" && { rm -f "$deb"; ok "Vagrant instalado (.deb ${ver})"; return 0; }
    fi
    rm -f "$deb"
    warn "No se pudo instalar Vagrant automáticamente: https://developer.hashicorp.com/vagrant/install"
    return 1
}

# ssh-keygen (paquete openssh-client)
if command -v ssh-keygen >/dev/null; then
    ok "ssh-keygen ya instalado"
else
    warn "ssh-keygen no encontrado, instalando openssh-client..."
    apt_install openssh-client || { warn "No se pudo instalar openssh-client"; exit 1; }
fi

# Docker Engine: solo se instala si NO está; si ya está, solo se verifica.
if command -v docker >/dev/null; then
    ok "Docker ya instalado ($(docker --version 2>/dev/null | cut -d, -f1))"
else
    warn "Docker no instalado, instalando docker.io y plugin de compose..."
    apt_install docker.io || { warn "Instala Docker manualmente: https://docs.docker.com/engine/install/"; exit 1; }
    apt_install docker-compose-plugin || true
    # Arranca el servicio y añade al usuario al grupo docker (efectivo tras re-login).
    command -v sudo >/dev/null && { sudo systemctl enable --now docker 2>/dev/null || true; sudo usermod -aG docker "$USER" 2>/dev/null || true; }
fi

# Compose v2: si el plugin ya está, solo verifica; si no, lo instala.
if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose v2 ya disponible"
else
    warn "Docker Compose v2 no encontrado, instalando plugin..."
    apt_install docker-compose-plugin || { warn "Instala el plugin de compose v2 manualmente"; exit 1; }
fi

# Verificación final.
command -v ssh-keygen >/dev/null || { warn "ssh-keygen sigue ausente"; exit 1; }
command -v docker     >/dev/null || { warn "docker sigue ausente"; exit 1; }
docker compose version >/dev/null 2>&1 || { warn "docker compose v2 sigue ausente"; exit 1; }
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

# ── config.json (lo usan las herramientas del host: análisis dinámico/kali) ──

CONFIG_FILE="$SCRIPT_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_FILE"
    ok "config.json creado desde config.example.json"
else
    ok "config.json ya existe"
fi
echo ""

# ── paquete Python `compartido` ──────────────────────────────────────────────
# Solo hace falta en el host para el análisis dinámico (dynamic/); el engine lo
# instala dentro de su propia imagen. El resto del lab corre en contenedores.

echo "-- Paquete Python del lab --"
command -v pip3 >/dev/null || apt_install python3-pip || true
if command -v pip3 >/dev/null; then
    pip3 install -e "$SCRIPT_DIR" >/dev/null 2>&1 \
      || pip3 install --user --break-system-packages -e "$SCRIPT_DIR" >/dev/null 2>&1 \
      && ok "paquete compartido instalado (editable)" \
      || warn "no se pudo instalar compartido en el host (solo afecta al análisis dinámico)"
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
    # Dependencias del dinámico: VirtualBox (proveedor del Vagrantfile) y Vagrant
    # (repo oficial de HashiCorp; no está en los repos de Ubuntu). El resto del
    # ciclo (crear VM → aislar → firewall → verificar) lo hace el módulo del
    # dinámico, no este script.
    if ! command -v VBoxManage &>/dev/null; then
        warn "VirtualBox no instalado, instalando..."
        apt_install virtualbox || warn "Instala VirtualBox manualmente: https://www.virtualbox.org/wiki/Linux_Downloads"
    else
        ok "VirtualBox ya instalado"
    fi
    install_vagrant || true

    if command -v vagrant &>/dev/null; then
        # Toda la orquestación del dinámico vive en su propia carpeta (modular):
        # crea/provisiona la VM, la aísla (host-only sin NAT), aplica el firewall
        # y VERIFICA la jaula (gate duro). Ver dinamico/scripts/configurar_dinamico.sh.
        if bash "$SCRIPT_DIR/dinamico/scripts/configurar_dinamico.sh"; then
            KALI_STARTED=true
            ok "Lab dinámico listo y aislamiento verificado"
        else
            warn "No se pudo dejar el lab dinámico aislado/verificado (revisa la salida de arriba)"
        fi
    else
        warn "No se pudo dejar Vagrant disponible; configura Kali luego: bash dinamico/scripts/configurar_dinamico.sh"
    fi
else
    info "Saltado. Para configurar luego: bash dinamico/scripts/configurar_dinamico.sh"
fi
echo ""

# ── Firewall del HOST: protege TU máquina de la VM (lo aplica con sudo) ───────
# Es la capa que descarta lo que la VM/malware intente INICIAR hacia el host
# (escaneo, brute-force SSH). Las reglas de iptables NO persisten al reiniciar el
# host, así que conviene (re)aplicarlas en cada setup. Se ofrece siempre que la
# VM ya exista (vboxnet0 presente) y NO se haya reconfigurado Kali en este setup
# (si SÍ se reconfiguró, configurar_dinamico.sh ya lo aplicó y verificó).
if [ "$KALI_STARTED" != true ] && VBoxManage list hostonlyifs 2>/dev/null | grep -q '^Name:.*vboxnet0'; then
    echo "-- Firewall del host (protege tu máquina de la VM) --"
    read -rp "¿Aplicar el firewall del host ahora (pide sudo)? [S/n]: " resp_fw
    if [[ ! "$resp_fw" =~ ^[Nn]$ ]]; then
        if bash "$SCRIPT_DIR/dinamico/reglas_firewall/aislar_host.sh"; then
            ok "Firewall del host aplicado en vboxnet0 (la VM no puede entrar a tu máquina)"
        else
            warn "No se pudo aplicar (córrelo a mano: bash dinamico/reglas_firewall/aislar_host.sh)"
        fi
    else
        info "Omitido. Aplícalo luego: bash dinamico/reglas_firewall/aislar_host.sh"
    fi
    echo ""
fi

# ── resumen ───────────────────────────────────────────────────────────────────

WEB_PORT=$(grep ^WEB_PORT "$ENV_FILE" | cut -d= -f2)
echo "================================================="
echo "  Setup completo"
echo ""
echo "  Web    → http://localhost:${WEB_PORT:-8000}   (sube muestras y elige comandos)"
echo "  Engine → http://localhost:8001        (API REST)"
echo ""
echo "Útil:"
echo "  docker compose logs -f engine     # ver logs del engine"
echo "  docker compose ps                 # estado de los contenedores"
echo ""
echo "  Ctrl+C para apagar y destruir los contenedores."
echo "================================================="
echo ""

# Mantiene el script vivo; el trap de arriba hace el cleanup al salir.
while true; do sleep 60; done
