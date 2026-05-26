#!/usr/bin/env python3
"""Malware Lab — CLI cliente HTTP del engine. Kevin"""
import os
import subprocess
import sys

import requests

ENGINE_URL   = os.environ.get("ENGINE_URL", "http://localhost:8001")
COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "docker-compose.yml")


def usage():
    print(f"""
Uso: python3 lab.py <comando> [args]

  up                             levanta los contenedores del lab
  down                           destruye los contenedores (datos en volúmenes se conservan)

  upload  <ruta_local>           sube una muestra al engine, devuelve sha256
  list                           lista todas las muestras del historial
  hash    <sha256>
  file    <sha256>
  strings <sha256> [min_len]
  entropy <sha256>
  ssdeep  <sha256>
  exiftool <sha256>
  readelf  <sha256>
  analyze <ruta_local>           shorthand: upload + todos los análisis

Engine: {ENGINE_URL}  (override con ENGINE_URL=...)
""")


def _upload(path):
    with open(path, "rb") as f:
        r = requests.post(
            f"{ENGINE_URL}/samples",
            files={"file": (os.path.basename(path), f)},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()


def _get(path, **params):
    r = requests.get(f"{ENGINE_URL}{path}", params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def _print_kv(label, value):
    print(f"  {label:<10} {value}")


def _compose(*args):
    base = ["docker", "compose", "-f", COMPOSE_FILE]
    result = subprocess.run(base + list(args))
    sys.exit(result.returncode)


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd  = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "up":
        _compose("up", "-d", "--build")

    elif cmd == "down":
        _compose("down")

    elif cmd == "upload":
        if not args:
            usage(); sys.exit(1)
        meta = _upload(args[0])
        print(f"sha256:   {meta['sha256']}")
        print(f"filename: {meta['filename']}")
        print(f"size:     {meta['size']} B")

    elif cmd == "list":
        for s in _get("/samples"):
            print(f"  {s['sha256']}  {s['filename']:<30}  {s['size']:>10} B  {s['uploaded_at']}")

    elif cmd == "hash":
        if not args: usage(); sys.exit(1)
        for alg, val in _get(f"/samples/{args[0]}/hash").items():
            _print_kv(alg, val)

    elif cmd == "file":
        if not args: usage(); sys.exit(1)
        print(_get(f"/samples/{args[0]}/file")["file"])

    elif cmd == "strings":
        if not args: usage(); sys.exit(1)
        min_len = int(args[1]) if len(args) > 1 else 4
        for s in _get(f"/samples/{args[0]}/strings", min_len=min_len)["strings"]:
            print(s)

    elif cmd == "entropy":
        if not args: usage(); sys.exit(1)
        print(_get(f"/samples/{args[0]}/entropy")["entropy"], "bits/byte")

    elif cmd == "ssdeep":
        if not args: usage(); sys.exit(1)
        print(_get(f"/samples/{args[0]}/ssdeep")["ssdeep"])

    elif cmd == "exiftool":
        if not args: usage(); sys.exit(1)
        for key, val in _get(f"/samples/{args[0]}/exiftool").items():
            _print_kv(key, val)

    elif cmd == "readelf":
        if not args: usage(); sys.exit(1)
        print(_get(f"/samples/{args[0]}/readelf")["readelf"])

    elif cmd == "analyze":
        if not args: usage(); sys.exit(1)
        meta = _upload(args[0])
        sha  = meta["sha256"]
        print(f"\n[+] {meta['filename']} → {sha}\n")
        print("Hashes:")
        for alg, val in _get(f"/samples/{sha}/hash").items():
            _print_kv(alg, val)
        _print_kv("File:",    _get(f"/samples/{sha}/file")["file"])
        _print_kv("Entropy:", f"{_get(f'/samples/{sha}/entropy')['entropy']} bits/byte")
        _print_kv("SSDeep:",  _get(f"/samples/{sha}/ssdeep")["ssdeep"])
        print("\nExifTool:")
        for key, val in _get(f"/samples/{sha}/exiftool").items():
            _print_kv(key, val)
        print(f"\nUsa 'lab.py strings {sha}' para ver strings.")
        print(f"Usa 'lab.py readelf {sha}' para ver cabeceras ELF.")

    else:
        usage(); sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"[!] HTTP {e.response.status_code}: {e.response.text}")
        sys.exit(1)
    except requests.ConnectionError:
        print(f"[!] No se pudo conectar al engine ({ENGINE_URL}). ¿`docker compose up -d`?")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"[!] {e}")
        sys.exit(1)
