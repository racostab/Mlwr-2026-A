"""Ejecución de la muestra en la VM y volcado de memoria.

Responsabilidad: una vez la VM está AISLADA y VERIFICADA (de eso se encargan
`aislamiento`/`verificacion`), aquí se sube la muestra, se ejecuta acotada por
tiempo BAJO strace (registro de syscalls), se vuelca su memoria (procdump →
gcore de respaldo) y se traen los resultados al host (strace.log + stdout/stderr
+ volcado). Lo orquesta `analizador_dinamico.py`.

Nota sobre ptrace: strace mantiene la muestra bajo ptrace y gcore/procdump
también lo usan, pero solo puede haber UN tracer a la vez; por eso se mata strace
(el kernel desengancha la muestra, que sigue viva) justo antes del volcado.

El volcado usa gcore (de gdb); requiere `ptrace_scope=0` y sudo NOPASSWD para el
usuario `kali` (lo deja listo `dinamico/user_data/provision_kali.sh`).
"""
import os
import time
from datetime import datetime
from pathlib import Path

from compartido.sftp.conexion import conectar_con_reintentos, subir


def esperar_ssh(host, port, user, key, intentos=36, espera=5):
    """Abre SSH a la VM reintentando hasta que el `sshd` responda (VM recién booteada)."""
    return conectar_con_reintentos(host, port, user, key, label="Kali",
                                   intentos=intentos, espera=espera)


def ejecutar_remoto(client, comando: str, mostrar=True) -> str:
    """Corre un comando por SSH en la VM; devuelve stdout (e imprime OUT/ERR)."""
    _, stdout, stderr = client.exec_command(comando)
    stdout.channel.recv_exit_status()
    salida = stdout.read().decode(errors="replace").strip()
    error = stderr.read().decode(errors="replace").strip()
    if mostrar and salida:
        print(f"    [OUT] {salida}")
    if mostrar and error:
        print(f"    [ERR] {error}")
    return salida


def correr_y_volcar(client, local_path: str, user: str, segundos: int) -> Path:
    """Sube la muestra, la ejecuta `segundos` bajo strace, vuelca su memoria y trae resultados.

    Devuelve la carpeta local (`dynamic_output/<timestamp>/`) con el volcado, el
    `strace.log` (syscalls) y los logs (stdout/stderr de la muestra).
    """
    nombre = os.path.basename(local_path)
    home = f"/home/{user}"
    remoto = f"{home}/{nombre}"
    dump_dir = f"{home}/dumps"

    print(f"[*] Subiendo muestra → {remoto}")
    subir(client, local_path, remoto)
    ejecutar_remoto(client, f"chmod +x {remoto} && rm -rf {dump_dir} && mkdir -p {dump_dir}",
                    mostrar=False)

    # Ejecutar la muestra BAJO strace para registrar sus syscalls (connect/open/
    # execve/...). strace queda como proceso padre y la muestra como su hijo, así
    # que $! es el PID de strace; el PID real del binario es su hijo.
    print(f"[*] Ejecutando la muestra bajo strace (la dejo correr {segundos}s antes del volcado)...")
    run = (
        f"cd {home} && strace -f -tt -T -o {dump_dir}/strace.log {remoto} "
        f">{dump_dir}/stdout.log 2>{dump_dir}/stderr.log & echo $!"
    )
    tracer = ejecutar_remoto(client, run, mostrar=False)
    tracer = tracer if tracer.isdigit() else ""

    # El PID real de la muestra es el hijo de strace (hace fork+exec).
    time.sleep(1)  # darle a strace un instante para exec-ear la muestra
    target = ejecutar_remoto(client, f"pgrep -P {tracer} | head -n1",
                             mostrar=False) if tracer else ""
    target = target if target.isdigit() else ""
    if not target:
        print("[!] No se obtuvo un PID válido (la muestra pudo salir al instante; "
              "aun así strace.log captura sus syscalls)")
    else:
        print(f"[+] Muestra lanzada con PID {target} (strace PID {tracer})")

    time.sleep(segundos)  # dejar que se cargue/desempaquete en memoria

    # Si el PID original murió (la muestra pudo daemonizarse), buscar un proceso
    # superviviente con el nombre del binario.
    vivo = ejecutar_remoto(client, f"kill -0 {target} 2>/dev/null && echo si || echo no",
                           mostrar=False) if target else "no"
    if vivo != "si":
        superv = ejecutar_remoto(client, f"pgrep -f {nombre} | head -n1", mostrar=False)
        if superv.isdigit():
            print(f"[*] El PID original no sigue vivo; uso el superviviente {superv}")
            target = superv
            vivo = "si"

    # strace tiene la muestra bajo ptrace, y gcore/procdump también usan ptrace
    # (solo un tracer a la vez). Matamos strace: el kernel DESENGANCHA a la muestra
    # —que sigue viva— y se vacía/cierra strace.log, dejando el ptrace libre para
    # el volcado.
    if tracer:
        ejecutar_remoto(client, f"kill {tracer} 2>/dev/null; true", mostrar=False)
        time.sleep(1)  # esperar a que el kernel complete el detach

    if vivo != "si":
        print("[!] No hay proceso vivo de la muestra; no se pudo volcar su memoria.")
    else:
        print(f"[*] Volcando memoria del PID {target} con procdump...")
        ejecutar_remoto(client, f"sudo -n procdump -n 1 {target} {dump_dir} 2>&1")
        # Si procdump no está o no generó archivo, intentar gcore.
        hay_dump = ejecutar_remoto(
            client, f"ls -1 {dump_dir}/*.core {dump_dir}/*.dmp 2>/dev/null | wc -l",
            mostrar=False,
        )
        if hay_dump.strip() == "0":
            print("[*] procdump no generó volcado; intentando gcore...")
            ejecutar_remoto(client, f"sudo -n gcore -o {dump_dir}/core {target} 2>&1")

    # Matar cualquier proceso superviviente de la muestra.
    ejecutar_remoto(client, f"sudo -n pkill -9 -f {nombre} 2>/dev/null; true", mostrar=False)

    # Traer resultados al host.
    destino = Path("dynamic_output") / datetime.now().strftime("%Y%m%d-%H%M%S")
    destino.mkdir(parents=True, exist_ok=True)
    archivos = ejecutar_remoto(client, f"ls -1 {dump_dir} 2>/dev/null", mostrar=False)
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
    return destino
