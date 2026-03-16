#!/bin/bash
# Coloca este script junto a id_rsa y ejecuta: bash ./kali.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KEY="$SCRIPT_DIR/id_rsa"

chmod 600 "$KEY"
ssh-keygen -f ~/.ssh/known_hosts -R "[127.0.0.1]:2222" 2>/dev/null || true

ssh -i "$KEY" -p 2222 kali@127.0.0.1