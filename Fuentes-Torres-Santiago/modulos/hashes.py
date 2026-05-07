#!/usr/bin/env python3
# ============================================================
#  modulos/hashes.py  —  Módulo de Firmas
#  Calcula MD5, SHA1 y SHA256 de un archivo
#
#  Uso standalone:
#    python hashes.py archivo.exe
#    python hashes.py archivo.txt
#
#  Uso como módulo:
#    from modulos.hashes import calcular_hashes
# ============================================================

import hashlib
import sys
import os

# ── Configuración ────────────────────────────────────────────
BUFFER_SIZE = 65536  # 64KB — para archivos grandes
# ─────────────────────────────────────────────────────────────


def calcular_hashes(ruta_archivo):
    """
    Calcula MD5, SHA1 y SHA256 de un archivo.
    Retorna un diccionario con los resultados o None si hay error.
    """
    # Verificar que el archivo existe
    if not os.path.isfile(ruta_archivo):
        print(f"[ERROR] Archivo no encontrado: {ruta_archivo}", file=sys.stderr)
        return None

    md5    = hashlib.md5()
    sha1   = hashlib.sha1()
    sha256 = hashlib.sha256()

    try:
        with open(ruta_archivo, "rb") as f:
            while chunk := f.read(BUFFER_SIZE):
                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
    except PermissionError:
        print(f"[ERROR] Sin permisos para leer: {ruta_archivo}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}", file=sys.stderr)
        return None

    return {
        "archivo": ruta_archivo,
        "md5":     md5.hexdigest(),
        "sha1":    sha1.hexdigest(),
        "sha256":  sha256.hexdigest(),
    }


def mostrar_hashes(resultado):
    """Muestra los hashes en formato legible."""
    if not resultado:
        return
    print(f"\n  Archivo : {resultado['archivo']}")
    print(f"  MD5     : {resultado['md5']}")
    print(f"  SHA1    : {resultado['sha1']}")
    print(f"  SHA256  : {resultado['sha256']}")
    print()


def mostrar_uso():
    print("""
 Uso: python hashes.py [archivo]

 Ejemplos:
   python hashes.py archivo.txt
   python hashes.py C:\\Users\\santi\\malware.exe
""")


# ── Main (uso standalone) ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        mostrar_uso()
        sys.exit(1)

    ruta = sys.argv[1]
    print(f"[HASHES] Calculando firmas de: {ruta}")

    resultado = calcular_hashes(ruta)

    if resultado:
        mostrar_hashes(resultado)
        print("[OK] Hashes calculados correctamente.")
        sys.exit(0)
    else:
        print("[ERROR] No se pudieron calcular los hashes.")
        sys.exit(1)