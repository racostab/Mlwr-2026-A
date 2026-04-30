#!/bin/bash
SSH_HOST=$(grep "SSH_HOST=" config.init | cut -d'=' -f2)
SSH_PORT=$(grep "SSH_PORT=" config.init | cut -d'=' -f2)
SSH_USER=$(grep "SSH_USER=" config.init | cut -d'=' -f2)
SSH_KEY=$(grep "SSH_KEY=" config.init | cut -d'=' -f2)
KEY="$SSH_KEY"

docker start kali
chmod 600 "$KEY"

echo "[+] Esperando que SSH esté disponible en $SSH_HOST:$SSH_PORT..."


for i in $(seq 1 15); do
    if ssh -o StrictHostKeyChecking=no \
           -o ConnectTimeout=1 \
           -o BatchMode=yes \
           -i "$KEY" -p "$SSH_PORT" \
           "$SSH_USER@$SSH_HOST" true 2>/dev/null; then
        break
    fi
    sleep 1
done

echo "[+] Conectando a $SSH_USER@$SSH_HOST:$SSH_PORT"
ssh -o StrictHostKeyChecking=no -i "$KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST"
