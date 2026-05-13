#!/usr/bin/env python3
# ============================================================
#  alma_clt.py  —  Cliente CLI del Laboratorio
#  Se conecta a alma_srv.py y envía comandos
#
#  Uso:
#    python alma_clt.py ping
#    python alma_clt.py vm list
#    python alma_clt.py vm start ciber
#    python alma_clt.py vm stop  ciber
#    python alma_clt.py docker list
#    python alma_clt.py docker exec whoami
#    python alma_clt.py analizar [ruta_archivo]
#    python alma_clt.py ejemplo
# ============================================================

import sys
import os
import socket
import json

# ── Configuración ────────────────────────────────────────────
SRV_HOST = "localhost"
SRV_PORT = 9999
BUFFER   = 4096
TIMEOUT  = 10
# ─────────────────────────────────────────────────────────────


def enviar_comando(accion, parametros={}):
    """
    Envía un comando al servidor y retorna la respuesta.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((SRV_HOST, SRV_PORT))

        mensaje = json.dumps({"accion": accion, "parametros": parametros})
        s.sendall(mensaje.encode("utf-8"))

        respuesta = b""
        while True:
            parte = s.recv(BUFFER)
            if not parte:
                break
            respuesta += parte
            if len(parte) < BUFFER:
                break

        s.close()
        return json.loads(respuesta.decode("utf-8"))

    except ConnectionRefusedError:
        print(f"[ERROR] No se pudo conectar al servidor {SRV_HOST}:{SRV_PORT}")
        print(f"[INFO]  Verifica que alma_srv.py este corriendo.")
        sys.exit(1)
    except socket.timeout:
        print(f"[ERROR] Timeout — el servidor no respondio.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def mostrar_respuesta(respuesta):
    """Muestra la respuesta del servidor de forma legible."""
    if respuesta.get("status") == "error":
        print(f"[ERROR] {respuesta.get('mensaje', 'Error desconocido')}")
        return

    # Ping
    if "mensaje" in respuesta:
        print(f"[OK] {respuesta['mensaje']}")
        return

    # VM / Docker — mostrar stdout
    if "stdout" in respuesta:
        if respuesta["stdout"]:
            print(respuesta["stdout"])
        if respuesta.get("stderr"):
            print(f"[STDERR] {respuesta['stderr']}")
        codigo = respuesta.get("codigo", 0)
        if codigo == 0:
            print("[OK] Comando ejecutado correctamente.")
        else:
            print(f"[ERROR] Codigo de salida: {codigo}")
        return

    # Análisis estático
    if "resultado" in respuesta:
        r = respuesta["resultado"]
        SEP = "=" * 60

        print(f"\n{SEP}")
        print(f"  RESULTADO DEL ANÁLISIS")
        print(SEP)

        if "tipo" in r:
            t = r["tipo"]
            print(f"\n  [TIPO]")
            print(f"  Tipo       : {t['tipo']}")
            print(f"  Descripcion: {t['descripcion']}")
            print(f"  Extension  : {t['extension']}")

        if "hashes" in r:
            h = r["hashes"]
            print(f"\n  [HASHES]")
            print(f"  MD5    : {h['md5']}")
            print(f"  SHA1   : {h['sha1']}")
            print(f"  SHA256 : {h['sha256']}")

        if "entropia" in r:
            e = r["entropia"]
            estado = "⚠ SOSPECHOSO" if e["sospechoso"] else "OK"
            print(f"\n  [ENTROPÍA]")
            print(f"  Valor  : {e['entropia']} / 8.0")
            print(f"  Nivel  : {e['nivel']}")
            print(f"  Estado : {estado}")

        if "cadenas" in r:
            c = r["cadenas"]
            print(f"\n  [CADENAS]")
            print(f"  Total  : {c['total']} encontradas")
            print(f"  Muestra:")
            for i, cadena in enumerate(c["muestra"][:10]):
                print(f"    {i+1:<4} {cadena}")
            if c["total"] > 10:
                print(f"    ... y {c['total'] - 10} mas.")

        if "ssdeep" in r:
            ss = r["ssdeep"]
            print(f"\n  [FUZZY HASH]")
            print(f"  Hash   : {ss['hash']}")
            print(f"  Tamano : {ss['tamano']} bytes")

        print(f"\n{SEP}\n")


def mostrar_ejemplos():
    """Ejecuta ejemplos de demostración."""
    print("[INFO] Ejecutando ejemplos...\n")

    print("── Ejemplo 1: ping ────────────────────────────")
    r = enviar_comando("ping")
    mostrar_respuesta(r)

    print("── Ejemplo 2: listar VMs ──────────────────────")
    r = enviar_comando("vm", {"cmd": "list"})
    mostrar_respuesta(r)

    print("── Ejemplo 3: listar contenedores ─────────────")
    r = enviar_comando("docker", {"cmd": "list"})
    mostrar_respuesta(r)


def mostrar_uso():
    print("""
 Uso: python alma_clt.py [accion] [argumentos]

 Acciones:
   ping                          Verifica conexion con servidor
   vm     list                   Lista todas las VMs
   vm     start  [nombre_vm]     Inicia una VM
   vm     stop   [nombre_vm]     Detiene una VM
   vm     pause  [nombre_vm]     Pausa una VM
   vm     resume [nombre_vm]     Reanuda una VM
   vm     status [nombre_vm]     Estado de una VM
   docker list                   Lista contenedores
   docker start  [nombre]        Inicia contenedor
   docker stop   [nombre]        Detiene contenedor
   docker exec   [comando]       Ejecuta comando en contenedor
   analizar [ruta]               Análisis estático de archivo
   ejemplo                       Ejecuta demos

 Ejemplos:
   python alma_clt.py ping
   python alma_clt.py vm list
   python alma_clt.py vm start ciber
   python alma_clt.py docker list
   python alma_clt.py docker exec whoami
   python alma_clt.py analizar hashes.py
""")


# ── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mostrar_uso()
        sys.exit(0)

    accion = args[0].lower()

    if accion == "ping":
        r = enviar_comando("ping")
        mostrar_respuesta(r)

    elif accion == "vm":
        if len(args) < 2:
            print("[ERROR] Especifica un comando VM.")
            mostrar_uso()
            sys.exit(1)
        cmd = args[1].lower()
        vm  = args[2] if len(args) > 2 else ""
        r   = enviar_comando("vm", {"cmd": cmd, "vm": vm})
        mostrar_respuesta(r)

    elif accion == "docker":
        if len(args) < 2:
            print("[ERROR] Especifica un comando Docker.")
            mostrar_uso()
            sys.exit(1)
        cmd     = args[1].lower()
        nombre  = args[2] if len(args) > 2 else "ciber-docker"
        comando = " ".join(args[2:]) if cmd == "exec" else ""
        r       = enviar_comando("docker", {
            "cmd":     cmd,
            "nombre":  nombre,
            "comando": comando
        })
        mostrar_respuesta(r)

    elif accion == "analizar":
        if len(args) < 2:
            print("[ERROR] Especifica un archivo.")
            mostrar_uso()
            sys.exit(1)
        ruta = args[1]
        print(f"[CLT] Enviando archivo al servidor: {ruta}")
        r = enviar_comando("analizar", {"archivo": ruta})
        mostrar_respuesta(r)

    elif accion == "ejemplo":
        mostrar_ejemplos()

    else:
        print(f"[ERROR] Accion desconocida: {accion}")
        mostrar_uso()
        sys.exit(1)