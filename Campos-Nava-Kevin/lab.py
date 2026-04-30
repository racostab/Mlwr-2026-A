#!/usr/bin/env python3
"""Malware Lab — punto de entrada principal."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def usage():
    print("""
Uso: python3 lab.py <modulo> <comando> [args]

  docker  start | stop | restart | pause | resume | status | logs
  kali    start | stop | pause | resume  [vm_name]
  static  hash | file | strings | entropy | ssdeep  <ruta_local>

Ejemplos:
  python3 lab.py docker status
  python3 lab.py docker start
  python3 lab.py kali start
  python3 lab.py static hash    /tmp/muestra.exe
  python3 lab.py static file    /tmp/muestra.exe
  python3 lab.py static strings /tmp/muestra.exe
  python3 lab.py static entropy /tmp/muestra.exe
  python3 lab.py static ssdeep  /tmp/muestra.exe
""")


if len(sys.argv) < 3:
    usage()
    sys.exit(1)

modulo  = sys.argv[1]
comando = sys.argv[2]
args    = sys.argv[3:]

if modulo == "docker":
    import docker.docker as mgr
    cmds = {
        "start":   mgr.iniciar,
        "stop":    mgr.detener,
        "restart": mgr.reiniciar,
        "pause":   mgr.pausar,
        "resume":  mgr.reanudar,
        "status":  mgr.estado,
        "logs":    mgr.logs,
    }
    if comando not in cmds:
        print(f"[!] Comando desconocido: {comando}")
        usage()
        sys.exit(1)
    cmds[comando]()

elif modulo == "kali":
    from kali import api
    api.run(comando, *args)

elif modulo == "static":
    import os
    from docker.debian import (
        conectar, hash_archivo,
        file_archivo, strings_archivo, entropia_archivo, ssdeep_archivo,
    )
    from core.ssh import subir
    if not args:
        print("[!] Falta la ruta del archivo")
        usage()
        sys.exit(1)
    local = args[0]
    if not os.path.exists(local):
        print(f"[!] Archivo local no encontrado: {local}")
        sys.exit(1)
    remoto = f"/tmp/{os.path.basename(local)}"
    client = conectar()
    subir(client, local, remoto)
    if comando == "hash":
        hashes = hash_archivo(client, remoto)
        print(f"\nArchivo: {local}")
        for alg, val in hashes.items():
            print(f"  {alg:<8} {val}")
    elif comando == "file":
        resultado = file_archivo(client, remoto)
        print(f"\nArchivo: {local}")
        print(f"  {resultado}")
    elif comando == "strings":
        try:
            raw = input("Longitud mínima de cadena [4]: ").strip()
            min_len = int(raw) if raw else 4
        except ValueError:
            print("[!] Valor inválido, usando 4")
            min_len = 4
        resultado = strings_archivo(client, remoto, min_len)
        print(f"\n--- strings (min={min_len}) en {local} ---")
        print(resultado)
    elif comando == "entropy":
        resultado = entropia_archivo(client, remoto)
        print(f"\nArchivo: {local}")
        print(f"  Entropía: {resultado} bits/byte")
    elif comando == "ssdeep":
        resultado = ssdeep_archivo(client, remoto)
        print(f"\nArchivo: {local}")
        print(f"  ssdeep: {resultado}")
    else:
        print(f"[!] Comando desconocido: {comando}")
        usage()
        sys.exit(1)
    client.close()

else:
    print(f"[!] Módulo desconocido: {modulo}")
    usage()
    sys.exit(1)
