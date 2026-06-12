#!/bin/bash
# Valida el GATE de aislamiento ANTES de detonar la primera muestra real.
#
# Prueba dos cosas con hechos:
#   1. Camino feliz : la VM aislada pasa las 4 comprobaciones (verificacion.py).
#   2. Camino de fallo: si se reactiva el NAT, el gate LO DETECTA (la comprobación
#      crítica `nat_desconectado` devuelve False ⇒ el análisis abortaría). Esto se
#      hace con la VM APAGADA: NUNCA se arranca una VM con salida a internet.
#
# Además deja listo un canario benigno (/tmp/canario_aislamiento.sh) que puedes
# detonar con el runner para confirmar en el strace.log que las conexiones
# salientes fallan.
#
# Uso:  bash dinamico/scripts/validar_aislamiento.sh [nombre_vm]
set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"          # dinamico/
ANALIZADOR="$DIR/analizador"
VM="${1:-kali-malware-lab}"

echo "=================================================================="
echo " Validación del gate de aislamiento — VM: $VM"
echo "=================================================================="

# ---------------------------------------------------------------------------
# 1. CAMINO FELIZ: aísla la VM y exige que el gate pase (exit 0).
# ---------------------------------------------------------------------------
echo
echo "[1/3] Camino feliz: la VM aislada debe pasar las 4 comprobaciones..."
if python3 "$ANALIZADOR/verificacion.py" "$VM"; then
    echo "    => OK: el gate confirma la jaula cerrada."
else
    echo "    => FALLO: el gate NO confirmó el aislamiento. Revisa red/firewall."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. CAMINO DE FALLO: con la VM APAGADA, reactivar el NAT y comprobar que la
#    comprobación crítica lo detecta. Restaurar siempre el NAT a 'null'.
# ---------------------------------------------------------------------------
echo
echo "[2/3] Camino de fallo: si vuelve el NAT, el gate debe detectarlo..."
VBoxManage controlvm "$VM" poweroff 2>/dev/null || true
sleep 2
VBoxManage modifyvm "$VM" --nic1 nat
echo "    (NAT reactivado temporalmente; la VM sigue APAGADA, sin arrancar)"

GATE_DETECTA=$(cd "$ANALIZADOR" && python3 - "$VM" <<'PY'
import sys
import red, verificacion
vm = sys.argv[1]
ok, modo = verificacion.nat_desconectado(vm)
# ok=True significaría "NAT desconectado"; aquí esperamos False (NAT activo).
print("DETECTA" if not ok else "NO_DETECTA", modo)
PY
)
echo "    Resultado: $GATE_DETECTA"

# Restaurar SIEMPRE el aislamiento del NAT, pase lo que pase.
VBoxManage modifyvm "$VM" --nic1 null
echo "    (NAT vuelto a 'null': VM de nuevo aislada)"

case "$GATE_DETECTA" in
  DETECTA*) echo "    => OK: el gate detecta el NAT activo y abortaría la detonación." ;;
  *)        echo "    => FALLO GRAVE: el gate NO detectó el NAT. NO detones nada."; exit 1 ;;
esac

# ---------------------------------------------------------------------------
# 3. Canario benigno: un script que INTENTA salir a internet por varias vías.
#    Detonarlo con el runner y revisar dumps/strace.log: los connect() deben
#    fallar (ECONNREFUSED/ETIMEDOUT/EHOSTUNREACH). Es la prueba de extremo a
#    extremo de que, ya dentro de la VM, una muestra no puede llamar a casa.
# ---------------------------------------------------------------------------
CANARIO=/tmp/canario_aislamiento.sh
cat > "$CANARIO" <<'PY'
#!/bin/bash
# Canario BENIGNO: intenta salir a internet por TCP/DNS/HTTP. Todo debe fallar
# en una VM aislada. No hace nada dañino: solo prueba conectividad y termina.
echo "[canario] intentando conexiones salientes (deberían fallar)..."
for ip in 1.1.1.1 8.8.8.8; do
    timeout 3 bash -c "echo > /dev/tcp/$ip/53" 2>/dev/null \
        && echo "[canario] SALIO a $ip:53  <-- FUGA" \
        || echo "[canario] bloqueado $ip:53  (ok)"
done
timeout 3 getent hosts google.com >/dev/null 2>&1 \
    && echo "[canario] DNS resolvió  <-- FUGA" \
    || echo "[canario] DNS bloqueado (ok)"
command -v curl >/dev/null && timeout 3 curl -s http://example.com >/dev/null 2>&1 \
    && echo "[canario] HTTP salió  <-- FUGA" \
    || echo "[canario] HTTP bloqueado (ok)"
echo "[canario] fin"
PY
chmod +x "$CANARIO"

echo
echo "[3/3] Canario benigno listo en: $CANARIO"
echo "      Detónalo de extremo a extremo y revisa el strace.log:"
echo "          python3 $DIR/analizador/analizador_dinamico.py $CANARIO 10"
echo "      En dynamic_output/<ts>/stdout.log no debe aparecer ninguna FUGA;"
echo "      en strace.log los connect() a 1.1.1.1/8.8.8.8 deben fallar."
echo
echo "=================================================================="
echo " Gate validado. Si el paso 3 tampoco muestra fugas, es seguro detonar."
echo "=================================================================="
