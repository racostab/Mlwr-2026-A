#!/bin/bash
set -e

echo "[*] Provisionando Kali Linux para malware lab..."

# Crear usuario kali si no existe
if ! id kali &>/dev/null; then
    useradd -m -s /bin/bash kali
    echo "kali:kali" | chpasswd
    usermod -aG sudo kali
    echo "[+] Usuario kali creado (password: kali)"
fi

# Instalar llave SSH del host
mkdir -p /home/kali/.ssh
chmod 700 /home/kali/.ssh

if [ -f /tmp/host_key.pub ]; then
    cat /tmp/host_key.pub >> /home/kali/.ssh/authorized_keys
    rm -f /tmp/host_key.pub
    echo "[+] Llave SSH del host agregada"
fi

# Copiar también la llave de vagrant para compatibilidad
[ -f /home/vagrant/.ssh/authorized_keys ] && \
    cat /home/vagrant/.ssh/authorized_keys >> /home/kali/.ssh/authorized_keys

chmod 600 /home/kali/.ssh/authorized_keys
chown -R kali:kali /home/kali/.ssh

# Configuración SSH
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/'  /etc/ssh/sshd_config
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/'     /etc/ssh/sshd_config
systemctl restart ssh 2>/dev/null || service ssh restart

# Herramientas de análisis dinámico — SOLO las necesarias (VM mínima).
# El volcado de memoria usa procdump (preferido) con gcore (de gdb) de respaldo.
echo "[*] Instalando herramientas de análisis..."
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    strace \
    ltrace \
    gdb \
    tcpdump \
    file \
    binutils \
    procps \
    curl \
    ca-certificates \
    python3

# procdump (Sysinternals para Linux): es el método de volcado PREFERIDO en
# ejecucion.py; gcore (de gdb, ya instalado arriba) queda como respaldo. No está
# en los repos de Kali, así que se instala desde el repo APT de Microsoft. TODO
# el bloque es NO FATAL: si no se puede, el lab sigue funcionando con gcore.
echo "[*] Instalando procdump (preferido para el volcado de memoria)..."
install_procdump() {
    command -v procdump >/dev/null 2>&1 && return 0          # ya presente
    apt-get install -y -qq procdump 2>/dev/null && return 0  # por si el repo lo trae
    # Repo de Microsoft (config de Debian 12 'bookworm'; Kali es Debian-based).
    local deb="/tmp/ms-prod.deb"
    curl -fsSL -o "$deb" \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb 2>/dev/null || return 1
    dpkg -i "$deb" >/dev/null 2>&1 || return 1
    rm -f "$deb"
    apt-get update -qq || return 1
    apt-get install -y -qq procdump || return 1
    return 0
}
if install_procdump; then
    echo "[+] procdump instalado (volcado preferido)"
else
    echo "[!] No se pudo instalar procdump; el lab usará gcore (gdb) como respaldo."
fi

# El volcado de memoria necesita ptrace sobre procesos no-descendientes y sudo
# no interactivo. Esto es seguro porque la VM es desechable y aislada.
echo 'kernel.yama.ptrace_scope=0' > /etc/sysctl.d/10-ptrace.conf
sysctl -p /etc/sysctl.d/10-ptrace.conf 2>/dev/null || true
echo 'kali ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/kali-lab
chmod 440 /etc/sudoers.d/kali-lab

# Defensa en profundidad: impedir el módulo de carpetas compartidas (vboxsf) y el
# de vídeo (vboxvideo). vboxsf es el sistema de archivos que monta una carpeta
# compartida; sin él NO se puede montar un puente de disco guest→host aunque se
# configure uno por error. No se toca vboxguest (driver base) para no afectar la
# estabilidad de la VM. El bridge de archivos —lo que importa— queda cerrado a
# nivel de kernel, además de quitarse el mapeo (red.py) y vigilarse en el gate.
cat > /etc/modprobe.d/blacklist-vbox-lab.conf <<'EOF'
# Laboratorio de malware: sin puente de archivos guest→host.
blacklist vboxsf
blacklist vboxvideo
install vboxsf /bin/false
EOF
rmmod vboxsf 2>/dev/null || true

echo "[+] Provisioning completo."
echo "    Conéctate con: bash dinamico/scripts/ssh_maquina_virtual.sh  (VM aislada en 192.168.56.10)"
