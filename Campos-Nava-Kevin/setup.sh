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
    # VirtualBox: proveedor que usa el Vagrantfile.
    if ! command -v VBoxManage &>/dev/null; then
        warn "VirtualBox no instalado, instalando..."
        apt_install virtualbox || warn "Instala VirtualBox manualmente: https://www.virtualbox.org/wiki/Linux_Downloads"
    else
        ok "VirtualBox ya instalado"
    fi

    # Vagrant (repo oficial de HashiCorp; no está en los repos de Ubuntu).
    install_vagrant || true

    if command -v vagrant &>/dev/null; then
        info "Levantando la VM Kali (vagrant up, puede tardar la primera vez)..."
        (cd "$SCRIPT_DIR/dinamico/maquina_virtual" && vagrant up)
        KALI_STARTED=true

        # Aislar: apagar, quitar el NAT (queda solo en host-only, sin internet) y
        # arrancar headless. Tras esto la VM solo es accesible en 192.168.56.10.
        info "Aislando la VM (host-only, sin internet)..."
        VM_NAME=$(python3 -c "import json;print(json.load(open('$CONFIG_FILE'))['kali']['vm_name'])" 2>/dev/null || echo kali-malware-lab)
        (cd "$SCRIPT_DIR/dinamico/maquina_virtual" && vagrant halt) || true
        if IP_VM=$(python3 "$SCRIPT_DIR/dinamico/scripts/red_aislada.py" "$VM_NAME"); then
            ok "VM aislada y encendida en $IP_VM (sin NAT)"
            info "Conéctate con: bash dinamico/scripts/ssh_maquina_virtual.sh"
        else
            warn "No se pudo aislar la VM automáticamente (revisa VirtualBox)"
        fi
    else
        warn "No se pudo dejar Vagrant disponible; configura Kali luego con 'vagrant up'"
    fi
else
    info "Saltado. Para configurar luego: vagrant up"
fi
echo ""

# ── Firewall del HOST: aislar el host de la VM (red host-only) ────────────────
# Se aplica si se configuró Kali en este setup ($KALI_STARTED) o si ya existe la
# interfaz host-only vboxnet0 (re-run, p. ej. tras reiniciar el host). Las reglas
# de iptables NO persisten al reiniciar el host, por eso se reaplican aquí.
if [ "$KALI_STARTED" = true ] || VBoxManage list hostonlyifs 2>/dev/null | grep -q '^Name:.*vboxnet0'; then
    echo "-- Firewall del host: aislando el host de la VM (host-only) --"
    if bash "$SCRIPT_DIR/dinamico/reglas_firewall/aislar_host.sh"; then
        ok "Firewall aplicado en vboxnet0 (la VM no puede iniciar conexiones hacia el host)"
    else
        warn "No se pudo aplicar el firewall (córrelo a mano: bash dinamico/reglas_firewall/aislar_host.sh)"
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
