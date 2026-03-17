#!/bin/bash


# Leer config.init
SSH_HOST=$(grep "SSH_HOST=" config.init | cut -d'=' -f2)
SSH_PORT=$(grep "SSH_PORT=" config.init | cut -d'=' -f2)
SSH_USER=$(grep "SSH_USER=" config.init | cut -d'=' -f2)
SSH_KEY=$(grep "SSH_KEY=" config.init | cut -d'=' -f2)

KEY="$SSH_KEY"

# Encender el contenedor
docker start kali

chmod 600 "$KEY"

# Conectarse
echo "[+] Conectando a $SSH_USER@$SSH_HOST:$SSH_PORT"
ssh -o StrictHostKeyChecking=no -i "$KEY" -p $SSH_PORT "$SSH_USER@$SSH_HOST"
