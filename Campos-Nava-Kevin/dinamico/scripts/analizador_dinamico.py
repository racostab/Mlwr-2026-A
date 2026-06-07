#!/usr/bin/env python3
"""Análisis dinámico en la VM Kali: enciende la VM, ejecuta la muestra y
captura un volcado de memoria con procdump (o gcore como alternativa).

Uso:
    python3 dinamico/scripts/analizador_dinamico.py <ruta_local> [segundos_ejecucion]

Flujo:
    1. Enciende la VM `kali` (VBoxManage, headless) si no está corriendo.
    2. Espera a que el SSH responda.
    3. Sube la muestra por SFTP y la marca como ejecutable.
    4. La ejecuta en segundo plano bajo `timeout`, capturando stdout/stderr.
    5. Corre procdump contra su PID para volcar la memoria (gcore si falla).
    6. Trae el volcado y los logs al host (./dynamic_output/<timestamp>/).

El volcado de memoria usa gcore (de gdb); requiere ptrace_scope=0 y sudo NOPASSWD
para el usuario `kali` (lo deja listo dinamico/user_data/provision_kali.sh).
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from compartido.configuracion import kali as cfg
from compartido.sftp.conexion import conectar, subir
import red_aislada


def esperar_ssh(host, port, user, key, intentos=36, espera=5):
    print(f"[*] Esperando SSH en {host}:{port} ...")
    ultimo = None
    for i in range(intentos):
        try:
            return conectar(host, port, user, key, label="Kali")
        except Exception as e:  # noqa: BLE001 — reintento hasta timeout
            ultimo = e
            time.sleep(espera)
    raise TimeoutError(f"SSH no respondió tras {intentos * espera}s: {ultimo}")


def aislar_host() -> None:
    """Aplica el firewall que aísla el host de la VM (dinamico/reglas_firewall/aislar_host.sh).

    Si existe la interfaz host-only `vboxnet0` pero el firewall no se puede
    aplicar, aborta: es preferible no ejecutar la muestra a hacerlo con el host
    expuesto. Si no hay `vboxnet0`, solo advierte (la VM podría tener internet).
    """
    hostonly = subprocess.run(
        ["VBoxManage", "list", "hostonlyifs"], capture_output=True, text=True
    ).stdout
    if "vboxnet0" not in hostonly:
        print("[!] ADVERTENCIA: no detecto la interfaz host-only 'vboxnet0'.")
        print("    La VM podría NO estar aislada (¿NAT con internet?). Revisa config de red.")
        return
    script = Path(__file__).parent.parent / "reglas_firewall" / "aislar_host.sh"
    print("[*] Aplicando firewall de aislamiento host-only (pedirá sudo)...")
    r = subprocess.run(["bash", str(script)])
    if r.returncode != 0:
        raise RuntimeError(
            "No se pudo aplicar el firewall host-only; abortando por seguridad. "
            "Corre 'bash dinamico/reglas_firewall/aislar_host.sh' a mano y reintenta."
        )


def _ejecutar(client, comando: str, mostrar=True) -> str:
    _, stdout, stderr = client.exec_command(comando)
    stdout.channel.recv_exit_status()
    salida = stdout.read().decode(errors="replace").strip()
    error = stderr.read().decode(errors="replace").strip()
    if mostrar and salida:
        print(f"    [OUT] {salida}")
    if mostrar and error:
        print(f"    [ERR] {error}")
    return salida


def analizar(local_path: str, segundos: int = 20) -> None:
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Muestra no encontrada: {local_path}")

    c = cfg()
    name = c["vm_name"]
    user = c["user"]

    # Deja la VM corriendo en la red AISLADA (host-only, sin NAT) y conéctate por
    # su IP privada. Ver dinamico/scripts/red_aislada.py.
    ip = red_aislada.preparar_aislada(name)
    client = esperar_ssh(ip, 22, user, c["key_path"])
    try:
        # Cinturón y tirantes: aislar el host ANTES de ejecutar nada.
        aislar_host()

        nombre = os.path.basename(local_path)
        home = f"/home/{user}"
        remoto = f"{home}/{nombre}"
        dump_dir = f"{home}/dumps"

        print(f"[*] Subiendo muestra → {remoto}")
        subir(client, local_path, remoto)
        _ejecutar(client, f"chmod +x {remoto} && rm -rf {dump_dir} && mkdir -p {dump_dir}",
                  mostrar=False)

        # Ejecutar la muestra directamente en segundo plano para que $! sea el
        # PID real del binario (no el de un wrapper como timeout/setsid).
        print(f"[*] Ejecutando la muestra (la dejo correr {segundos}s antes del volcado)...")
        run = (
            f"cd {home} && {remoto} "
            f">{dump_dir}/stdout.log 2>{dump_dir}/stderr.log & echo $!"
        )
        pid = _ejecutar(client, run, mostrar=False)
        target = pid if pid.isdigit() else ""
        if not target:
            print(f"[!] No se obtuvo un PID válido (la muestra pudo salir al instante): {pid!r}")
        else:
            print(f"[+] Muestra lanzada con PID {target}")

        time.sleep(segundos)  # dejar que se cargue/desempaquete en memoria

        # Si el PID original murió (la muestra pudo daemonizarse), buscar un
        # proceso superviviente con el nombre del binario.
        vivo = _ejecutar(client, f"kill -0 {target} 2>/dev/null && echo si || echo no",
                         mostrar=False) if target else "no"
        if vivo != "si":
            superv = _ejecutar(client, f"pgrep -f {nombre} | head -n1", mostrar=False)
            if superv.isdigit():
                print(f"[*] El PID original no sigue vivo; uso el superviviente {superv}")
                target = superv
                vivo = "si"

        if vivo != "si":
            print("[!] No hay proceso vivo de la muestra; no se pudo volcar su memoria.")
        else:
            print(f"[*] Volcando memoria del PID {target} con procdump...")
            _ejecutar(client, f"sudo -n procdump -n 1 {target} {dump_dir} 2>&1")
            # Si procdump no está o no generó archivo, intentar gcore.
            hay_dump = _ejecutar(
                client, f"ls -1 {dump_dir}/*.core {dump_dir}/*.dmp 2>/dev/null | wc -l",
                mostrar=False,
            )
            if hay_dump.strip() == "0":
                print("[*] procdump no generó volcado; intentando gcore...")
                _ejecutar(client, f"sudo -n gcore -o {dump_dir}/core {target} 2>&1")

        # Matar cualquier proceso superviviente de la muestra.
        _ejecutar(client, f"sudo -n pkill -9 -f {nombre} 2>/dev/null; true", mostrar=False)

        # Traer resultados al host.
        destino = Path("dynamic_output") / datetime.now().strftime("%Y%m%d-%H%M%S")
        destino.mkdir(parents=True, exist_ok=True)
        archivos = _ejecutar(client, f"ls -1 {dump_dir} 2>/dev/null", mostrar=False)
        sftp = client.open_sftp()
        try:
            for f in archivos.splitlines():
                f = f.strip()
                if not f:
                    continue
                sftp.get(f"{dump_dir}/{f}", str(destino / f))
                print(f"[+] Recuperado: {destino / f}")
        finally:
            sftp.close()

        print(f"\n[✓] Análisis dinámico completo. Resultados en: {destino}/")
        print("    (la VM sigue encendida; apágala con 'dinamico/scripts/control_maquina_virtual.sh stop kali' si quieres)")
    finally:
        client.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 dinamico/scripts/analizador_dinamico.py <ruta_local> [segundos_ejecucion]")
        sys.exit(1)
    ruta = sys.argv[1]
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    try:
        analizar(ruta, secs)
    except Exception as e:  # noqa: BLE001
        print(f"[!] {e}")
        sys.exit(1)
