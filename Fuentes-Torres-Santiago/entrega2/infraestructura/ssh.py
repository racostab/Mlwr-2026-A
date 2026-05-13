#!/usr/bin/env python3
# ============================================================
#  programa_ssh.py  —  Control SSH via API (subprocess)
#  Equivalente Python de ssh_login.bat y ssh_cmd.bat
#
#  Uso:
#    python programa_ssh.py login
#    python programa_ssh.py cmd whoami
#    python programa_ssh.py cmd df -h
#    python programa_ssh.py ejemplo
# ============================================================

import subprocess
import sys

# ── Configuración ────────────────────────────────────────────
DEFAULT_HOST = "ciber-vm"
# ─────────────────────────────────────────────────────────────


def ssh_login(host=DEFAULT_HOST):
    """Abre sesión SSH interactiva hacia la VM."""
    print(f"[SSH] Conectando a {host}...")
    print("[SSH] Escribe 'exit' para cerrar la sesion.\n")

    resultado = subprocess.run(
        ["ssh", host],
        check=False
    )

    if resultado.returncode == 0:
        print("\n[OK] Sesion cerrada correctamente.")
    else:
        print("\n[ERROR] No se pudo conectar.")
        print(f"[INFO]  Verifica que la VM este encendida y el alias '{host}' configurado.")


def ssh_cmd(comando, host=DEFAULT_HOST):
    """Ejecuta un comando remoto y captura su salida."""
    if not comando:
        print("[ERROR] Debes especificar un comando.")
        return

    print(f"[SSH] Ejecutando en {host}: {comando}\n")

    resultado = subprocess.run(
        ["ssh", host, comando],
        capture_output=True,
        text=True,
        check=False
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(f"[STDERR] {resultado.stderr}")

    if resultado.returncode == 0:
        print("[OK] Comando ejecutado correctamente.")
    else:
        print(f"[ERROR] El comando termino con codigo {resultado.returncode}.")


def ssh_cmd_params(comando, parametros, host=DEFAULT_HOST):
    """Ejecuta un comando remoto con parámetros separados."""
    cmd_completo = f"{comando} {parametros}"
    print(f"[SSH] Ejecutando en {host}: {cmd_completo}\n")

    resultado = subprocess.run(
        ["ssh", host, cmd_completo],
        capture_output=True,
        text=True,
        check=False
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(f"[STDERR] {resultado.stderr}")

    if resultado.returncode == 0:
        print("[OK] Comando ejecutado correctamente.")
    else:
        print(f"[ERROR] El comando termino con codigo {resultado.returncode}.")


def mostrar_uso():
    print("""
 Uso: python ssh.py [accion] [argumentos]

 Acciones:
   login                    Abre sesion interactiva
   login [host]             Abre sesion en host especifico
   cmd [comando]            Ejecuta comando remoto
   cmd [host] [comando]     Ejecuta comando en host especifico
   ejemplo                  Muestra ejemplos de uso

 Ejemplos:
   python ssh.py login
   python ssh.py login ciber-vm
   python ssh.py cmd whoami
   python ssh.py cmd df -h
   python ssh.py cmd ciber-vm uname -a
""")


def mostrar_ejemplos():
    print("[INFO] Ejecutando ejemplos de demostracion...\n")

    print("── Ejemplo 1: whoami ──────────────────────────")
    ssh_cmd("whoami")

    print("── Ejemplo 2: uname -a ────────────────────────")
    ssh_cmd_params("uname", "-a")

    print("── Ejemplo 3: df -h ───────────────────────────")
    ssh_cmd_params("df", "-h")

    print("── Ejemplo 4: ls /home ────────────────────────")
    ssh_cmd_params("ls", "/home")


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mostrar_uso()
        sys.exit(0)

    accion = args[0].lower()

    if accion == "login":
        host = args[1] if len(args) > 1 else DEFAULT_HOST
        ssh_login(host)

    elif accion == "cmd":
        if len(args) < 2:
            print("[ERROR] Especifica un comando.")
            mostrar_uso()
            sys.exit(1)

        # Detectar si el segundo argumento es un host conocido
        if args[1] == DEFAULT_HOST or (len(args) > 2 and "@" in args[1]):
            host = args[1]
            comando = " ".join(args[2:])
        else:
            host = DEFAULT_HOST
            comando = " ".join(args[1:])

        ssh_cmd(comando, host)

    elif accion == "ejemplo":
        mostrar_ejemplos()

    else:
        print(f"[ERROR] Accion desconocida: {accion}")
        mostrar_uso()
        sys.exit(1)