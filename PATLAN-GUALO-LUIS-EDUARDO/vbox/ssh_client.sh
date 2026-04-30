#!/bin/bash

SSH_HOST=$(grep "SSH_HOST=" config.init | cut -d'=' -f2)
SSH_PORT=$(grep "SSH_PORT=" config.init | cut -d'=' -f2)
SSH_USER=$(grep "SSH_USER=" config.init | cut -d'=' -f2)

echo "[+] Conectando a $SSH_USER@$SSH_HOST:$SSH_PORT"
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST
