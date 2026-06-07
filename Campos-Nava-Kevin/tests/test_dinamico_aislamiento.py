"""Test de AISLAMIENTO de la VM dinámica (Kali) — opt-in.

Comprueba que la VM queda "amurallada" en una red host-only de VirtualBox:

  ✅ El host SÍ puede ENTRAR por SFTP        (el único canal aprobado)
  ❌ La VM NO puede iniciar conexiones al host (el firewall las descarta)
  ❌ La VM NO tiene salida a internet         (red host-only, sin NAT)

NO corre por defecto: necesita VirtualBox y la VM Kali (que normalmente no está),
así que se SALTA solo y no afecta al resto de la suite. Para correrlo de verdad:

    LAB_DINAMICO=1 pytest tests/test_dinamico_aislamiento.py -v

    # crear la VM si falta (necesita vagrant):
    LAB_DINAMICO=1 LAB_DINAMICO_CREAR=1 pytest tests/test_dinamico_aislamiento.py -v
    # apagar la VM al terminar:
    LAB_DINAMICO=1 LAB_DINAMICO_APAGAR=1 pytest tests/test_dinamico_aislamiento.py -v

Aplicar el firewall usa `sudo` (iptables): córrelo donde puedas autenticarte.
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from shutil import which

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dinamico" / "scripts"))

# Interruptor general: si no se pide explícitamente, ni se intenta.
pytestmark = pytest.mark.skipif(
    os.environ.get("LAB_DINAMICO") != "1",
    reason="análisis dinámico desactivado (exporta LAB_DINAMICO=1 para activarlo)",
)


def _en_vm(client, comando: str, timeout: int = 20):
    """Corre un comando dentro de la VM por SSH; devuelve (rc, stdout, stderr)."""
    _, stdout, stderr = client.exec_command(comando, timeout=timeout)
    rc = stdout.channel.recv_exit_status()
    return (
        rc,
        stdout.read().decode(errors="replace").strip(),
        stderr.read().decode(errors="replace").strip(),
    )


def _rc_de(salida: str) -> str:
    """Extrae el 'rc=N' que imprimimos al final del comando remoto."""
    return salida.split("rc=")[-1].strip()


@pytest.fixture(scope="module")
def vm_aislada():
    """Levanta (si se desea) la VM en red host-only, aplica el firewall y conecta.

    Cada paso que no se cumpla hace `skip` con un motivo claro, para que el test
    explique qué falta en lugar de fallar de forma confusa.
    """
    import red_aislada as red
    from compartido.configuracion import kali
    from compartido.sftp.conexion import conectar
    import analizador_dinamico as runner

    if not red.disponible():
        pytest.skip("VBoxManage no está instalado (instala VirtualBox)")

    cfg = kali()
    vm = cfg["vm_name"]

    # 1) ¿Existe la VM? Si no, crearla solo si se pide (y hay vagrant).
    if not red.vm_existe(vm):
        if os.environ.get("LAB_DINAMICO_CREAR") == "1":
            if not which("vagrant"):
                pytest.skip("la VM no existe y vagrant no está instalado para crearla")
            vdir = ROOT / "dinamico" / "maquina_virtual"
            subprocess.run(["vagrant", "up"], cwd=vdir, check=True)
        else:
            pytest.skip(f"la VM '{vm}' no existe (usa LAB_DINAMICO_CREAR=1 para crearla)")

    # 2) Conexión AISLADA con la API de VirtualBox: host-only, sin NAT.
    #    preparar_aislada asegura vboxnet0, le quita el NAT y arranca la VM.
    arrancada_por_test = not red.vm_corriendo(vm)
    host_ip = red.HOST_IP                 # 192.168.56.1 (el host en la red privada)
    guest_ip = red.preparar_aislada(vm)   # 192.168.56.10 (la VM, ya aislada)
    port = 22

    client = None
    ultimo_error = None
    for _ in range(40):  # ~200 s
        try:
            client = conectar(guest_ip, port, cfg["user"], cfg["key_path"],
                              label="Kali (aislada)")
            break
        except Exception as e:  # noqa: BLE001 — reintento hasta timeout
            ultimo_error = e
            time.sleep(5)
    if client is None:
        pytest.skip(f"no se pudo abrir SSH a la VM ({guest_ip}:{port}): {ultimo_error}")

    # 4) Firewall: cortar lo que la VM inicie hacia el host (deja pasar SFTP).
    try:
        runner.aislar_host()
    except Exception as e:  # noqa: BLE001
        client.close()
        pytest.skip(f"no se pudo aplicar el firewall de aislamiento: {e}")

    yield {"client": client, "vm": vm, "host_ip": host_ip, "guest_ip": guest_ip}

    client.close()
    if arrancada_por_test and os.environ.get("LAB_DINAMICO_APAGAR") == "1":
        red.apagar_vm(vm)


# ── canal APROBADO: el host entra por SFTP ───────────────────────────────────

def test_sftp_entrada_aprobada(vm_aislada):
    """El host SÍ puede transferir por SFTP: subir un archivo y recuperarlo."""
    client = vm_aislada["client"]
    sftp = client.open_sftp()
    try:
        remoto = "/tmp/lab_aislamiento_prueba.txt"
        contenido = "aislamiento-ok"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(contenido)
            local = f.name

        sftp.put(local, remoto)                       # ENTRADA por SFTP (permitida)
        assert sftp.stat(remoto).st_size == len(contenido)

        vuelta = local + ".back"
        sftp.get(remoto, vuelta)
        assert Path(vuelta).read_text() == contenido

        sftp.remove(remoto)
    finally:
        sftp.close()


# ── lo RECHAZADO: la VM no puede iniciar nada hacia el host ───────────────────

@pytest.mark.parametrize("puerto", [22, 8001])
def test_vm_no_puede_conectar_al_host(vm_aislada, puerto):
    """La VM NO puede ABRIR conexiones hacia el host (el firewall las descarta).

    Probamos puertos que el host suele tener escuchando (SSH 22, engine 8001). Con
    el firewall de aislamiento el intento queda colgado y `timeout` lo corta
    (rc 124); sin firewall conectaría (rc 0). Cualquier rc != 0 ⇒ la VM no llegó.
    """
    client = vm_aislada["client"]
    host_ip = vm_aislada["host_ip"]
    cmd = f"timeout 5 bash -c 'echo > /dev/tcp/{host_ip}/{puerto}' 2>/dev/null; echo rc=$?"
    _, salida, _ = _en_vm(client, cmd, timeout=15)
    assert _rc_de(salida) != "0", (
        f"¡La VM alcanzó {host_ip}:{puerto}! No está aislada del host."
    )


def test_vm_sin_salida_a_internet(vm_aislada):
    """Red host-only sin NAT: la VM no puede salir a internet."""
    client = vm_aislada["client"]
    cmd = "timeout 6 ping -c1 -W3 8.8.8.8 >/dev/null 2>&1; echo rc=$?"
    _, salida, _ = _en_vm(client, cmd, timeout=15)
    assert _rc_de(salida) != "0", "La VM tiene internet; debería estar aislada (sin NAT)."
