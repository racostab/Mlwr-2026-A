#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/config.json"

if ! command -v jq &>/dev/null; then
    echo "[!] jq requerido: sudo apt install jq"
    exit 1
fi

HOST=$(jq -r '.kali.host'     "$CONFIG")
PORT=$(jq -r '.kali.port'     "$CONFIG")
USER=$(jq -r '.kali.user'     "$CONFIG")
KEY=$(eval echo "$(jq -r '.kali.key_path' "$CONFIG")")

ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[$HOST]:$PORT" 2>/dev/null || true
chmod 600 "$KEY"
ssh -o StrictHostKeyChecking=no -i "$KEY" -p "$PORT" "$USER@$HOST"
