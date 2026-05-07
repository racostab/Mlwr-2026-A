#!/usr/bin/env python3
# ============================================================
#  modulos/ssdeep.py  —  Módulo de Hash por Similitud
#  Implementación de fuzzy hashing estilo ssdeep
#  Detecta archivos similares aunque no sean idénticos
#  Sin dependencias externas — solo Python base
#
#  Uso standalone:
#    python ssdeep.py archivo.exe
#    python ssdeep.py archivo1.exe archivo2.exe
#    python ssdeep.py --dir carpeta/
#    python ssdeep.py --dir carpeta/ [umbral]
#
#  Modos:
#    1 archivo   → Calcula fuzzy hash
#    2 archivos  → Compara similitud entre ambos
#    --dir       → Compara todos los archivos de una carpeta
#                  umbral default: 50 (0-100)
#
#  Uso como módulo:
#    from modulos.ssdeep import calcular_ssdeep, comparar
# ============================================================

import sys
import os
import math

# ── Configuración ────────────────────────────────────────────
BLOCK_MIN  = 3     # Tamaño mínimo de bloque
BASE64     = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
# ─────────────────────────────────────────────────────────────


def _rolling_hash(data, offset, window=7):
    """Hash rodante sobre una ventana de bytes."""
    h = 0
    for i in range(window):
        if offset + i < len(data):
            h = (h * 31 + data[offset + i]) & 0xFFFFFFFF
    return h


def _block_size(longitud):
    """Calcula el tamaño de bloque óptimo según el tamaño del archivo."""
    bs = BLOCK_MIN
    while bs * 64 < longitud:
        bs *= 2
    return bs


def _hash_bloque(data, start, end):
    """Hash simple de un bloque de bytes."""
    h = 5381
    for b in data[start:end]:
        h = ((h << 5) + h + b) & 0xFFFFFFFF
    return BASE64[h % 64]


def calcular_ssdeep(ruta_archivo):
    """
    Calcula el fuzzy hash de un archivo estilo ssdeep.
    Retorna un diccionario con el resultado o None si hay error.
    """
    if not os.path.isfile(ruta_archivo):
        print(f"[ERROR] Archivo no encontrado: {ruta_archivo}", file=sys.stderr)
        return None

    try:
        with open(ruta_archivo, "rb") as f:
            data = f.read()
    except PermissionError:
        print(f"[ERROR] Sin permisos para leer: {ruta_archivo}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}", file=sys.stderr)
        return None

    if len(data) == 0:
        return {
            "archivo":    ruta_archivo,
            "block_size": BLOCK_MIN,
            "hash":       f"{BLOCK_MIN}::",
            "tamano":     0
        }

    bs = _block_size(len(data))

    # Generar hash en dos resoluciones (bloque y bloque*2)
    hash1 = []
    hash2 = []

    bloque_inicio = 0
    for i in range(len(data)):
        rh = _rolling_hash(data, i)
        if (rh % bs) == (bs - 1):
            hash1.append(_hash_bloque(data, bloque_inicio, i + 1))
            bloque_inicio = i + 1
        if (rh % (bs * 2)) == (bs * 2 - 1):
            hash2.append(_hash_bloque(data, bloque_inicio, i + 1))

    # Agregar último bloque
    if bloque_inicio < len(data):
        hash1.append(_hash_bloque(data, bloque_inicio, len(data)))
        hash2.append(_hash_bloque(data, bloque_inicio, len(data)))

    h1 = "".join(hash1[:64])
    h2 = "".join(hash2[:32])
    fuzzy_hash = f"{bs}:{h1}:{h2}"

    return {
        "archivo":    ruta_archivo,
        "block_size": bs,
        "hash":       fuzzy_hash,
        "tamano":     len(data)
    }


def _distancia_edicion(s1, s2):
    """Distancia de Levenshtein entre dos cadenas."""
    m, n = len(s1), len(s2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if s1[i-1] == s2[j-1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j-1])
            prev = temp
    return dp[n]


def comparar(resultado1, resultado2):
    """
    Compara dos fuzzy hashes y retorna similitud del 0 al 100.
    100 = idénticos, 0 = completamente diferentes.
    """
    if not resultado1 or not resultado2:
        return 0

    h1 = resultado1["hash"].split(":")
    h2 = resultado2["hash"].split(":")

    if len(h1) < 3 or len(h2) < 3:
        return 0

    parte1_h1, parte2_h1 = h1[1], h1[2]
    parte1_h2, parte2_h2 = h2[1], h2[2]

    # Comparar ambas partes
    def similitud_cadenas(a, b):
        if not a or not b:
            return 0
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 100
        dist = _distancia_edicion(a, b)
        return int((1 - dist / max_len) * 100)

    s1 = similitud_cadenas(parte1_h1, parte1_h2)
    s2 = similitud_cadenas(parte2_h1, parte2_h2)

    return max(s1, s2)


def mostrar_ssdeep(resultado):
    """Muestra el fuzzy hash en formato legible."""
    if not resultado:
        return
    print(f"\n  Archivo    : {resultado['archivo']}")
    print(f"  Tamano     : {resultado['tamano']} bytes")
    print(f"  Block size : {resultado['block_size']}")
    print(f"  Fuzzy hash : {resultado['hash']}")
    print()


def mostrar_uso():
    print("""
 Uso: python ssdeep.py [archivo1] [archivo2]

 Modos:
   python ssdeep.py archivo.exe              Calcula fuzzy hash
   python ssdeep.py archivo1.exe archivo2.exe  Compara similitud

 Ejemplos:
   python ssdeep.py hashes.py
   python ssdeep.py hashes.py entropia.py
""")


# ── Main (uso standalone) ─────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        mostrar_uso()
        sys.exit(1)

    if len(sys.argv) == 2:
        # Modo: calcular hash de un archivo
        ruta = sys.argv[1]
        print(f"[SSDEEP] Calculando fuzzy hash de: {ruta}")
        resultado = calcular_ssdeep(ruta)
        if resultado:
            mostrar_ssdeep(resultado)
            print("[OK] Fuzzy hash calculado correctamente.")
            sys.exit(0)
        else:
            print("[ERROR] No se pudo calcular el fuzzy hash.")
            sys.exit(1)

    elif len(sys.argv) == 3:
        # Modo: comparar dos archivos
        ruta1 = sys.argv[1]
        ruta2 = sys.argv[2]
        print(f"[SSDEEP] Comparando archivos:")
        print(f"  Archivo 1: {ruta1}")
        print(f"  Archivo 2: {ruta2}\n")

        r1 = calcular_ssdeep(ruta1)
        r2 = calcular_ssdeep(ruta2)

        if r1 and r2:
            mostrar_ssdeep(r1)
            mostrar_ssdeep(r2)
            similitud = comparar(r1, r2)
            print(f"  Similitud : {similitud}%")
            if similitud >= 80:
                print("  ⚠ ALERTA: Archivos muy similares.")
            elif similitud >= 50:
                print("  ~ Archivos parcialmente similares.")
            else:
                print("  OK Archivos diferentes.")
            print()
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        mostrar_uso()
        sys.exit(1)
    # Agregar esto al final de ssdeep.py, dentro del main

elif len(sys.argv) >= 3 and sys.argv[1] == "--dir":
        # Modo: comparar todos los archivos de una carpeta
        carpeta = sys.argv[2]
        umbral  = int(sys.argv[3]) if len(sys.argv) > 3 else 50

        if not os.path.isdir(carpeta):
            print(f"[ERROR] No es una carpeta: {carpeta}")
            sys.exit(1)

        archivos = [
            os.path.join(carpeta, f)
            for f in os.listdir(carpeta)
            if os.path.isfile(os.path.join(carpeta, f))
        ]

        if len(archivos) < 2:
            print("[ERROR] Se necesitan al menos 2 archivos en la carpeta.")
            sys.exit(1)

        print(f"[SSDEEP] Analizando {len(archivos)} archivos en: {carpeta}")
        print(f"[SSDEEP] Umbral de similitud: {umbral}%\n")

        # Calcular hash de todos
        resultados = {}
        for archivo in archivos:
            r = calcular_ssdeep(archivo)
            if r:
                resultados[archivo] = r

        # Comparar todos contra todos
        encontrados = False
        archivos_lista = list(resultados.keys())

        for i in range(len(archivos_lista)):
            for j in range(i + 1, len(archivos_lista)):
                a1 = archivos_lista[i]
                a2 = archivos_lista[j]
                sim = comparar(resultados[a1], resultados[a2])

                if sim >= umbral:
                    encontrados = True
                    nombre1 = os.path.basename(a1)
                    nombre2 = os.path.basename(a2)
                    alerta  = "⚠ MUY SIMILARES" if sim >= 80 else "~ PARCIALMENTE SIMILARES"
                    print(f"  {nombre1}  vs  {nombre2}")
                    print(f"  Similitud: {sim}%  —  {alerta}\n")

        if not encontrados:
            print(f"  Sin archivos similares por encima del {umbral}%.")