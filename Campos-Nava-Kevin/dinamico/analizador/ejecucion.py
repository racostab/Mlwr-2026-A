"""Ejecución de la muestra en la VM y volcado de memoria.

Responsabilidad: una vez la VM está AISLADA y VERIFICADA (de eso se encargan
`aislamiento`/`verificacion`), aquí se sube la muestra, se ejecuta acotada por
tiempo BAJO strace (registro de syscalls), se vuelca su memoria (procdump →
gcore de respaldo) y se traen los resultados al host (strace.log + stdout/stderr
+ volcado). Lo orquesta `analizador_dinamico.py`.

Nota sobre ptrace: strace mantiene la muestra bajo ptrace y gcore/procdump
también lo usan, pero solo puede haber UN tracer a la vez; por eso se mata strace
(el kernel desengancha la muestra, que sigue viva) justo antes del volcado.

El volcado usa procdump (preferido) con gcore (de gdb) de respaldo; requiere
`ptrace_scope=0` y sudo NOPASSWD para el usuario `kali` (los deja listos, junto
con ambas herramientas, `dinamico/user_data/provision_kali.sh`).
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
    #
    # OJO: strace se lanza como comando SIMPLE en segundo plano (con `;`, NO con
    # `cd && strace &`). Un `&&` haría que bash backgroundee la lista en un
    # SUBSHELL que hereda el stdout del canal SSH y lo mantiene abierto mientras
    # strace viva → `ejecutar_remoto` se colgaría en `stdout.read()` esperando un
    # EOF que no llega (el runner nunca avanzaría al volcado). Redirigimos los tres
    # descriptores de strace (stdin←/dev/null, stdout/stderr→ficheros) para que no
    # retenga el canal; así bash sale tras `echo $!` y el read recibe su EOF.
    print(f"[*] Ejecutando la muestra bajo strace (la dejo correr {segundos}s antes del volcado)...")
    run = (
        f"cd {home}; strace -f -tt -T -o {dump_dir}/strace.log {remoto} "
        f"</dev/null >{dump_dir}/stdout.log 2>{dump_dir}/stderr.log & echo $!"
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

    # Dejar correr la muestra bajo strace para que se desempaquete y actúe, pero
    # VIGILANDO que siga viva en pasos de 1 s, en vez de dormir el tiempo completo
    # a ciegas (lo que hacía esperar en vano cuando la muestra sale antes). Así:
    #   - VIDA CORTA: en cuanto muere salimos del bucle (no hay memoria que volcar
    #     de un proceso ya terminado; strace.log igual capturó sus syscalls);
    #   - DAEMONIZA: si el PID original muere pero deja un hijo, seguimos al
    #     superviviente y será a él a quien volquemos.
    vivo = "si" if target else "no"
    fin = time.monotonic() + segundos
    while time.monotonic() < fin:
        time.sleep(min(1.0, max(0.0, fin - time.monotonic())))
        if target and ejecutar_remoto(
                client, f"kill -0 {target} 2>/dev/null && echo si || echo no",
                mostrar=False) == "si":
            vivo = "si"
            continue
        # El PID que seguíamos ya no está: ¿se daemonizó? Buscar superviviente.
        superv = ejecutar_remoto(client, f"pgrep -f {nombre} | head -n1", mostrar=False)
        if superv.isdigit():
            if superv != target:
                print(f"[*] El PID original no sigue vivo; uso el superviviente {superv}")
            target, vivo = superv, "si"
            continue
        # Nada vivo: muestra de vida corta. No tiene sentido seguir esperando.
        if vivo == "si":
            print("[!] La muestra terminó antes del tiempo pedido (vida corta); "
                  "strace.log tiene sus syscalls, pero no queda proceso que volcar.")
        vivo = "no"
        break

    # strace tiene la muestra bajo ptrace, y gcore/procdump también usan ptrace
    # (solo un tracer a la vez). Matamos strace: el kernel DESENGANCHA a la muestra
    # —que sigue viva— y se vacía/cierra strace.log, dejando el ptrace libre para
    # el volcado.
    #
    # SIGTERM no siempre termina a strace (puede quedar bloqueado en el detach del
    # tracee y seguir reteniendo el ptrace → gcore/procdump fallan con "only one
    # tracer"). Por eso escalamos: SIGTERM, breve espera y, si sigue vivo, SIGKILL.
    # Al morir el tracer el kernel desengancha a la muestra, que sigue viva (strace
    # no activa PTRACE_O_EXITKILL).
    if tracer:
        ejecutar_remoto(
            client,
            f"kill {tracer} 2>/dev/null; "
            f"for _ in 1 2 3; do kill -0 {tracer} 2>/dev/null || break; sleep 0.3; done; "
            f"kill -9 {tracer} 2>/dev/null; true",
            mostrar=False,
        )
        time.sleep(1)  # esperar a que el kernel complete el detach

    if vivo != "si":
        print("[!] No hay proceso vivo de la muestra; no se pudo volcar su memoria.")
    else:
        print(f"[*] Volcando memoria del PID {target} con procdump...")
        # procdump (Sysinternals para Linux) exige el PID con -p y el prefijo de
        # salida con -o; -n 1 escribe un solo volcado y -s 1 lo dispara tras 1s de
        # vida (no 10 por defecto). El volcado queda en {dump_dir}/dump_*.
        ejecutar_remoto(client, f"sudo -n procdump -s 1 -n 1 -p {target} -o {dump_dir}/dump 2>&1")
        # ¿Generó procdump algún volcado? Cuenta cualquier archivo del dump_dir que
        # NO sea uno de los logs (procdump no usa extensión .core/.dmp fija).
        hay_dump = ejecutar_remoto(
            client,
            f"ls -1 {dump_dir} 2>/dev/null | grep -vE '^(strace|stdout|stderr)\\.log$' | wc -l",
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
