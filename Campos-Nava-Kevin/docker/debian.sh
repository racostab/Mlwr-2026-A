#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/config.json"

if ! command -v jq &>/dev/null; then
    echo "[!] jq requerido: sudo apt install jq"
    exit 1
fi

HOST=$(jq -r '.docker.host'      "$CONFIG")
PORT=$(jq -r '.docker.port'      "$CONFIG")
USER=$(jq -r '.docker.user'      "$CONFIG")
KEY=$(eval  echo "$(jq -r '.docker.key_path' "$CONFIG")")
CONTAINER=$(jq -r '.docker.container' "$CONFIG")

docker start "$CONTAINER"
sleep 2
chmod 600 "$KEY"
ssh -o StrictHostKeyChecking=no -i "$KEY" -p "$PORT" "$USER@$HOST"
