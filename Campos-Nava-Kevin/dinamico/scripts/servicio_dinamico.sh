#!/bin/bash
# Arranca el servicio HOST del análisis dinámico (FastAPI, fuera de Docker).
#
# La web (en Docker) lo llama vía host.docker.internal:8002 para disparar
# detonaciones en la VM aislada. Debe correr en el host porque usa VBoxManage y
# sudo iptables, que no existen dentro de los contenedores.
#
# Requisitos:  pip install -e ".[dinamico]"   (fastapi + uvicorn + multipart)
# Uso:         bash dinamico/scripts/servicio_dinamico.sh
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"          # dinamico/
PUERTO="${DYNAMIC_PORT:-8002}"

if ! python3 -c "import fastapi, uvicorn, multipart" 2>/dev/null; then
    echo "[!] Faltan dependencias del servicio dinámico."
    echo "    Instálalas en el host:  pip install -e \".[dinamico]\""
    exit 1
fi

echo "[*] Servicio dinámico escuchando en http://0.0.0.0:$PUERTO"
echo "    (la web lo alcanza por host.docker.internal:$PUERTO)"
# sys.path[0] = la carpeta del paquete: imports planos (analizador_dinamico, red…).
cd "$DIR/analizador"
exec env DYNAMIC_PORT="$PUERTO" python3 servicio_dinamico.py
