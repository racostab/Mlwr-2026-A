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

# Herramientas de análisis dinámico
echo "[*] Instalando herramientas de análisis..."
apt-get update -qq
apt-get install -y -qq \
    strace \
    ltrace \
    gdb \
    tcpdump \
    tshark \
    netcat-openbsd \
    binwalk \
    file \
    binutils \
    bsdmainutils \
    python3-pip \
    curl \
    wget \
    net-tools \
    procps \
    procdump

# El volcado de memoria necesita ptrace sobre procesos no-descendientes y sudo
# no interactivo. Esto es seguro porque la VM es desechable y aislada.
echo 'kernel.yama.ptrace_scope=0' > /etc/sysctl.d/10-ptrace.conf
sysctl -p /etc/sysctl.d/10-ptrace.conf 2>/dev/null || true
echo 'kali ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/kali-lab
chmod 440 /etc/sudoers.d/kali-lab

echo "[+] Provisioning completo."
echo "    Conéctate con: ssh -i ~/.ssh/id_rsa -p 2222 kali@127.0.0.1"
