#!/usr/bin/env python3
# ============================================================
#  alma_srv.py  —  Servidor del Laboratorio
#  Prototipo 1 — Flujo automatizado Docker
#
#  Uso:
#    python alma_srv.py
#    python alma_srv.py --puerto 9999
#
#  Flujo automático al recibir "analizar":
#    1. Verificar Docker
#    2. Verificar imagen lab-malware
#    3. Levantar contenedor si no está corriendo
#    4. Copiar archivo al contenedor
#    5. Ejecutar análisis dentro del contenedor
#    6. Regresar resultados al cliente
#    7. Limpiar archivo del contenedor
# ============================================================

import sys
import os
import socket
import json
import threading
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from modulos.hashes       import calcular_hashes
from modulos.entropia     import calcular_entropia
from modulos.tipo_archivo import detectar_tipo
from modulos.cadenas      import extraer_cadenas
from modulos.ssdeep       import calcular_ssdeep

# ── Helpers Docker ────────────────────────────────────────────

def _run(cmd, capture=True):
    """Ejecuta un comando y retorna el resultado."""
    return subprocess.run(
       cmd,
        capture_output=capture,
        text=True,
        check=False,
        encoding="utf-8",     
        errors="replace"  
    )


def docker_verificar():
    """Verifica que Docker esté instalado y corriendo."""
    r = _run(["docker", "info"])
    return r.returncode == 0


def docker_imagen_existe():
    """Verifica si la imagen lab-malware existe."""
    r = _run(["docker", "image", "inspect", config.DOCKER_IMAGEN])
    return r.returncode == 0


def docker_contenedor_existe():
    """Verifica si el contenedor existe."""
    r = _run(["docker", "inspect", config.DOCKER_CONTENEDOR])
    return r.returncode == 0


def docker_contenedor_corriendo():
    """Verifica si el contenedor está corriendo."""
    r = _run([
        "docker", "inspect",
        "--format={{.State.Running}}",
        config.DOCKER_CONTENEDOR
    ])
    return r.stdout.strip() == "true"


def docker_asegurar_contenedor():
    """
    Asegura que el contenedor esté listo.
    Lo crea o inicia según sea necesario.
    Retorna (ok, mensaje)
    """
    if not docker_verificar():
        return False, "Docker no está corriendo"

    if not docker_imagen_existe():
        return False, f"Imagen '{config.DOCKER_IMAGEN}' no encontrada. Ejecuta: docker build -t {config.DOCKER_IMAGEN} ."

    if not docker_contenedor_existe():
        print(f"[DOCKER] Creando contenedor {config.DOCKER_CONTENEDOR}...")
        r = _run([
            "docker", "create", "-it",
            "--name", config.DOCKER_CONTENEDOR,
            config.DOCKER_IMAGEN,
            "/bin/bash"
        ])
        if r.returncode != 0:
            return False, f"Error al crear contenedor: {r.stderr}"

    if not docker_contenedor_corriendo():
        print(f"[DOCKER] Iniciando contenedor {config.DOCKER_CONTENEDOR}...")
        r = _run(["docker", "start", config.DOCKER_CONTENEDOR])
        if r.returncode != 0:
            return False, f"Error al iniciar contenedor: {r.stderr}"

    return True, "Contenedor listo"


def docker_copiar_archivo(ruta_local):
    """Copia un archivo de Windows al contenedor."""
    nombre   = os.path.basename(ruta_local)
    ruta_dst = f"{config.DOCKER_DIR_MUESTRAS}/{nombre}"

    r = _run([
        "docker", "cp",
        ruta_local,
        f"{config.DOCKER_CONTENEDOR}:{ruta_dst}"
    ])
    return r.returncode == 0, ruta_dst


def docker_ejecutar(comando):
    """Ejecuta un comando dentro del contenedor."""
    return _run([
        "docker", "exec",
        config.DOCKER_CONTENEDOR,
        "/bin/bash", "-c", comando
    ])


def docker_eliminar_archivo(ruta_contenedor):
    """Elimina un archivo del contenedor."""
    _run(["docker", "exec", config.DOCKER_CONTENEDOR,
          "/bin/bash", "-c", f"rm -f {ruta_contenedor}"])


# ── Acciones ─────────────────────────────────────────────────

def accion_ping(params):
    return {"status": "ok", "mensaje": "Servidor activo"}


def accion_vm(params):
    """Controla VirtualBox via VBoxManage."""
    cmd  = params.get("cmd")
    vm   = params.get("vm", "")

    comandos = {
        "list":     ["VBoxManage", "list", "vms"],
        "start":    ["VBoxManage", "startvm", vm, "--type", "headless"],
        "stop":     ["VBoxManage", "controlvm", vm, "poweroff"],
        "pause":    ["VBoxManage", "controlvm", vm, "pause"],
        "resume":   ["VBoxManage", "controlvm", vm, "resume"],
        "status":   ["VBoxManage", "showvminfo", vm, "--machinereadable"],
        "snapshot": ["VBoxManage", "snapshot", vm, "take",
                     params.get("nombre", "snap")],
    }

    if cmd not in comandos:
        return {"status": "error", "mensaje": f"Comando VM desconocido: {cmd}"}

    try:
        r = _run(comandos[cmd])
        return {
            "status": "ok" if r.returncode == 0 else "error",
            "stdout": r.stdout,
            "stderr": r.stderr,
            "codigo": r.returncode
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


def accion_docker(params):
    """Controla Docker."""
    cmd    = params.get("cmd")
    nombre = params.get("nombre", config.DOCKER_CONTENEDOR)
    imagen = params.get("imagen", config.DOCKER_IMAGEN)

    comandos = {
        "list":   ["docker", "ps", "-a"],
        "start":  ["docker", "start", nombre],
        "stop":   ["docker", "stop", nombre],
        "create": ["docker", "create", "-it", "--name", nombre,
                   imagen, "/bin/bash"],
        "logs":   ["docker", "logs", nombre],
    }

    if cmd == "exec":
        cmd_exec = params.get("comando", "whoami")
        comandos["exec"] = [
            "docker", "exec", nombre, "/bin/bash", "-c", cmd_exec
        ]

    if cmd not in comandos:
        return {"status": "error", "mensaje": f"Comando Docker desconocido: {cmd}"}

    try:
        r = _run(comandos[cmd])
        return {
            "status": "ok" if r.returncode == 0 else "error",
            "stdout": r.stdout,
            "stderr": r.stderr,
            "codigo": r.returncode
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


def accion_analizar(params):
    """Flujo completo de análisis estático en Docker."""
    ruta = params.get("archivo")

    if not ruta:
        return {"status": "error", "mensaje": "No se especificó archivo"}

    # Resolver ruta relativa desde experimentos/
    if not os.path.isabs(ruta):
        ruta_exp = os.path.join(config.EXPERIMENTOS_DIR, ruta)
        if os.path.isfile(ruta_exp):
            ruta = ruta_exp

    if not os.path.isfile(ruta):
        return {"status": "error", "mensaje": f"Archivo no encontrado: {ruta}"}

    print(f"[SRV] Analizando: {ruta} | modo: docker")
    return _analizar_docker(ruta)


def _analizar_docker(ruta):
    """Análisis estático dentro del contenedor Docker."""

    # 1. Asegurar contenedor
    ok, msg = docker_asegurar_contenedor()
    if not ok:
        return {"status": "error", "mensaje": msg}
    print(f"[DOCKER] {msg}")

    # 2. Copiar archivo al contenedor
    ok, ruta_contenedor = docker_copiar_archivo(ruta)
    if not ok:
        return {"status": "error",
                "mensaje": f"No se pudo copiar archivo al contenedor"}
    print(f"[DOCKER] Archivo copiado a: {ruta_contenedor}")

    # 3. Ejecutar análisis dentro del contenedor
    resultado = {}

    # Tipo de archivo con comando 'file'
    print("[DOCKER] Ejecutando: file")
    r = docker_ejecutar(f"file {ruta_contenedor}")
    if r.returncode == 0:
        resultado["tipo_file"] = r.stdout.strip()

    # Exiftool
    print("[DOCKER] Ejecutando: exiftool")
    r = docker_ejecutar(f"exiftool {ruta_contenedor}")
    if r.returncode == 0:
        resultado["exiftool"] = r.stdout.strip()

    # Strings
    print("[DOCKER] Ejecutando: strings")
    r = docker_ejecutar(f"strings {ruta_contenedor} | head -50")
    if r.returncode == 0:
        resultado["strings"] = r.stdout.strip().split("\n")

    # ssdeep nativo
    print("[DOCKER] Ejecutando: ssdeep")
    r = docker_ejecutar(f"ssdeep {ruta_contenedor}")
    if r.returncode == 0:
        resultado["ssdeep_nativo"] = r.stdout.strip()

    # Análisis Python (hashes + entropía)
    print("[DOCKER] Ejecutando: análisis Python")
    r = docker_ejecutar(
        f"python3 {config.DOCKER_DIR_LAB}/laboratorio.py analizar {ruta_contenedor} 2>/dev/null"
    )
    if r.returncode == 0:
        resultado["laboratorio"] = r.stdout.strip()

    # 4. Limpiar archivo del contenedor
    docker_eliminar_archivo(ruta_contenedor)
    print(f"[DOCKER] Archivo eliminado del contenedor.")

    return {"status": "ok", "modo": "docker", "resultado": resultado}


# ── Mapa de acciones ─────────────────────────────────────────
ACCIONES = {
    "ping":     accion_ping,
    "vm":       accion_vm,
    "docker":   accion_docker,
    "analizar": accion_analizar,
}


# ── Manejo de cliente ─────────────────────────────────────────

def manejar_cliente(conn, addr):
    print(f"[+] Cliente conectado: {addr[0]}:{addr[1]}")
    try:
        while True:
            datos = b""
            while True:
                parte = conn.recv(config.BUFFER)
                if not parte:
                    break
                datos += parte
                if len(parte) < config.BUFFER:
                    break

            if not datos:
                break

            try:
                mensaje = json.loads(datos.decode("utf-8"))
            except json.JSONDecodeError:
                conn.sendall(json.dumps(
                    {"status": "error", "mensaje": "JSON invalido"}
                ).encode("utf-8"))
                continue

            accion = mensaje.get("accion", "")
            params = mensaje.get("parametros", {})
            print(f"[>] {addr[0]} → accion: {accion} | params: {params}")

            if accion in ACCIONES:
                respuesta = ACCIONES[accion](params)
            else:
                respuesta = {"status": "error",
                             "mensaje": f"Accion desconocida: {accion}"}

            conn.sendall(json.dumps(respuesta).encode("utf-8"))

    except ConnectionResetError:
        print(f"[-] Cliente desconectado abruptamente: {addr}")
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Cliente desconectado: {addr[0]}:{addr[1]}")


# ── Servidor principal ────────────────────────────────────────

def iniciar_servidor(host=config.SRV_HOST, puerto=config.SRV_PORT):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        srv.bind((host, puerto))
    except OSError as e:
        print(f"[ERROR] No se pudo iniciar el servidor: {e}")
        print(f"[INFO]  Puerto {puerto} puede estar en uso.")
        sys.exit(1)

    srv.listen(5)
    print(f"[SERVIDOR] Escuchando en {host}:{puerto}")
    print(f"[SERVIDOR] Modo default: {config.MODO_DEFAULT}")
    print(f"[SERVIDOR] Experimentos: {config.EXPERIMENTOS_DIR}")
    print(f"[SERVIDOR] Presiona Ctrl+C para detener.\n")

    try:
        while True:
            conn, addr = srv.accept()
            hilo = threading.Thread(
                target=manejar_cliente,
                args=(conn, addr),
                daemon=True
            )
            hilo.start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Detenido.")
    finally:
        srv.close()


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args   = sys.argv[1:]
    host   = config.SRV_HOST
    puerto = config.SRV_PORT

    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i+1]; i += 2
        elif args[i] == "--puerto" and i + 1 < len(args):
            try:
                puerto = int(args[i+1]); i += 2
            except ValueError:
                print("[ERROR] Puerto debe ser numero entero.")
                sys.exit(1)
        else:
            i += 1

    iniciar_servidor(host, puerto)