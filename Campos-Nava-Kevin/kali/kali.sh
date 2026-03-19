#!/bin/bash

# Instalar sshpass si no está instalado
if ! command -v sshpass &>/dev/null; then
    echo "[*] Instalando sshpass..."
    sudo apt install -y sshpass
fi

# Leer config_kali.ini
HOST=$(grep "^host"     config_kali.ini | cut -d'=' -f2 | tr -d ' ')
PORT=$(grep "^port"     config_kali.ini | cut -d'=' -f2 | tr -d ' ')
USER=$(grep "^user"     config_kali.ini | cut -d'=' -f2 | tr -d ' ')

KEY="$HOME/.ssh/id_rsa"

chmod 600 "$KEY"

# Limpiar huella guardada
ssh-keygen -f ~/.ssh/known_hosts -R "[$HOST]:$PORT" 2>/dev/null || true

# Conectarse sin contraseña
ssh -o StrictHostKeyChecking=no -i "$KEY" -p "$PORT" "$USER@$HOST"