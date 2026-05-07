#!/usr/bin/env python3
# ============================================================
#  modulos/cadenas.py  —  Módulo de Cadenas (Strings)
#  Extrae cadenas de texto legibles de cualquier archivo
#  Equivalente al comando 'strings' de Linux
#  Sin dependencias externas — solo Python base
#
#  Uso standalone:
#    python cadenas.py archivo.exe
#    python cadenas.py archivo.exe --min 6
#    python cadenas.py archivo.exe --max 50
#
#  Uso como módulo:
#    from modulos.cadenas import extraer_cadenas
# ============================================================

import sys
import os

# ── Configuración ────────────────────────────────────────────
MIN_LONGITUD = 4   # Mínimo de caracteres para considerar cadena
MAX_LONGITUD = 200 # Máximo de caracteres por cadena
MAX_MOSTRAR  = 50  # Máximo de cadenas a mostrar en pantalla
# ─────────────────────────────────────────────────────────────

# Caracteres imprimibles ASCII
IMPRIMIBLES = set(
    b"abcdefghijklmnopqrstuvwxyz"
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    b"0123456789"
    b" !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
)


def extraer_cadenas(ruta_archivo, min_len=MIN_LONGITUD, max_len=MAX_LONGITUD):
    """
    Extrae cadenas de texto legibles de un archivo binario.
    Retorna un diccionario con las cadenas encontradas o None si hay error.
    """
    if not os.path.isfile(ruta_archivo):
        print(f"[ERROR] Archivo no encontrado: {ruta_archivo}", file=sys.stderr)
        return None

    try:
        with open(ruta_archivo, "rb") as f:
            datos = f.read()
    except PermissionError:
        print(f"[ERROR] Sin permisos para leer: {ruta_archivo}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}", file=sys.stderr)
        return None

    cadenas = []
    actual  = []

    for byte in datos:
        if byte in IMPRIMIBLES:
            actual.append(chr(byte))
            # Cortar si excede el máximo
            if len(actual) >= max_len:
                if len(actual) >= min_len:
                    cadenas.append("".join(actual))
                actual = []
        else:
            if len(actual) >= min_len:
                cadenas.append("".join(actual))
            actual = []

    # Última cadena pendiente
    if len(actual) >= min_len:
        cadenas.append("".join(actual))

    return {
        "archivo":  ruta_archivo,
        "total":    len(cadenas),
        "min_len":  min_len,
        "cadenas":  cadenas,
    }


def mostrar_cadenas(resultado, max_mostrar=MAX_MOSTRAR):
    """Muestra las cadenas encontradas en formato legible."""
    if not resultado:
        return

    print(f"\n  Archivo  : {resultado['archivo']}")
    print(f"  Total    : {resultado['total']} cadenas encontradas")
    print(f"  Min len  : {resultado['min_len']} caracteres")
    print(f"\n  {'#':<5} {'Cadena'}")
    print(f"  {'-'*5} {'-'*60}")

    cadenas = resultado["cadenas"]
    mostrar = min(len(cadenas), max_mostrar)

    for i, cadena in enumerate(cadenas[:mostrar]):
        print(f"  {i+1:<5} {cadena}")

    if len(cadenas) > max_mostrar:
        print(f"\n  ... y {len(cadenas) - max_mostrar} cadenas mas.")
    print()


def mostrar_uso():
    print("""
 Uso: python cadenas.py [archivo] [opciones]

 Opciones:
   --min [n]   Longitud minima de cadena (default: 4)
   --max [n]   Longitud maxima de cadena (default: 200)

 Ejemplos:
   python cadenas.py archivo.exe
   python cadenas.py malware.exe --min 6
   python cadenas.py binario.bin --min 8 --max 100
""")


# ── Main (uso standalone) ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        mostrar_uso()
        sys.exit(1)

    ruta    = sys.argv[1]
    min_len = MIN_LONGITUD
    max_len = MAX_LONGITUD

    # Parsear opciones
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--min" and i + 1 < len(args):
            try:
                min_len = int(args[i+1])
                i += 2
            except ValueError:
                print(f"[ERROR] --min requiere un numero entero.")
                sys.exit(1)
        elif args[i] == "--max" and i + 1 < len(args):
            try:
                max_len = int(args[i+1])
                i += 2
            except ValueError:
                print(f"[ERROR] --max requiere un numero entero.")
                sys.exit(1)
        else:
            i += 1

    print(f"[CADENAS] Extrayendo cadenas de: {ruta}")

    resultado = extraer_cadenas(ruta, min_len, max_len)

    if resultado:
        mostrar_cadenas(resultado)
        print("[OK] Cadenas extraidas correctamente.")
        sys.exit(0)
    else:
        print("[ERROR] No se pudieron extraer cadenas.")
        sys.exit(1)