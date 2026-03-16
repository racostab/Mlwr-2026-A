#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ruta completa a la llave privada
KEY="$SCRIPT_DIR/id_rsa"

# SSH rechaza llaves con permisos abiertos, esto los ajusta a solo-lectura del dueño
chmod 600 "$KEY"

# Borra la huella guardada de este servidor para evitar el error "host key changed"
ssh-keygen -f ~/.ssh/known_hosts -R "[127.0.0.1]:2222" 2>/dev/null || true

# Conectarse a Kali:
#   -i  usa esta llave privada específica
#   -p  puerto 2222 (reenvío de puertos de VirtualBox hacia el puerto 22 de Kali)
ssh -i "$KEY" -p 2222 kali@127.0.0.1