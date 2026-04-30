#!/bin/bash

# Leer config.ini
HOST=$(grep "^host" config_debian.ini | cut -d'=' -f2 | tr -d ' ')
PORT=$(grep "^port" config_debian.ini | cut -d'=' -f2 | tr -d ' ')
USER=$(grep "^user" config_debian.ini | cut -d'=' -f2 | tr -d ' ')

KEY="$HOME/.ssh/id_rsa"

# Arrancar el contenedor
docker start debian

sleep 2

chmod 600 "$KEY"

# Conectarse con llave
ssh -o StrictHostKeyChecking=no -i "$KEY" -p "$PORT" "$USER@$HOST"