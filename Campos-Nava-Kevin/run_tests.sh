#!/bin/bash
# Corre la suite de tests del lab en un venv aislado, más dos validaciones de
# infraestructura (compose y Django). No necesita el lab levantado: los tests de
# integración se saltan solos si el engine no responde.
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-/tmp/lab_test_venv}"

echo "== preparando venv en $VENV =="
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -e "$ROOT"                                   # paquete compartido
"$VENV/bin/pip" install -q -r "$ROOT/estatico/user_data/motor/requirements.txt"  # importar el motor
"$VENV/bin/pip" install -q -r "$ROOT/web/requirements.txt"              # django + requests
"$VENV/bin/pip" install -q pytest

echo ""
echo "== pytest =="
"$VENV/bin/python" -m pytest "$ROOT/tests" -q

echo ""
echo "== docker compose config =="
if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then
    docker compose -f "$ROOT/docker-compose.yml" config >/dev/null && echo "compose OK"
else
    echo "(docker no disponible; salto la validación de compose)"
fi

echo ""
echo "== django check =="
(cd "$ROOT/web" && "$VENV/bin/python" manage.py check)

echo ""
echo "[OK] Todo verde."
