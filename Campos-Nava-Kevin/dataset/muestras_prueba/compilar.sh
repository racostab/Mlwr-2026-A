#!/usr/bin/env bash
# Compila TODAS las muestras senuelo benignas (senuelo_*.c) y muestra su sha256
# (asi se nombran en el lab). Estatico si hay libc estatica; si no, dinamico.
set -euo pipefail
cd "$(dirname "$0")"

for SRC in senuelo_*.c; do
    OUT="${SRC%.c}"
    if gcc -static -O2 -o "$OUT" "$SRC" 2>/dev/null; then
        modo="ESTATICO"
    else
        gcc -O2 -o "$OUT" "$SRC"
        modo="DINAMICO"
    fi
    printf '[ok] %-20s %-9s sha256=%s\n' "$OUT" "$modo" \
        "$(sha256sum "$OUT" | cut -d' ' -f1)"
done

cat <<'EOF'

Pruebalos dinamicamente en la VM (ej. 20 s):
  python3 dinamico/analizador/analizador_dinamico.py dataset/muestras_prueba/senuelo_botnet  20
  python3 dinamico/analizador/analizador_dinamico.py dataset/muestras_prueba/senuelo_red     20
  python3 dinamico/analizador/analizador_dinamico.py dataset/muestras_prueba/senuelo_memoria 20
EOF
