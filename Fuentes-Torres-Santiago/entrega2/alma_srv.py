#!/usr/bin/env python3
# ============================================================
#  alma_srv.py  —  Servidor del Laboratorio
#  Recibe comandos de clientes CLI y GUI
#  Controla VM, Docker y ejecuta análisis estático
#
#  Uso:
#    python alma_srv.py
#    python alma_srv.py --puerto 9999
#    python alma_srv.py --host 0.0.0.0 --puerto 9999
#
#  Protocolo:
#    Cliente envía: JSON con {accion, parametros}
#    Servidor responde: JSON con {status, resultado}
#
#  Acciones disponibles:
#    vm      → Controla VirtualBox
#    docker  → Controla Docker
#    analizar → Análisis estático de archivo
#    ping    → Verificar conexión
# ============================================================

import sys
import os
import socket
import json
import threading
import subprocess

# Agregar carpeta al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modulos.hashes       import calcular_hashes
from modulos.entropia     import calcular_entropia
from modulos.tipo_archivo import detectar_tipo
from modulos.cadenas      import extraer_cadenas
from modulos.ssdeep       import calcular_ssdeep

# ── Configuración ────────────────────────────────────────────
HOST    = "0.0.0.0"
PUERTO  = 9999
BUFFER  = 4096
MAX_CLI = 5
# ─────────────────────────────────────────────────────────────


# ── Acciones ─────────────────────────────────────────────────

def accion_ping(params):
    """Verifica que el servidor esté activo."""
    return {"status": "ok", "mensaje": "Servidor activo"}


def accion_vm(params):
    """Controla VirtualBox via VBoxManage."""
    cmd    = params.get("cmd")
    vm     = params.get("vm", "")
    salida = {}

    comandos = {
        "list":     ["VBoxManage", "list", "vms"],
        "start":    ["VBoxManage", "startvm", vm, "--type", "headless"],
        "stop":     ["VBoxManage", "controlvm", vm, "poweroff"],
        "pause":    ["VBoxManage", "controlvm", vm, "pause"],
        "resume":   ["VBoxManage", "controlvm", vm, "resume"],
        "status":   ["VBoxManage", "showvminfo", vm, "--machinereadable"],
        "snapshot": ["VBoxManage", "snapshot", vm, "take", params.get("nombre", "snap")],
    }

    if cmd not in comandos:
        return {"status": "error", "mensaje": f"Comando VM desconocido: {cmd}"}

    try:
        resultado = subprocess.run(
            comandos[cmd],
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "status":   "ok" if resultado.returncode == 0 else "error",
            "stdout":   resultado.stdout,
            "stderr":   resultado.stderr,
            "codigo":   resultado.returncode
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


def accion_docker(params):
    """Controla Docker."""
    cmd  = params.get("cmd")
    nombre = params.get("nombre", "ciber-docker")
    imagen = params.get("imagen", "debian:bookworm-slim")

    comandos = {
        "list":   ["docker", "ps", "-a"],
        "start":  ["docker", "start", nombre],
        "stop":   ["docker", "stop", nombre],
        "create": ["docker", "create", "-it", "--name", nombre, imagen, "/bin/bash"],
        "logs":   ["docker", "logs", nombre],
    }

    if cmd == "exec":
        comando_exec = params.get("comando", "whoami")
        comandos["exec"] = ["docker", "exec", nombre, "/bin/bash", "-c", comando_exec]

    if cmd not in comandos:
        return {"status": "error", "mensaje": f"Comando Docker desconocido: {cmd}"}

    try:
        resultado = subprocess.run(
            comandos[cmd],
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "status": "ok" if resultado.returncode == 0 else "error",
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
            "codigo": resultado.returncode
        }
    except Exception as e:
        return {"status": "error", "mensaje": str(e)}


def accion_analizar(params):
    """Ejecuta análisis estático completo de un archivo."""
    ruta = params.get("archivo")

    if not ruta or not os.path.isfile(ruta):
        return {"status": "error", "mensaje": f"Archivo no encontrado: {ruta}"}

    resultado = {}

    tipo     = detectar_tipo(ruta)
    hashes   = calcular_hashes(ruta)
    entropia = calcular_entropia(ruta)
    cadenas  = extraer_cadenas(ruta)
    ssdeep   = calcular_ssdeep(ruta)

    if tipo:
        resultado["tipo"] = tipo
    if hashes:
        resultado["hashes"] = hashes
    if entropia:
        resultado["entropia"] = entropia
    if cadenas:
        # Solo enviar primeras 50 cadenas para no saturar el buffer
        resultado["cadenas"] = {
            "total":   cadenas["total"],
            "muestra": cadenas["cadenas"][:50]
        }
    if ssdeep:
        resultado["ssdeep"] = ssdeep

    return {"status": "ok", "resultado": resultado}


# ── Mapa de acciones ─────────────────────────────────────────
ACCIONES = {
    "ping":     accion_ping,
    "vm":       accion_vm,
    "docker":   accion_docker,
    "analizar": accion_analizar,
}


# ── Manejo de cliente ─────────────────────────────────────────

def manejar_cliente(conn, addr):
    """Hilo que maneja cada cliente conectado."""
    print(f"[+] Cliente conectado: {addr[0]}:{addr[1]}")

    try:
        while True:
            # Recibir datos
            datos = b""
            while True:
                parte = conn.recv(BUFFER)
                if not parte:
                    break
                datos += parte
                if len(parte) < BUFFER:
                    break

            if not datos:
                break

            # Decodificar JSON
            try:
                mensaje = json.loads(datos.decode("utf-8"))
            except json.JSONDecodeError:
                respuesta = {"status": "error", "mensaje": "JSON invalido"}
                conn.sendall(json.dumps(respuesta).encode("utf-8"))
                continue

            accion  = mensaje.get("accion", "")
            params  = mensaje.get("parametros", {})

            print(f"[>] {addr[0]} → accion: {accion} | params: {params}")

            # Ejecutar acción
            if accion in ACCIONES:
                respuesta = ACCIONES[accion](params)
            else:
                respuesta = {"status": "error", "mensaje": f"Accion desconocida: {accion}"}

            # Enviar respuesta
            conn.sendall(json.dumps(respuesta).encode("utf-8"))

    except ConnectionResetError:
        print(f"[-] Cliente desconectado abruptamente: {addr}")
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Cliente desconectado: {addr[0]}:{addr[1]}")


# ── Servidor principal ────────────────────────────────────────

def iniciar_servidor(host=HOST, puerto=PUERTO):
    """Inicia el servidor y escucha conexiones."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        srv.bind((host, puerto))
    except OSError as e:
        print(f"[ERROR] No se pudo iniciar el servidor: {e}")
        print(f"[INFO]  Verifica que el puerto {puerto} este disponible.")
        sys.exit(1)

    srv.listen(MAX_CLI)
    print(f"[SERVIDOR] Escuchando en {host}:{puerto}")
    print(f"[SERVIDOR] Maximo de clientes: {MAX_CLI}")
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
        print("\n[SERVIDOR] Detenido por el usuario.")
    finally:
        srv.close()


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args  = sys.argv[1:]
    host  = HOST
    puerto = PUERTO

    i = 0
    while i < len(args):
        if args[i] == "--host" and i + 1 < len(args):
            host = args[i+1]
            i += 2
        elif args[i] == "--puerto" and i + 1 < len(args):
            try:
                puerto = int(args[i+1])
                i += 2
            except ValueError:
                print("[ERROR] Puerto debe ser un numero entero.")
                sys.exit(1)
        else:
            i += 1

    iniciar_servidor(host, puerto)