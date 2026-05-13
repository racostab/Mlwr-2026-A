#!/usr/bin/env python3
# ============================================================
#  modulos/entropia.py  —  Módulo de Entropía
#  Calcula la entropía de Shannon de un archivo
#
#  Valores de referencia:
#    0.0 - 1.0  →  Archivo casi vacío o muy repetitivo
#    1.0 - 5.0  →  Archivo de texto normal
#    5.0 - 7.0  →  Archivo comprimido o cifrado parcialmente
#    7.0 - 8.0  →  Archivo cifrado o comprimido (sospechoso)
#
#  Uso standalone:
#    python entropia.py archivo.exe
#
#  Uso como módulo:
#    from modulos.entropia import calcular_entropia
# ============================================================

import sys
import os
import math

def calcular_entropia(ruta_archivo):
    """
    Calcula la entropía de Shannon de un archivo.
    Retorna un diccionario con el resultado o None si hay error.
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

    if len(datos) == 0:
        return {
            "archivo":   ruta_archivo,
            "entropia":  0.0,
            "nivel":     "vacio",
            "sospechoso": False
        }

    # Calcular frecuencia de cada byte (0-255)
    frecuencia = [0] * 256
    for byte in datos:
        frecuencia[byte] += 1

    # Fórmula de Shannon: H = -sum(p * log2(p))
    total = len(datos)
    entropia = 0.0
    for count in frecuencia:
        if count > 0:
            p = count / total
            entropia -= p * math.log2(p)

    # Clasificar el nivel
    if entropia < 1.0:
        nivel = "muy bajo (repetitivo)"
        sospechoso = False
    elif entropia < 5.0:
        nivel = "normal (texto)"
        sospechoso = False
    elif entropia < 7.0:
        nivel = "medio (posible compresion)"
        sospechoso = True
    else:
        nivel = "alto (cifrado o comprimido)"
        sospechoso = True

    return {
        "archivo":    ruta_archivo,
        "entropia":   round(entropia, 4),
        "nivel":      nivel,
        "sospechoso": sospechoso
    }


def mostrar_entropia(resultado):
    """Muestra la entropía en formato legible."""
    if not resultado:
        return
    sospecha = "⚠ SOSPECHOSO" if resultado["sospechoso"] else "OK"
    print(f"\n  Archivo  : {resultado['archivo']}")
    print(f"  Entropia : {resultado['entropia']} / 8.0")
    print(f"  Nivel    : {resultado['nivel']}")
    print(f"  Estado   : {sospecha}")
    print()


def mostrar_uso():
    print("""
 Uso: python entropia.py [archivo]

 Ejemplos:
   python entropia.py archivo.txt
   python entropia.py malware.exe
""")


# ── Main (uso standalone) ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        mostrar_uso()
        sys.exit(1)

    ruta = sys.argv[1]
    print(f"[ENTROPIA] Calculando entropia de: {ruta}")

    resultado = calcular_entropia(ruta)

    if resultado:
        mostrar_entropia(resultado)
        print("[OK] Entropia calculada correctamente.")
        sys.exit(0)
    else:
        print("[ERROR] No se pudo calcular la entropia.")
        sys.exit(1)