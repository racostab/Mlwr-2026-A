#!/usr/bin/env python3
"""Descarga los binarios botnet ELF Intel referenciados en el catálogo.

Complemento de `build_dataset.py`: ese cataloga METADATOS; este baja los
binarios reales desde MalwareBazaar (abuse.ch), filtrando solo arquitectura
Intel (x86 / x86-64 / i686 / i586).

SEGURIDAD — esto descarga malware funcional:
  * Cada muestra se guarda como ZIP CIFRADO (password de abuse.ch: "infected").
    El script NUNCA lo extrae. Lo descomprimes tú DENTRO de la VM aislada.
  * Destino por defecto: samples/quarantine/ (samples/ está en .gitignore).
  * No ejecutes nada de aquí en tu host. Solo en la VM con red host-only y
    snapshot previo.

Uso:
    export MB_AUTH_KEY=<tu-key>                 # gratis en https://auth.abuse.ch/

    # 1) genera primero el catálogo de metadatos:
    python3 dataset/build_dataset.py --families Mirai Gafgyt Tsunami

    # 2) baja las muestras Intel del catálogo (por defecto, máx. 10):
    python3 dataset/fetch_samples.py --limit 10

    # o salta el catálogo y consulta familias al vuelo:
    python3 dataset/fetch_samples.py --families Mirai --limit 5
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API_URL = "https://mb-api.abuse.ch/api/v1/"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Tags de arquitectura Intel en MalwareBazaar.
INTEL_ARCH = {"x86", "x86-64", "x86_64", "i686", "i586", "i386", "intel"}

# Tags de arquitecturas NO Intel. MalwareBazaar rara vez etiqueta la arch, así
# que en vez de exigir un tag Intel (deja pasar ~29), descartamos solo lo que
# DICE ser otra arch y aceptamos lo no etiquetado. La arquitectura real se
# confirma luego en la VM con `file`/`readelf -h`.
NON_INTEL_ARCH = {"arm", "aarch64", "mips", "mipsel", "mips64", "powerpc",
                  "ppc", "ppc64", "sparc", "m68k", "sh4", "riscv"}

# Password con el que abuse.ch cifra TODOS los ZIP de muestras.
ZIP_PASSWORD = b"infected"

# Mismas familias por defecto que build_dataset.py.
DEFAULT_FAMILIES = ["Mirai", "Gafgyt", "Tsunami", "XorDDoS"]

AUTH_ERRORS = {"unauthorized", "illegal_auth_key", "unknown_auth_key", "auth_required"}


class AuthError(RuntimeError):
    """La API rechazó la petición por Auth-Key ausente o inválida."""


def is_intel_elf(entry):
    """True si la entrada es un ELF candidato a Intel.

    Filtro relajado: aceptamos el ELF salvo que sus tags declaren explícitamente
    otra arquitectura (ARM, MIPS, PowerPC...). Los ELF sin tag de arch pasan y se
    verifican con `file`/`readelf` ya descomprimidos en la VM.
    """
    if (entry.get("file_type") or "").lower() != "elf":
        return False
    tags = {t.lower() for t in (entry.get("tags") or [])}
    if tags & NON_INTEL_ARCH:
        return False
    return True


def from_catalog(json_path):
    """Saca las muestras Intel del catálogo JSON generado por build_dataset.py."""
    if not os.path.exists(json_path):
        return None
    with open(json_path, encoding="utf-8") as f:
        samples = json.load(f).get("samples", [])
    return [s for s in samples if is_intel_elf(s)]


def query_families(session, auth_key, families, per_family):
    """Consulta MalwareBazaar por familia y devuelve solo los ELF Intel."""
    out = []
    for family in families:
        resp = session.post(
            API_URL,
            data={"query": "get_siginfo", "signature": family, "limit": str(per_family)},
            headers={"Auth-Key": auth_key} if auth_key else {},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        status = payload.get("query_status")
        if status in AUTH_ERRORS:
            raise AuthError(status)
        if status != "ok":
            print(f"  ! '{family}': sin resultados ({status})", file=sys.stderr)
            continue
        intel = [e for e in payload.get("data", []) if is_intel_elf(e)]
        print(f"  {family:<12} {len(intel):>3} muestras Intel ELF")
        out.extend(intel)
        time.sleep(1)
    return out


def download_sample(session, auth_key, sha256, dest_dir):
    """Baja una muestra como ZIP cifrado. No la extrae. Devuelve la ruta o None."""
    dest = os.path.join(dest_dir, f"{sha256}.zip")
    if os.path.exists(dest):
        return dest, "ya estaba"

    resp = session.post(
        API_URL,
        data={"query": "get_file", "sha256_hash": sha256},
        headers={"Auth-Key": auth_key} if auth_key else {},
        timeout=120,
    )
    # La API devuelve el ZIP binario en caso de éxito, o JSON si hay error.
    ctype = resp.headers.get("Content-Type", "")
    if "application/json" in ctype or "text/" in ctype:
        try:
            status = resp.json().get("query_status", "error")
        except ValueError:
            status = "respuesta_no_zip"
        if status in AUTH_ERRORS:
            raise AuthError(status)
        return None, status

    with open(dest, "wb") as f:
        f.write(resp.content)
    return dest, "descargada"


def write_manifest(path, rows):
    """Escribe el inventario de lo descargado (qué hay en cuarentena)."""
    fields = ["familia", "sha256", "procesador", "file_name", "file_size",
              "zip_path", "estado", "url_origen"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Descarga binarios botnet ELF Intel desde MalwareBazaar (cifrados).",
    )
    parser.add_argument(
        "--families", nargs="+", metavar="FAMILIA",
        help="consultar estas familias al vuelo en vez de leer el catálogo JSON",
    )
    parser.add_argument(
        "--catalog", default=os.path.join(HERE, "botnet_elf.json"),
        help="catálogo JSON de build_dataset.py (def: dataset/botnet_elf.json)",
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="máximo de binarios a descargar en total (def: 10)",
    )
    parser.add_argument(
        "--dest", default=os.path.join(REPO, "samples", "quarantine"),
        help="carpeta de cuarentena (def: samples/quarantine/, ya en .gitignore)",
    )
    parser.add_argument(
        "--auth-key", default=os.environ.get("MB_AUTH_KEY", ""),
        help="Auth-Key de abuse.ch (o variable MB_AUTH_KEY)",
    )
    parser.add_argument(
        "--per-family", type=int, default=100,
        help="muestras a pedir por familia al consultar al vuelo (def: 100)",
    )
    args = parser.parse_args()

    if not args.auth_key:
        sys.exit(
            "ERROR: falta la Auth-Key de abuse.ch.\n"
            "  1. Regístrate gratis en https://auth.abuse.ch/\n"
            "  2. export MB_AUTH_KEY=<tu-key>   (o usa --auth-key)"
        )

    session = requests.Session()
    session.headers["User-Agent"] = "malware-lab-sample-fetcher/1.0"

    # Fuente de muestras: familias al vuelo, o el catálogo de build_dataset.py.
    try:
        if args.families:
            print(f"Consultando familias: {', '.join(args.families)}")
            candidates = query_families(session, args.auth_key, args.families, args.per_family)
        else:
            candidates = from_catalog(args.catalog)
            if candidates is None:
                sys.exit(
                    f"No existe el catálogo {args.catalog}.\n"
                    "Genéralo primero con build_dataset.py, o usa --families."
                )
            print(f"Catálogo: {len(candidates)} muestras Intel ELF disponibles")
    except AuthError as e:
        sys.exit(f"ERROR: MalwareBazaar rechazó la Auth-Key ({e}).")
    except requests.RequestException as e:
        sys.exit(f"ERROR de red consultando MalwareBazaar: {e}")

    # Dedup por sha256 y recorte al límite pedido.
    seen, picked = set(), []
    for c in candidates:
        h = c.get("sha256") or c.get("sha256_hash")
        if h and h not in seen:
            seen.add(h)
            picked.append(c)
        if len(picked) >= args.limit:
            break

    if not picked:
        sys.exit("No hay muestras Intel ELF que descargar con esos criterios.")

    os.makedirs(args.dest, exist_ok=True)
    print(f"\nDescargando {len(picked)} muestras (ZIP cifrado, password '{ZIP_PASSWORD.decode()}')")
    print(f"Destino: {args.dest}\n")

    rows, ok = [], 0
    try:
        for c in picked:
            sha256 = c.get("sha256") or c.get("sha256_hash")
            familia = c.get("familia") or c.get("signature") or ""
            path, estado = download_sample(session, args.auth_key, sha256, args.dest)
            mark = "OK" if path else "--"
            print(f"  [{mark}] {familia:<10} {sha256[:16]}… {estado}")
            if path:
                ok += 1
            rows.append({
                "familia": familia,
                "sha256": sha256,
                "procesador": c.get("procesador") or "",
                "file_name": c.get("file_name") or "",
                "file_size": c.get("file_size") or "",
                "zip_path": path or "",
                "estado": estado,
                "url_origen": f"https://bazaar.abuse.ch/sample/{sha256}/",
            })
            time.sleep(1)               # cortesía con la API pública
    except AuthError as e:
        sys.exit(f"\nERROR: Auth-Key rechazada a mitad ({e}).")
    except requests.RequestException as e:
        sys.exit(f"\nERROR de red descargando: {e}")

    manifest = os.path.join(args.dest, "manifest.csv")
    write_manifest(manifest, rows)

    print(f"\nListo: {ok}/{len(picked)} binarios en cuarentena.")
    print(f"Inventario -> {manifest}")
    print(
        "\nRECORDATORIO: son ZIP cifrados (password 'infected'). NO los extraigas\n"
        "en tu host. Cópialos a la VM aislada y descomprímelos solo ahí."
    )


if __name__ == "__main__":
    main()
