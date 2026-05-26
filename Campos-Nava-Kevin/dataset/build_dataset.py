#!/usr/bin/env python3
"""Constructor del dataset de muestras botnet en formato ELF.

Consulta la API de MalwareBazaar (abuse.ch) por las familias de botnet más
frecuentes, se queda solo con las muestras ELF y genera un catálogo en CSV + JSON.

Solo cataloga METADATOS (hashes, familia, arquitectura, URL de origen). No
descarga binarios: cada muestra queda referenciada por su hash en MalwareBazaar.

Uso:
    export MB_AUTH_KEY=<tu-key>          # gratis en https://auth.abuse.ch/
    python3 dataset/build_dataset.py
    python3 dataset/build_dataset.py --families Mirai Gafgyt --limit 200 --merge

El dataset replica las columnas de la hoja "Samples" del ejemplo de referencia
(docs/Malware-botnet_v1.xlsx).
"""
import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API_URL = "https://mb-api.abuse.ch/api/v1/"
HERE = os.path.dirname(os.path.abspath(__file__))

# Firmas de botnets ELF más frecuentes en MalwareBazaar. Necurs/Emotet/Qbot se
# omiten a propósito: son PE de Windows y no producen muestras ELF.
DEFAULT_FAMILIES = [
    "Mirai", "Gafgyt", "Bashlite", "Tsunami",
    "Mozi", "XorDDoS", "Hajime", "Kaiji",
]

# Tags de MalwareBazaar que identifican la arquitectura del binario ELF.
ARCH_TAGS = {
    "arm", "arm7", "armv4l", "armv5l", "armv6l", "armv7l", "aarch64",
    "mips", "mipsel", "mips64",
    "x86", "x86-64", "x86_64", "i686", "i586",
    "sparc", "m68k", "powerpc", "ppc", "sh4", "riscv",
}

# Estados de la API que indican un problema con la Auth-Key.
AUTH_ERRORS = {"unauthorized", "illegal_auth_key", "unknown_auth_key", "auth_required"}

# Columnas del CSV, alineadas con la hoja "Samples" del ejemplo de referencia.
CSV_FIELDS = [
    "no", "familia", "anio", "md5", "sha1", "sha256",
    "url_origen", "existe", "virustotal", "porc_deteccion",
    "procesador", "so_formato", "cve", "cve_link",
    "first_seen", "file_name", "file_size", "tags", "reporter",
]


class AuthError(RuntimeError):
    """La API rechazó la petición por falta de Auth-Key o key inválida."""


def query_signature(session, auth_key, signature, limit):
    """Consulta MalwareBazaar por una firma de familia y devuelve sus muestras."""
    resp = session.post(
        API_URL,
        data={"query": "get_siginfo", "signature": signature, "limit": str(limit)},
        headers={"Auth-Key": auth_key} if auth_key else {},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    status = payload.get("query_status")

    if status == "ok":
        return payload.get("data", [])
    if status in ("no_results", "illegal_signature"):
        print(f"  ! '{signature}': sin resultados ({status})", file=sys.stderr)
        return []
    if status in AUTH_ERRORS:
        raise AuthError(status)
    raise RuntimeError(f"MalwareBazaar respondió '{status}' para la firma '{signature}'")


def is_elf(entry):
    """True si la muestra es un binario ELF."""
    return (entry.get("file_type") or "").lower() == "elf"


def detect_arch(tags):
    """Extrae la arquitectura del procesador a partir de los tags de la muestra."""
    for tag in tags or []:
        if tag.lower() in ARCH_TAGS:
            return tag
    return ""


def build_record(entry):
    """Convierte una entrada de MalwareBazaar en un registro del catálogo."""
    sha256 = entry.get("sha256_hash", "")
    first_seen = entry.get("first_seen") or ""
    tags = entry.get("tags") or []
    return {
        "no": None,                         # se asigna al final, ya ordenado
        "familia": entry.get("signature") or "",
        "anio": first_seen[:4],
        "md5": entry.get("md5_hash", ""),
        "sha1": entry.get("sha1_hash", ""),
        "sha256": sha256,
        "url_origen": f"https://bazaar.abuse.ch/sample/{sha256}/",
        "existe": "Si",                     # presente en MalwareBazaar al consultar
        "virustotal": f"https://www.virustotal.com/gui/file/{sha256}",
        "porc_deteccion": "",               # rellenar manual: requiere API de VT
        "procesador": detect_arch(tags),
        "so_formato": "Linux / ELF",
        "cve": "",                          # rellenar manual tras el análisis
        "cve_link": "",
        "first_seen": first_seen,
        "last_seen": entry.get("last_seen") or "",
        "file_name": entry.get("file_name", ""),
        "file_size": entry.get("file_size", ""),
        "file_type": entry.get("file_type", ""),
        "mime": entry.get("file_type_mime", ""),
        "tags": tags,
        "ssdeep": entry.get("ssdeep") or "",
        "tlsh": entry.get("tlsh") or "",
        "telfhash": entry.get("telfhash") or "",
        "reporter": entry.get("reporter", ""),
    }


def load_existing(json_path):
    """Carga las muestras de un dataset JSON previo (para --merge)."""
    if not os.path.exists(json_path):
        return []
    with open(json_path, encoding="utf-8") as f:
        return json.load(f).get("samples", [])


def write_csv(path, samples):
    """Escribe el catálogo como CSV plano (tags unidos por coma)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for s in samples:
            row = dict(s)
            row["tags"] = ", ".join(s.get("tags", []))
            writer.writerow(row)


def write_json(path, samples, families):
    """Escribe el catálogo completo como JSON."""
    doc = {
        "dataset": "Malware Botnet ELF — catálogo de metadatos",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "MalwareBazaar (abuse.ch) — query=get_siginfo",
        "families_queried": families,
        "count": len(samples),
        "samples": samples,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Construye el dataset de muestras botnet ELF desde MalwareBazaar.",
    )
    parser.add_argument(
        "--families", nargs="+", default=DEFAULT_FAMILIES, metavar="FAMILIA",
        help="firmas de familia a consultar (por defecto: %(default)s)",
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="muestras a pedir por familia (máx. 1000 en la API; def. 100)",
    )
    parser.add_argument(
        "--auth-key", default=os.environ.get("MB_AUTH_KEY", ""),
        help="Auth-Key de abuse.ch (o variable de entorno MB_AUTH_KEY)",
    )
    parser.add_argument(
        "--out-dir", default=HERE,
        help="carpeta de salida para botnet_elf.csv / .json (def: junto al script)",
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="acumular sobre el JSON ya existente en vez de sobrescribir",
    )
    args = parser.parse_args()

    if not args.auth_key:
        print(
            "AVISO: sin Auth-Key. MalwareBazaar exige una key gratuita.\n"
            "  1. Regístrate en https://auth.abuse.ch/\n"
            "  2. export MB_AUTH_KEY=<tu-key>   (o usa --auth-key)\n",
            file=sys.stderr,
        )

    session = requests.Session()
    session.headers["User-Agent"] = "malware-lab-dataset-builder/1.0"

    # sha256 -> registro; arranca desde el dataset previo si se pidió --merge.
    json_path = os.path.join(args.out_dir, "botnet_elf.json")
    by_hash = {}
    if args.merge:
        for s in load_existing(json_path):
            by_hash[s["sha256"]] = s
        print(f"merge: {len(by_hash)} muestras cargadas de {json_path}")

    try:
        for family in args.families:
            entries = query_signature(session, args.auth_key, family, args.limit)
            elf = [e for e in entries if is_elf(e)]
            nuevas = 0
            for entry in elf:
                record = build_record(entry)
                if record["sha256"] and record["sha256"] not in by_hash:
                    nuevas += 1
                by_hash[record["sha256"]] = record
            print(f"  {family:<12} {len(entries):>4} muestras · {len(elf):>4} ELF · {nuevas:>4} nuevas")
            time.sleep(1)               # cortesía con la API pública
    except AuthError as e:
        sys.exit(
            f"\nERROR: MalwareBazaar rechazó la Auth-Key ({e}).\n"
            "Consigue una gratis en https://auth.abuse.ch/ y expórtala en MB_AUTH_KEY."
        )
    except requests.RequestException as e:
        sys.exit(f"\nERROR de red consultando MalwareBazaar: {e}")

    # Ordena por familia y fecha, y numera secuencialmente.
    samples = sorted(by_hash.values(), key=lambda s: (s["familia"], s["first_seen"]))
    for i, s in enumerate(samples, start=1):
        s["no"] = i

    os.makedirs(args.out_dir, exist_ok=True)
    csv_path = os.path.join(args.out_dir, "botnet_elf.csv")
    write_csv(csv_path, samples)
    write_json(json_path, samples, args.families)

    print(f"\nDataset: {len(samples)} muestras botnet ELF")
    print(f"  CSV  -> {csv_path}")
    print(f"  JSON -> {json_path}")


if __name__ == "__main__":
    main()
