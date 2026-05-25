#!/usr/bin/env python3
# ============================================================
#  alma_clt.py  —  Cliente CLI del Laboratorio
#  Interfaz simplificada — solo archivo y tipo de análisis
#
#  Uso:
#    python alma_clt.py analizar [archivo]
#    python alma_clt.py analizar [archivo] --modo docker
#    python alma_clt.py vm      [cmd] [vm]
#    python alma_clt.py docker  [cmd]
#    python alma_clt.py ping
# ============================================================

import sys
import os
import socket
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


def enviar_comando(accion, parametros={}):
    """Envía un comando al servidor y retorna la respuesta."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(config.TIMEOUT)
        s.connect((config.SRV_HOST, config.SRV_PORT))

        s.sendall(json.dumps(
            {"accion": accion, "parametros": parametros}
        ).encode("utf-8"))

        respuesta = b""
        while True:
            parte = s.recv(config.BUFFER)
            if not parte:
                break
            respuesta += parte
            if len(parte) < config.BUFFER:
                break

        s.close()
        return json.loads(respuesta.decode("utf-8"))

    except ConnectionRefusedError:
        print(f"[ERROR] No se pudo conectar al servidor.")
        print(f"[INFO]  Verifica que alma_srv.py este corriendo.")
        sys.exit(1)
    except socket.timeout:
        print(f"[ERROR] Timeout — el servidor no respondio.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def mostrar_respuesta(respuesta):
    """Muestra la respuesta del servidor."""
    if respuesta.get("status") == "error":
        print(f"[ERROR] {respuesta.get('mensaje', 'Error desconocido')}")
        return

    if "mensaje" in respuesta:
        print(f"[OK] {respuesta['mensaje']}")
        return

    if "stdout" in respuesta:
        if respuesta["stdout"]:
            print(respuesta["stdout"])
        if respuesta.get("stderr"):
            print(f"[STDERR] {respuesta['stderr']}")
        return

    if "resultado" in respuesta:
        r    = respuesta["resultado"]
        modo = respuesta.get("modo", "?")
        SEP  = "=" * 60

        print(f"\n{SEP}")
        print(f"  RESULTADO — modo: {modo.upper()}")
        print(SEP)

        # Resultados modo local
        if "tipo" in r:
            t = r["tipo"]
            print(f"\n  [TIPO]")
            print(f"  {t['tipo']} — {t['descripcion']} ({t['extension']})")

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
            print(f"  {e['entropia']} / 8.0 — {e['nivel']} — {estado}")

        if "cadenas" in r:
            c = r["cadenas"]
            print(f"\n  [CADENAS] {c['total']} encontradas")
            for i, s in enumerate(c["muestra"][:10]):
                print(f"    {i+1:<4} {s}")
            if c["total"] > 10:
                print(f"    ... y {c['total'] - 10} mas.")

        if "ssdeep" in r:
            ss = r["ssdeep"]
            print(f"\n  [FUZZY HASH]")
            print(f"  {ss['hash']}")

        # Resultados modo docker
        if "tipo_file" in r:
            print(f"\n  [FILE]")
            print(f"  {r['tipo_file']}")

        if "exiftool" in r:
            print(f"\n  [EXIFTOOL]")
            for linea in r["exiftool"].split("\n")[:15]:
                print(f"  {linea}")

        if "strings" in r:
            print(f"\n  [STRINGS] (primeras 10)")
            for i, s in enumerate(r["strings"][:10]):
                print(f"  {i+1:<4} {s}")

        if "ssdeep_nativo" in r:
            print(f"\n  [SSDEEP NATIVO]")
            print(f"  {r['ssdeep_nativo']}")

        if "laboratorio" in r:
            print(f"\n  [ANÁLISIS PYTHON]")
            print(r["laboratorio"])

        print(f"\n{SEP}\n")


def mostrar_uso():
    print(f"""
 Uso: python alma_clt.py [accion] [argumentos]

 Acciones:
   analizar [archivo]         Análisis estático en Docker
   vm       [cmd] [nombre]    Controla VirtualBox
   docker   [cmd] [nombre]    Controla Docker
   ping                       Verifica conexión

 Ejemplos:
   python alma_clt.py analizar malware.exe
   python alma_clt.py analizar experimentos/muestra.txt
   python alma_clt.py vm list
   python alma_clt.py vm start ciber
   python alma_clt.py docker list
   python alma_clt.py ping
   analizar-dir [carpeta]     Analiza todos los archivos de una carpeta
""")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        mostrar_uso()
        sys.exit(0)

    accion = args[0].lower()

    if accion == "ping":
        mostrar_respuesta(enviar_comando("ping"))

    elif accion == "analizar":
        if len(args) < 2:
            print("[ERROR] Especifica un archivo.")
            mostrar_uso()
            sys.exit(1)

        archivo = args[1]

        print(f"[CLT] Archivo : {archivo}")
        print(f"[CLT] Modo    : docker")

        mostrar_respuesta(enviar_comando("analizar", {
            "archivo": archivo,
            "modo":    "docker"
        }))

    elif accion == "vm":
        if len(args) < 2:
            print("[ERROR] Especifica un comando VM.")
            mostrar_uso()
            sys.exit(1)
        cmd = args[1].lower()
        vm  = args[2] if len(args) > 2 else config.VM_NOMBRE
        mostrar_respuesta(enviar_comando("vm", {"cmd": cmd, "vm": vm}))

    elif accion == "docker":
        if len(args) < 2:
            print("[ERROR] Especifica un comando Docker.")
            mostrar_uso()
            sys.exit(1)
        cmd     = args[1].lower()
        nombre  = args[2] if len(args) > 2 else config.DOCKER_CONTENEDOR
        comando = " ".join(args[2:]) if cmd == "exec" else ""
        mostrar_respuesta(enviar_comando("docker", {
            "cmd":     cmd,
            "nombre":  nombre,
            "comando": comando
        }))
        
    elif accion == "analizar-dir":
        if len(args) < 2:
            print("[ERROR] Especifica una carpeta.")
            mostrar_uso()
            sys.exit(1)

        carpeta = args[1]

        if not os.path.isabs(carpeta):
            carpeta_exp = os.path.join(config.EXPERIMENTOS_DIR, carpeta)
            if os.path.isdir(carpeta_exp):
                carpeta = carpeta_exp

        if not os.path.isdir(carpeta):
            print(f"[ERROR] Carpeta no encontrada: {carpeta}")
            sys.exit(1)

        archivos = [
            f for f in os.listdir(carpeta)
            if os.path.isfile(os.path.join(carpeta, f))
        ]

        if not archivos:
            print(f"[ERROR] No hay archivos en: {carpeta}")
            sys.exit(1)

        print(f"[CLT] Carpeta  : {carpeta}")
        print(f"[CLT] Archivos : {len(archivos)} encontrados")
        print(f"[CLT] Modo     : docker\n")

        # ── Loop de análisis ─────────────────────────────────────
        hashes_ssdeep = {}

        for i, archivo in enumerate(archivos):
            ruta = os.path.join(carpeta, archivo)
            print(f"[{i+1}/{len(archivos)}] Analizando: {archivo}")
            print("-" * 40)
            respuesta = enviar_comando("analizar", {
                "archivo": ruta,
                "modo":    "docker"
            })
            mostrar_respuesta(respuesta)

            # Guardar ssdeep para comparación final
            if respuesta.get("status") == "ok":
                r = respuesta.get("resultado", {})
                if "ssdeep_nativo" in r:
                    hashes_ssdeep[archivo] = r["ssdeep_nativo"]
                elif "ssdeep" in r:
                    hashes_ssdeep[archivo] = r["ssdeep"]["hash"]

        # ── Comparación ssdeep al final ───────────────────────────
        if len(hashes_ssdeep) >= 2:
            from modulos.ssdeep import calcular_ssdeep, comparar

            SEP = "=" * 60
            print(f"\n{SEP}")
            print(f"  COMPARACIÓN DE SIMILITUD (SSDEEP)")
            print(f"  Archivos comparados: {len(hashes_ssdeep)}")
            print(SEP)

            archivos_lista = list(hashes_ssdeep.keys())
            encontrados    = False

            for i in range(len(archivos_lista)):
                for j in range(i + 1, len(archivos_lista)):
                    a1  = archivos_lista[i]
                    a2  = archivos_lista[j]
                    r1  = calcular_ssdeep(os.path.join(carpeta, a1))
                    r2  = calcular_ssdeep(os.path.join(carpeta, a2))
                    sim = comparar(r1, r2)

                    encontrados = True
                    if sim >= 80:
                        alerta = "⚠ MUY SIMILARES — posible variante"
                    elif sim >= 50:
                        alerta = "~ PARCIALMENTE SIMILARES"
                    else:
                        alerta = "OK — diferentes"

                    print(f"\n  {a1}  vs  {a2}")
                    print(f"  Similitud: {sim}%  —  {alerta}")

            if not encontrados:
                print("\n  Sin archivos para comparar.")
            print(f"\n{SEP}\n")
        else:
            print("\n[INFO] Se necesitan al menos 2 archivos para comparar similitud.\n")
            if len(args) < 2:
                print("[ERROR] Especifica una carpeta.")
                mostrar_uso()
                sys.exit(1)

            carpeta = args[1]

            # Si no es ruta absoluta, buscar en experimentos/
            if not os.path.isabs(carpeta):
                carpeta_exp = os.path.join(config.EXPERIMENTOS_DIR, carpeta)
                if os.path.isdir(carpeta_exp):
                    carpeta = carpeta_exp

            if not os.path.isdir(carpeta):
                print(f"[ERROR] Carpeta no encontrada: {carpeta}")
                sys.exit(1)

            archivos = [
                f for f in os.listdir(carpeta)
                if os.path.isfile(os.path.join(carpeta, f))
            ]

            if not archivos:
                print(f"[ERROR] No hay archivos en: {carpeta}")
                sys.exit(1)

            print(f"[CLT] Carpeta  : {carpeta}")
            print(f"[CLT] Archivos : {len(archivos)} encontrados")
            print(f"[CLT] Modo     : docker\n")

            # Guardar hashes ssdeep para comparación final

    else:
        print(f"[ERROR] Accion desconocida: {accion}")
        mostrar_uso()
        sys.exit(1)